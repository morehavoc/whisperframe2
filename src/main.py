import argparse
from pvrecorder import PvRecorder
import recording
import generate
import settings
import webrtcvad
import openai
import os
import subprocess
import signal
import sys
import leds
import time

SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
FRAME_LENGTH = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples for 30ms at 16kHz

def append_to_transcript(t):
    with open(settings.TRANSCRIPT_FILE, "a") as f:
        f.write(str(t) + "\n")
    recording.trim_transcript_file(settings.TRANSCRIPT_FILE)

def run():
    openai.api_key = settings.OPENAI_API_KEY

    recorder = PvRecorder(frame_length=FRAME_LENGTH, device_index=settings.INPUT_DEVICE_ID)
    vad = webrtcvad.Vad(3)  # Mode 0 (Quality) - least aggressive

    try:
        # Generate an image on start up using the last stuff that was in the transcript
        generate.run(settings.OPENAI_API_KEY, 20, settings.DB_FILE, settings.TRANSCRIPT_FILE)

        line_counter = 0

        while True:
            leds.percent(line_counter/20.0)
            recording.wait_for_voices(vad, recorder, SAMPLE_RATE)
            # there should now be voices, so transcribe 15 seconds of audio
            transcript = recording.transcribe_openai(recorder, 15, settings.OPENAI_API_KEY)

            if transcript is not None and transcript != "" and transcript != "\n" and transcript.strip() != "":
                print("* TS:")
                print(transcript)
                append_to_transcript(transcript)

                # each time we get a transcript line, we increase the counter by one.
                # then each time we get 20 new lines, we call generate
                line_counter+=1
                if line_counter >= 2:
                    line_counter = 0
                    generate.run(settings.OPENAI_API_KEY, 20, settings.DB_FILE, settings.TRANSCRIPT_FILE)
                else:
                    print("Need " +str(20-line_counter)+" More snippets")

    except KeyboardInterrupt as e:
        print("stopping")
        raise e
    finally:
        if recorder is not None:
            recorder.delete()

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--show_audio_devices', action='store_true')

    args = parser.parse_args()

    if args.show_audio_devices:
        devices = PvRecorder.get_available_devices()
        for i in range(len(devices)):
            print('index: %d, device name: %s' % (i, devices[i]))
    else:
        print("running...")
        # run flask in another python process
        time.sleep(5)
        browser_process = subprocess.Popen(['python3', 'view.py'])

        def signal_handler(sig, frame):
            print('Stopping Flask app and closing browser')
            browser_process.terminate()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        while True:
            try:
                run()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print("Exception: ", e)
                print("Restart Required...")
                leds.error()
                while True:
                    time.sleep(30)

if __name__ == '__main__':
    main()
