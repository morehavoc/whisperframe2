python -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt 
mkdir db
touch db/transcript.txt
touch db/prompts.json
cp .env.example .env