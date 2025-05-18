import os
import ipaddress
import ssl
import wifi
import socketpool
import time
import json
import adafruit_requests
from secrets import secrets
from adafruit_io.adafruit_io import IO_MQTT, IO_HTTP
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_display_text import label
from adafruit_magtag.magtag import MagTag
from adafruit_datetime import datetime

# an actual reasonable tutorial here: https://learn.adafruit.com/mqtt-in-circuitpython/circuitpython-wifi-usage


# Connet to Wifi
print("ESP32-S2 WebClient Test")

print(f"My MAC address: {[hex(i) for i in wifi.radio.mac_address]}")

print("Available WiFi networks:")
for network in wifi.radio.start_scanning_networks():
    print("\t%s\t\tRSSI: %d\tChannel: %d" % (str(network.ssid, "utf-8"),
                                             network.rssi, network.channel))
wifi.radio.stop_scanning_networks()

print(f"Connecting to {os.getenv('WIFI_SSID')}")
wifi.radio.connect(os.getenv("WIFI_SSID"), os.getenv("WIFI_PASSWORD"))
print(f"Connected to {os.getenv('WIFI_SSID')}")
print(f"My IP address: {wifi.radio.ipv4_address}")

# Create socket and ssl_context for the MQTT client
pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()
requests = adafruit_requests.Session(pool, ssl_context)

# Set up a MiniMQTT Client
# source code: https://github.com/adafruit/Adafruit_CircuitPython_MiniMQTT/blob/main/examples/esp32spi/minimqtt_adafruitio_esp32spi.py
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    port=1883,
    username=os.getenv('ADAFRUIT_IO_USERNAME'),
    password=os.getenv('ADAFRUIT_IO_KEY'),
    socket_pool=pool,
    ssl_context=ssl_context,
)

# source code: https://github.com/adafruit/Adafruit_CircuitPython_AdafruitIO/blob/main/adafruit_io/adafruit_io.py
io = IO_MQTT(mqtt_client)
iohttp = IO_HTTP(os.getenv('ADAFRUIT_IO_USERNAME'), os.getenv('ADAFRUIT_IO_KEY'), requests)
io.connect()

# setup the mag tag
magtag = MagTag()
magtag.add_text(
    text_font="/fonts/Arial-Bold-12.bdf",
    text_wrap=35,
    text_maxlen=150,
    text_position=(
        (magtag.graphics.display.width // 2),
        (magtag.graphics.display.height // 2) - 20,
    ),
    line_spacing=0.75,
    text_anchor_point=(0.5, 0.5),  # center the text on x & y
)
magtag.add_text(
    text_font="/fonts/Arial-Italic-12.bdf",
    text_maxlen=50,
    text_position=(
        (magtag.graphics.display.width // 4 * 3 - 10), 118),
    text_anchor_point=(0.0, 0.5)
)
magtag.add_text(
    text_font="/fonts/Arial-Italic-12.bdf",
    text_maxlen=50,
    text_position=(
        (10), 100),
    text_anchor_point=(0.0, 0.5)
)

#setup magtag leds
def lights_on():
    magtag.peripherals.neopixel_disable = False
    magtag.peripherals.neopixels.brightness = .05
    magtag.peripherals.neopixels.fill((255,255,255))
    
def lights_off():
    magtag.peripherals.neopixel_disable = True
    
lights_on()


def on_current_image_msg(client, source, msg):
    print(msg)
    data = json.loads(str(msg))
    # if there is no url, then we turn it off.
    if 'url' not in data:
        lights_off()
        magtag.set_text("", 0, auto_refresh=False)
        magtag.set_text("", 1, auto_refresh=False)
        magtag.set_text("", 2, auto_refresh=True)
        return
    # if there is a url
    lights_on()
    d = datetime.fromisoformat(data["date"])
    magtag.set_text(data["prompt"], 0, auto_refresh = False)
    magtag.set_text(str(d.year)+"-"+str(d.month)+"-"+str(d.day), 1, auto_refresh=False)
    magtag.set_text(data["name"], 2, auto_refresh=True)
    

# Set up a message handler for the CurrentImage feed
io.add_feed_callback("CurrentImage", on_current_image_msg)

# Subscribe to all messages on the CurrentImage feed
io.subscribe("CurrentImage")

#Get the most recent data image
on_current_image_msg(None, None, iohttp.receive_data('piframe.currentimage')['value'])

# Start a blocking loop to check for new messages
while True:
    try:
        io.loop()
    except (ValueError, RuntimeError, OSError) as e:
        print("Failed to get data, retrying\n", e)
        time.sleep(5)
        wifi.reset()
        io.reconnect()
        continue
    time.sleep(0.5)

