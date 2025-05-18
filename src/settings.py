import os
from dotenv import load_dotenv

load_dotenv()

# API Keys and Secrets (loaded from .env)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CUSTOM_AI_ENDPOINT = os.getenv('CUSTOM_AI_ENDPOINT', 'http://localhost:7071')
CUSTOM_AI_CODE = os.getenv('CUSTOM_AI_CODE')  # Authentication code for custom AI endpoint
ADAFRUIT_IO_USERNAME = os.getenv('ADAFRUIT_IO_USERNAME')
ADAFRUIT_IO_KEY = os.getenv('ADAFRUIT_IO_KEY')
ADAFRUIT_IO_FEED = os.getenv('ADAFRUIT_IO_FEED', 'whisperframe')
PV_ACCESS_KEY = os.getenv('PV_ACCESS_KEY')

# Hardware configuration
INPUT_DEVICE_ID = int(os.getenv('INPUT_DEVICE_ID', '0'))
ENABLE_LEDS = os.getenv('ENABLE_LEDS', 'false').lower() == 'true'

# Browser settings
START_BROWSER = os.getenv('START_BROWSER', 'false').lower() == 'true'

# File paths
TRANSCRIPT_FILE = "db/transcript.txt"
DB_FILE = "db/prompts.json"