import sys
import collections
import wave
import multiprocessing
import time
import struct
import openai
import os
import webrtcvad

TEMP_WAVE_FILE = "output.wav"
RUNNING_SUM_COUNT = 5  # Looking at 5 frames (150ms at 30ms per frame)
MAX_TRANSCRIPT_LINES = 120  # About 1 hour of transcript (15s recordings every ~30s)

def _openai_background(openai_api_key):
    print("** Open AI Says...")
    import openai
    client = openai.OpenAI(api_key=openai_api_key)
    with open(TEMP_WAVE_FILE, 'rb') as af:
        transcript = client.audio.transcriptions.create(
            model="gpt-4o-transcribe", 
            file=af, 
            response_format="text",
            prompt="The following is some audio that needs transcription. If you don't know what is being said or if the audio is blank return nothing (an empty result)."
        )
        print(transcript)
        return str(transcript)

mpPool = multiprocessing.Pool(1)

def wait_for_voices(vad, recorder, sample_rate):
    print("Listening...")
    running_values = collections.deque([0] * RUNNING_SUM_COUNT, maxlen=RUNNING_SUM_COUNT)
    try:
        recorder.start()

        while True:
            pcm = recorder.read()
            audio_frame = struct.pack("%dh" % len(pcm), *pcm)
            is_speech = vad.is_speech(audio_frame, sample_rate)
            
            running_values.append(1 if is_speech else 0)
            active_frames = sum(running_values)
            
            # Debug output on one line
            sys.stdout.write("\rFrame: speech=%s values=%s active=%d/%d thresh=%d     " % (
                is_speech,
                list(running_values),
                active_frames,
                RUNNING_SUM_COUNT,
                RUNNING_SUM_COUNT  # Now requiring all frames to be speech
            ))
            sys.stdout.flush()
            
            if active_frames == RUNNING_SUM_COUNT:  # All frames must be speech
                print("\nVoice detected! Starting recording...")
                break
            
            # Add a small delay to make the output more readable
            time.sleep(0.1)
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
