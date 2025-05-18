# whisper-frame

A set of Python scripts that together allow the raspberry pi to:

1. Listen to conversations around it and record 15-second snippets of them
2. Call OpenAI's Speech2Text service to transcribe those 15-second snippets and store them
3. Periodically, use GPT-4 to create an image generation prompt for stable-diffusion, and generate that image
4. If there has been an image generated in the last 30 minutes, show that image (checking every 5 minutes).
5. If there has not been an image in the last 30 minutes, then select a random one from the database and display that.

## Current Limitations

* It currently calls OpenAI's Speech2Text service instead of using a local whisper instance. The Pi just isn't powerful enough to run a large ML model like Whisper (even the smaller ones struggle). So, more hardware or running our own "instance" of the Whisper model on another computer would save some money here.
* The display randomly selects an image that has been generated, so it could show something from a long time ago.
* The entire conversation is not converted, only 15-second snippets, typically separated by about 10-20 seconds. So it is really just samples of the entire conversation.
* Silence is transcribed as some Japanese characters that roughly translate into "thank you for watching, please like and subscribe". Clearly, it was trained on lots of YouTube videos.
* Probably some other things too.

## Large Moving Parts

* `main.py` - The file that you run, e.g. `python3 main.py`
* `recording.py` - Listens for words, records and transcribes the audio. Transcriptions are appended to `db/transcript.txt`
* `generate.py` - Grabs the last 20 lines of `db/transcript.txt`, generates a prompt, and generates an image. the image URL, prompt and date stamp to the image is appended to `db/prompts.json`
* `view.py` - Runs a Flask web server that hosts an html page. The HTML page requests an image from the `/image` endpoint every 5 minutes. The `/image` endpoint shows the most recent image from `db/prompts.json` if that file has been modified in the last 30 minutes, otherwise, it selects a random image from `db/prompts.json`.

## File descriptions

### `main.py`

The main app that you run. This contains a `while True` loop that:
1. waits for voices to be found using picovoice
2. records a 15-second snippet (and transcribe it)
3. counts the number of snippets
4. Every 20 snippets, generate a new image

Roughly, this means that a new image is generated every 5 minutes during normal conversation.

This script also starts the flask server (`view.py`) as a sub-process and attaches the termination signals to it so that it will shut down when this script shuts down.

### `generate.py`

Pulls the last 20 lines of `db/transcript.txt` and combines that with the information in the prompts directory to create a GPT4 prompt to generate a stable diffusion prompt. It then passes that on to stable diffusion for rendering. The resulting image URL, prompt and datetime is appended to `db/prompts.json`

### `output.wav`

The temporary audio file is saved by `recording.py` during its process.

### `prompts`
A set of text files used to construct the GPT prompt. Currently, system.txt is set as the system prompt then example_1.txt and example_result_1.txt are set as the first User and Assistant inputs, then the current transcript is set as the next User input, then sent to GPT. GPT then generates the Assistant result that contains the prompt for stable-diffusion.

The idea here was that there might be a couple of different sets of "example" pairs (2, 3, 4, etc.) that would generate slightly different prompts. Then `generate.py` could randomly select one of these as an example to send to GPT.

### `recording.py`

Contains methods to wait for voices and to record/transcribe the audio. The Call to OpenAI to transcribe the audio sometimes randomly just never returns a result. To help combat this, it runs in a background thread with a timeout so that if it just goes away, we will eventually get a no result back and we can just go on as though it never happened. This is okay with me b/c we are just sampling the conversation anyway, so missing an occasional snippet is fine.

### `templates`

Html templates folder for `view.py`. Contains the `index.html` file that requests a new image every 5 mins.

### `db/transcript.txt`

Contains transcriptions appended together in a text file. Each line is the result of a transcription of a 15-second snippet of recording.

### `db/prompts.json`

A list of objects, where each object contains the image URL, prompt and datestamp. They are stored in date order so the last one in the list is the most recent.

### `view.py`

Runs a flask server that hosts `/` and `/image`. `/` will return the index. html file, which requests an image from `/image` and renders it, it repeats that process every 5 minutes. `/image` returns a random image from `db/prompts.json`.

Each time a request to the `/image` endpoint happens, the result is also published to the `ADAFRUIT_IO_FEED` from settings so that the sign can pick it up via MQTT push.

Also starts Chrome in kiosk mode and attaches termination signals to it so that it will all shutdown when this shuts down.

### `requirements.txt`

What I think are the minimum required parts to make this script go (After setup)

### `requirements-freeze.txt`

A full `pip3 freeze > requirements-freeze.txt` output, in case I was wrong.

## Setup

1. Install Python 3
2. Create a Virtual Env (in the src directory, to make it easy) (windows: `python -m venv .venv`)
3. Change to the VEnv (`python -m venv .venv`)
4. Intall dependencies `pip3 install -r requirements.txt`

5. Create a `db` directory in the project root:
```bash
mkdir db
touch db/transcript.txt
touch db/prompts.json
```

6. Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```
7. Run it: `python main.py`