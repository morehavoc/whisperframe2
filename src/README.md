# WhisperFrame Setup & Configuration Guide

This guide covers the technical setup, configuration, and troubleshooting for WhisperFrame. For an overview of how the system works, see the [main README](../README.md).

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi 4 (4GB+ recommended) with Raspberry Pi OS
- **Any microphone** (USB microphone or ReSpeaker 4-Mic HAT)
- Python 3.8+ with pip
- Internet connection for API calls

### 0. Python Setup

#### Create venv:
```bash
python -m venv .venv
```

#### Activate it:
```bash
source .venv/bin/activate
```

#### Install PyAudio:
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
```

#### Install:
```bash
pip install -r requirements.txt
```

### 1. Hardware Setup

#### Option A: USB Microphone (Recommended)
```bash
# Simply plug in your USB microphone - no additional setup required!
# Test that it's detected:
python3 main.py --show_audio_devices
```

Most USB microphones will appear as device 0 or 1. This is the simplest setup option.

#### Option B: ReSpeaker 4-Mic HAT (Advanced)
Only follow these steps if you're using the ReSpeaker HAT:

```bash
# Clone and install the voice card drivers
git clone https://github.com/respeaker/seeed-voicecard
cd seeed-voicecard
sudo ./install.sh
sudo reboot
```

#### Verify Audio Setup
```bash
# Check available audio devices
python3 main.py --show_audio_devices

# Test recording with your microphone
arecord -D plughw:0 -c 1 -r 16000 -f S16_LE -d 5 test.wav

# Play back to verify
aplay test.wav
```

### 2. Software Installation

```bash
# Clone the repository
git clone https://github.com/morehavoc/whisperframe2.git
cd whisperframe2/src

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create database directories
mkdir db
touch db/transcript.txt
echo "[]" > db/prompts.json
```

### 3. Configuration

Create a `.env` file in the `src/` directory with your API credentials:

```env
# Required API Keys
OPENAI_API_KEY=sk-your-openai-api-key-here
CUSTOM_AI_ENDPOINT=https://your-custom-ai-endpoint.azurewebsites.net
CUSTOM_AI_CODE=your-function-auth-code

# Hardware Configuration
INPUT_DEVICE_ID=0
ENABLE_LEDS=true

# Optional: External Signage
ADAFRUIT_IO_USERNAME=your-adafruit-username
ADAFRUIT_IO_KEY=your-adafruit-key
ADAFRUIT_IO_FEED=whisperframe

# Optional: Browser Control
START_BROWSER=true
```

### 4. First Run

```bash
# Test audio device detection
python3 main.py --show_audio_devices

# Run the system
python3 main.py
```

The system will:
1. Generate an initial image from any existing transcript
2. Start the Flask web server on `http://localhost:5000`
3. Optionally open a browser in kiosk mode
4. Begin listening for conversations

## 🔧 Detailed Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for Whisper and GPT-4 |
| `CUSTOM_AI_ENDPOINT` | Yes | - | URL of your custom AI image generation endpoint |
| `CUSTOM_AI_CODE` | Yes | - | Authentication code for the custom endpoint |
| `INPUT_DEVICE_ID` | No | 0 | Audio input device index (use --show_audio_devices to find) |
| `ENABLE_LEDS` | No | false | Enable ReSpeaker LED ring progress indicators |
| `START_BROWSER` | No | false | Automatically start browser in kiosk mode |
| `ADAFRUIT_IO_USERNAME` | No | - | Username for Adafruit IO external signage |
| `ADAFRUIT_IO_KEY` | No | - | Key for Adafruit IO |
| `ADAFRUIT_IO_FEED` | No | whisperframe | Feed name for Adafruit IO |

### Audio Configuration

#### Finding Your Audio Device
```bash
python3 main.py --show_audio_devices
```

This will list available audio devices. USB microphones typically appear as device 0 or 1, while the ReSpeaker HAT appears as device 0 when properly installed.

#### Adjusting Voice Activity Detection
In `recording.py`, you can adjust the WebRTC VAD sensitivity:

```python
vad = webrtcvad.Vad(3)  # 0-3, where 3 is most aggressive
```

- **Mode 0**: Least aggressive, good for quiet environments
- **Mode 1**: Moderate sensitivity  
- **Mode 2**: More aggressive, good for noisy environments
- **Mode 3**: Most aggressive, may pick up background noise

**Note**: USB microphones may require different sensitivity settings than the ReSpeaker HAT due to different pickup patterns and noise characteristics.

#### Audio Not Working
```bash
# Check available audio devices
python3 main.py --show_audio_devices

# For USB microphones:
arecord -D plughw:0 -c 1 -r 16000 -f S16_LE -d 5 test.wav

# For ReSpeaker HAT:
arecord -D plughw:0 -c 6 -r 16000 -f S16_LE -d 5 test.wav

# Play back to verify
aplay test.wav
```

**USB Microphone Issues:**
- Ensure the microphone is properly connected and recognized by the system
- Try different USB ports if the device isn't detected
- Some microphones may require specific drivers - check manufacturer documentation

**ReSpeaker HAT Issues:**
- Verify the HAT is properly seated on the GPIO pins
- Ensure the voice card drivers were installed correctly
- Check that the device appears in `arecord -l` output

### Prompt Engineering

The system uses several prompt files in the `prompts/` directory:

#### `system.txt`
Main system prompt that defines the AI's role and constraints. Key elements:
- Instructs the AI to create concise image descriptions
- Specifies format requirements (subject, medium, style, details)
- Sets content guidelines and restrictions

#### `example_1.txt` & `example_result_1.txt`
Example conversation and corresponding image prompt. Used for few-shot learning to guide the AI's output style.

#### `name_system.txt`
System prompt for generating creative artist names for each image.

### Customizing Art Generation

#### Adjusting Generation Frequency
In `main.py`, change the counter threshold:
```python
if line_counter >= 20:  # Generate every 20 snippets (~5 minutes)
```

#### Modifying Conversation Window
In `generate.py`, adjust how many transcript lines are used:
```python
lines = get_last_lines(transcript_file, 20)  # Use last 20 lines
```

#### Changing Buffer Size
In `recording.py`, modify the maximum transcript storage:
```python
MAX_TRANSCRIPT_LINES = 120  # Keep 120 lines (~10 minutes)
```

## 🖥️ Display Configuration

### Web Interface Customization

#### HTML Template (`templates/index.html`)
Minimal template that loads CSS and JavaScript for the display interface.

#### Styling (`static/style.css`)
- Background image transitions
- Text overlay positioning and opacity
- Responsive design elements

#### JavaScript (`static/script.js`)
- WebSocket connection for real-time updates
- Periodic image fetching (fallback)
- Image transition handling

### Display Behavior

The system intelligently chooses which image to display:

1. **Recent Images** (last 30 minutes): Shows the most recent image when conversation is active
2. **Random Selection**: During quiet periods, randomly selects from historical images
3. **Night Mode**: Goes dark between midnight and 7 AM
4. **Seed-based Randomization**: Uses time-based seeding so the same random image is shown for 5-minute intervals

## 🔍 Troubleshooting

### Common Issues

#### Audio Not Working
```bash
# Check available audio devices
python3 main.py --show_audio_devices

# For USB microphones:
arecord -D plughw:0 -c 1 -r 16000 -f S16_LE -d 5 test.wav

# For ReSpeaker HAT:
arecord -D plughw:0 -c 6 -r 16000 -f S16_LE -d 5 test.wav

# Play back to verify
aplay test.wav
```

**USB Microphone Issues:**
- Ensure the microphone is properly connected and recognized by the system
- Try different USB ports if the device isn't detected
- Some microphones may require specific drivers - check manufacturer documentation

**ReSpeaker HAT Issues:**
- Verify the HAT is properly seated on the GPIO pins
- Ensure the voice card drivers were installed correctly
- Check that the device appears in `arecord -l` output

#### API Errors
- **OpenAI API**: Verify your API key has sufficient credits and proper permissions
- **Custom AI Endpoint**: Ensure the endpoint URL and auth code are correct
- **Network Issues**: Check internet connectivity and firewall settings

#### Image Generation Failures
- Check the console output for specific error messages
- Verify the custom AI endpoint is responding
- Ensure prompts aren't being blocked by safety filters

#### Display Issues
- Verify Flask server is running on port 5000
- Check browser console for JavaScript errors
- Ensure WebSocket connections are working

### Debug Mode

Enable debug logging by modifying `view.py`:
```python
app.run(host="0.0.0.0", debug=True)
```

### Log Files

The system outputs to console. To capture logs:
```bash
python3 main.py 2>&1 | tee whisperframe.log
```

## 🔄 Running as a Service

### Systemd Service (Recommended)

Create `/etc/systemd/system/whisperframe.service`:
```ini
[Unit]
Description=WhisperFrame AI Art Generator
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/whisperframe2/src
Environment=PATH=/home/pi/whisperframe2/src/.venv/bin
ExecStart=/home/pi/whisperframe2/src/.venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable whisperframe
sudo systemctl start whisperframe
sudo systemctl status whisperframe
```

For seeing the console log:
```bash
sudo journalctl -u whisperframe.service -n 200 --no-pager
```

### Auto-start Browser

For kiosk mode, add to `/etc/xdg/lxsession/LXDE-pi/autostart`:
```
@chromium-browser --kiosk --disable-infobars http://localhost:5000
```

## 📊 Performance Optimization

### Raspberry Pi 4 Recommendations
- Use a high-quality SD card (Class 10 or better)
- Ensure adequate cooling to prevent throttling
- Consider overclocking for better performance
- Use a reliable power supply (official Pi PSU recommended)

### Memory Management
- The system keeps a rolling buffer of transcripts to manage memory usage
- Images are stored remotely (Azure) to avoid filling local storage
- Consider periodic cleanup of old log files

### Network Optimization
- Use a stable internet connection for API calls
- Consider local caching for improved reliability
- Monitor API usage to manage costs

## 🛡️ Security Considerations

- Store API keys securely in `.env` files (never commit to version control)
- Consider network isolation for the Pi if used in sensitive environments
- Regularly update dependencies for security patches
- The system doesn't store conversation content long-term (rolling buffer only)

## 📈 Monitoring & Maintenance

### Health Checks
- Monitor API call success rates
- Check disk space usage
- Verify audio input levels
- Monitor system temperature and performance

### Regular Maintenance
- Update dependencies periodically
- Clean up old log files
- Backup configuration files
- Test hardware components

---

For questions about how the system works conceptually, see the [main README](../README.md). For technical issues, check the troubleshooting section above or review the console output for specific error messages.
