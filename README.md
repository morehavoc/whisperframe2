# Whisper-Frame

A basic start on the whisper-frame concept that Daniel Reeves thought up. It listens to conversations in the room and creates and displays art based on that speech. Thanks to Bethany for helping make the stable diffusion prompts way better!

## To Run it
On a desktop, or via VNC, open a terminal and:
```
cd whisper-frame/src
python3 main.py
```

If you are at the beesnest and you know the password, you can ssh into our version of this using `beesnest@piframe.local`.

## Folders
* `src` Contains the source code for the app. See [Readme](src/README.md)
* `4mics_hat` - Copy of code used for the mic array (see [instructions](https://wiki.seeedstudio.com/ReSpeaker_4_Mic_Array_for_Raspberry_Pi/))
* `seeed-voicecard` - Copy of code used for mic array (see [instructions](https://wiki.seeedstudio.com/ReSpeaker_4_Mic_Array_for_Raspberry_Pi/))

## Notes
* Roughly, you need to follow the [instructions](https://wiki.seeedstudio.com/ReSpeaker_4_Mic_Array_for_Raspberry_Pi/) to get the mic setup, then follow the [Readme](src/README.md) in the `src` folder to get this code up and running.
* You will also need to setup src/settings.py with the following properties:
* 
```python
PV_ACCESS_KEY = "picovoice access key"
INPUT_DEVICE_ID = -1 # -1 for the default if you have that setup correctly
TRANSCRIPT_FILE = "db/transcript.txt"
OPENAI_API_KEY = "open ai API key"
STABLE_DIF_API_KEY = "stable diffusion API key"
DB_FILE = "db/prompts.json"
ADAFRUIT_IO_USER = "adafruit io user for feed push for sign"
ADAFRUIT_IO_KEY = "adafruit io key for feed push for sign"
```

## Some Reference Docs
* [Instructions on setting up and using the Mic Array](https://wiki.seeedstudio.com/ReSpeaker_4_Mic_Array_for_Raspberry_Pi/#enabling-voice-recognition-at-edge-with-picovoice)
* [Picovoice used for speech detection](https://github.com/Picovoice/cobra/blob/main/demo/python/cobra_demo_mic.py)
* [Picovoice main site](https://picovoice.ai)
* [OpenAI Speech to Texxt](https://platform.openai.com/docs/guides/speech-to-text/improving-reliability)
* [StableDiffusion API Queued Image Fetching](https://stablediffusionapi.com/docs/stable-diffusion-api/fetchqueimg/)
