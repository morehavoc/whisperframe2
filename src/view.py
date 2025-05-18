from flask import Flask, jsonify, render_template
import json
import random
import subprocess
import signal
import sys
import os
import time
import datetime
import settings
from Adafruit_IO import Client, Data
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)
browser_process = None
aio = Client(settings.ADAFRUIT_IO_USERNAME, settings.ADAFRUIT_IO_KEY)

# Store WebSocket connections
ws_clients = set()

def get_random_url():
    # set the seed to the same value every 5 minutes so all calls within 5 mins return the same random.choice()
    random.seed(int(datetime.datetime.now().timestamp()/360))
    file_path = settings.DB_FILE
    modification_time = os.path.getmtime(file_path)

    try:
        with open(file_path, "rb") as f:
            urls = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        urls = []

    if len(urls) == 0:
        # No urls
        return {}

    # return the last one if the file has been changed in the last 30 mins.
    if time.time() - modification_time <= 30 * 60:
        return urls[-1]
    # return a null one if the time is between midnight and 7 am
    elif datetime.time(0,0) <= datetime.datetime.now().time() <= datetime.time(7,0):
        return {}
    # return a random image
    else:
        return random.choice(urls)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/image')
def image():
    img = get_random_url()
    aio.append(settings.ADAFRUIT_IO_FEED, json.dumps(img))
    return jsonify(img)

@sock.route('/ws')
def ws(ws):
    ws_clients.add(ws)
    try:
        while True:
            # Keep connection alive and wait for new images
            ws.receive()
    except:
        ws_clients.remove(ws)

def notify_clients(data):
    """Notify all WebSocket clients of new image data"""
    dead_clients = set()
    for client in ws_clients:
        try:
            client.send(json.dumps(data))
        except:
            dead_clients.add(client)
    
    # Clean up dead connections
    for client in dead_clients:
        ws_clients.remove(client)

def signal_handler(sig, frame):
    print('Stopping Flask app and closing browser')
    browser_process.terminate()
    sys.exit(0)

if __name__ == '__main__':
    if settings.START_BROWSER:
        # Start the browser in kiosk mode
        browser_process = subprocess.Popen(['chromium', '-kiosk', 'http://localhost:5000'])
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    app.run(host="0.0.0.0", debug=True)
