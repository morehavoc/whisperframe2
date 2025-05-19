import openai
import json
from datetime import datetime
import settings
from image_generators import CustomAIGenerator, ModerationBlockedException
import requests
import view

def read_all(filename):
    with open(filename, "r") as f:
        return f.read()

def get_last_lines(transcript_file, num_of_lines):
    with open(transcript_file, "r") as f:
        lines = f.readlines()
        return "\n".join(lines[-num_of_lines:])

def _notify_view_app(data):
    """Send notification to view.py about new image via HTTP request"""
    try:
        response = requests.post(
            "http://localhost:5000/_internal/notify_new_image",
            json=data,
            timeout=2  # Short timeout for local request
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Warning: Failed to notify view app about new image: {e}")

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
        
    # Notify view.py about the new image via HTTP
    _notify_view_app(data)

def rewrite_prompt_for_safety(client, original_prompt):
    """Rewrite a prompt that was rejected by the safety system"""
    print(f"Rewriting prompt for safety: {original_prompt}")
    try:
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "system",
                    "content": "The following prompt for an image generator was rejected due to safety concerns. Please rewrite it to make it compliant with typical content safety policies, while preserving the core artistic idea as much as possible. Return only the rewritten prompt. When possible make the new prompt as simple as possible."
                },
                {"role": "user", "content": original_prompt}
            ]
        )
        rewritten_prompt = response.choices[0].message.content.strip()
        print(f"Rewritten prompt: {rewritten_prompt}")
        return rewritten_prompt
    except Exception as e:
        print(f"Error during prompt rewriting: {e}")
        return None

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
    current_prompt_being_tried = prompt
    safety_rewrites_performed = 0
    MAX_SAFETY_REWRITES = 1  # Allow one rewrite attempt

    while True:  # Loop for safety rewrites
        print(f"Attempting to generate image with prompt: '{current_prompt_being_tried}' (Rewrite #{safety_rewrites_performed})")
        try:
            generator = CustomAIGenerator(settings.CUSTOM_AI_ENDPOINT, settings.CUSTOM_AI_CODE)
            imgurl = generator.generate(current_prompt_being_tried)  # Has internal retries for network/500 errors
            save_image(current_prompt_being_tried, imgurl, artist_name, db_file)
            print("  Image generated successfully.")
            return  # SUCCESS
        except ModerationBlockedException as mbe:
            print(f"  Moderation system blocked prompt: {mbe.original_prompt}")
            if safety_rewrites_performed < MAX_SAFETY_REWRITES:
                print("  Attempting to rewrite...")
                new_prompt = rewrite_prompt_for_safety(client, current_prompt_being_tried)
                if new_prompt and new_prompt != current_prompt_being_tried:
                    current_prompt_being_tried = new_prompt
                    safety_rewrites_performed += 1
                    continue  # Try the new prompt
                else:
                    print("  Rewrite failed or produced the same prompt. Aborting.")
                    return  # FAILURE
            else:
                print("  Max safety rewrites reached. Aborting.")
                return  # FAILURE
        except Exception as e:  # Other errors from generator.generate() after its internal retries
            print(f"  Image generation failed for prompt '{current_prompt_being_tried}': {e}")
            # If a prompt version fails with a general error, we give up on it.
            # If no more rewrites are allowed, we give up entirely.
            if safety_rewrites_performed >= MAX_SAFETY_REWRITES:
                print("  No more safety rewrites possible. Aborting.")
                return  # FAILURE
            else:
                # This means the current prompt failed its attempt.
                # We only rewrite on ModerationBlocked. So, if a prompt fails general attempts, it's done.
                print(f"  Prompt '{current_prompt_being_tried}' failed. Aborting as we only rewrite on moderation blocks.")
                return  # FAILURE
        
        # Should not be reached if logic is correct
        if safety_rewrites_performed >= MAX_SAFETY_REWRITES:  # Ensure loop terminates
            break
    
    print("Image generation ultimately failed.")  # Fallback message
