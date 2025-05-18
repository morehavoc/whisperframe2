import openai
import json
from datetime import datetime
import settings
from image_generators import CustomAIGenerator
import view

def read_all(filename):
    with open(filename, "r") as f:
        return f.read()

def get_last_lines(transcript_file, num_of_lines):
    with open(transcript_file, "r") as f:
        lines = f.readlines()
        return "\n".join(lines[-num_of_lines:])

def save_image(prompt, url, artist_name, db_file):
    data = {
        'prompt': prompt,
        'url': url,
        'date': datetime.today().isoformat(),
        'name': artist_name
    }

    existing_data = list()
    try:
        with open(db_file, "r") as f:
            existing_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        existing_data = list()

    existing_data.append(data)

    with open(db_file, "w") as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=4)
        
    # Notify WebSocket clients of the new image
    view.notify_clients(data)

def run(openai_api_key, num_of_lines, db_file, transcript_file):
    client = openai.OpenAI(api_key=openai_api_key)
    lines = get_last_lines(transcript_file, num_of_lines)
    print("* Summarizing")
    r = client.chat.completions.create(
      model="gpt-4.1",
      messages=[
        {"role": "system", "content": read_all("prompts/system.txt")},
        {"role": "user", "content": read_all("prompts/example_1.txt")},
        {"role": "assistant", "content": read_all("prompts/example_result_1.txt")},
        {"role": "user", "content": lines}
      ]
    )

    prompt = r.choices[0].message.content
    print("* Prompt:")
    print(prompt)

    print("* Naming")
    r = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {"role": "system", "content": read_all("prompts/name_system.txt")},
            {"role": "user", "content": prompt}
        ]
    )
    artist_name = r.choices[0].message.content
    print("* Name:")
    print(artist_name)

    print("* Generating")
    generator = CustomAIGenerator(settings.CUSTOM_AI_ENDPOINT, settings.CUSTOM_AI_CODE)
    imgurl = generator.generate(prompt)
    save_image(prompt, imgurl, artist_name, db_file)
