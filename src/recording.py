import pvcobra
import sys
import collections
import wave
import multiprocessing
import time
import struct
import openai
import os

TEMP_WAVE_FILE = "output.wav"
RUNNING_SUM_COUNT = 3
MAX_TRANSCRIPT_LINES = 120  # About 1 hour of transcript (15s recordings every ~30s)

def _openai_background(openai_api_key):
    print("** Open AI Says...")
    import openai
    client = openai.OpenAI(api_key=openai_api_key)
    with open(TEMP_WAVE_FILE, 'rb') as af:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=af
        )
        return str(transcript.text)

mpPool = multiprocessing.Pool(1)

def wait_for_voices(cobra, recorder):
    print("Listening...")
    running_values = collections.deque([0,0,0,0,0], maxlen=RUNNING_SUM_COUNT)
    try:
        print("Cobra version: %s" % cobra.version)
        recorder.start()

        while True:
            pcm = recorder.read()

            voice_probability = cobra.process(pcm)
            running_values.append(voice_probability)
            average = sum(running_values)/RUNNING_SUM_COUNT
            if average > .5:
                # 5 values in a row where we think there are words so we bail out
                break
            percentage = voice_probability * 100
            bar_length = int((percentage / 10) * 3)
            empty_length = 30 - bar_length
            sys.stdout.write("\r[%3d]|%s%s|" % (percentage, '█' * bar_length, ' ' * empty_length))
            sys.stdout.flush()
    except KeyboardInterrupt:
        raise
    finally:
        recorder.stop()

def trim_transcript_file(transcript_file):
    """Keep only the last MAX_TRANSCRIPT_LINES lines in the transcript file"""
    if not os.path.exists(transcript_file):
        return
        
    with open(transcript_file, 'r') as f:
        lines = f.readlines()
    
    if len(lines) > MAX_TRANSCRIPT_LINES:
        with open(transcript_file, 'w') as f:
            f.writelines(lines[-MAX_TRANSCRIPT_LINES:])

def transcribe_openai(recorder, timeout, openai_api_key):
    global mpPool
    print("recording")
    wav_file = wave.open(TEMP_WAVE_FILE, "w")
    wav_file.setparams((1, 2, 16000, 512, "NONE", "NONE"))
    recorder.start()
    start_time = time.time() # get current time

    while time.time() - start_time < timeout: # run loop for 15 seconds
        pcm = recorder.read()
        wav_file.writeframes(struct.pack("h" * len(pcm), *pcm))

    recorder.stop()
    wav_file.close()
    res = mpPool.apply_async(_openai_background, [openai_api_key])
    try:
        transcript = res.get(20)
        return transcript
    except:
        mpPool = multiprocessing.Pool(1)
        return ""
