import io
import requests
import time
from abc import ABC, abstractmethod

class ModerationBlockedException(Exception):
    """Raised when an image generation request is blocked by the safety system"""
    def __init__(self, message, original_prompt):
        super().__init__(message)
        self.original_prompt = original_prompt

class ImageGenerator(ABC):
    """Base class for image generation providers"""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate an image and return its URL"""
        pass

class CustomAIGenerator(ImageGenerator):
    """Custom AI image generator implementation"""
    
    def __init__(self, endpoint_url: str, auth_code: str):
        if not auth_code:
            raise ValueError("No auth code provided for Custom AI endpoint")
        self.endpoint_url = endpoint_url.rstrip('/')
        self.auth_code = auth_code
        
    def generate(self, prompt: str) -> str:
        url = f"{self.endpoint_url}/api/GenerateImage?code={self.auth_code}"
        data = {
            "group": "whisperframe",
            "type": "raw",
            "size": "1536x1024",
            "details": prompt
        }
        print(url)
        print(data)
        
        max_retries = 3
        initial_wait = 10
        attempt = 0
        
        while attempt <= max_retries:
            try:
                resp = requests.post(url, json=data)
                
                if 200 <= resp.status_code < 300:
                    result = resp.json()
                    print(result)
                    # Add code parameter to image URL
                    image_url = f"{self.endpoint_url}/{result['imageUrl']}?code={self.auth_code}"
                    print(image_url)
                    return image_url
                
                # For any non-2xx response, first check if it's a moderation block
                try:
                    error_data = resp.json()
                    if error_data.get("error", {}).get("code") == "moderation_blocked":
                        raise ModerationBlockedException(error_data["error"]["message"], prompt)
                except (ValueError, KeyError):
                    # Not a JSON response or not the moderation error format,
                    # so it's not a moderation_blocked error we can parse.
                    # Proceed to check status code for other errors.
                    pass 
                
                # Now handle specific status codes like 500 for retries,
                # or other errors.
                if resp.status_code == 500:
                    # If we are here, it means it was a 500 but NOT a moderation_blocked error
                    # (or if it was, ModerationBlockedException was already raised).
                    attempt += 1
                    if attempt > max_retries:
                        raise Exception(f"Max retries ({max_retries}) exceeded for 500 error. Last error: {resp.text}")
                    
                    wait_time = initial_wait * (2 ** (attempt - 1))  # exponential backoff
                    print(f"Got 500 error (not moderation_blocked), attempt {attempt}/{max_retries}. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                
                else: # For any other error status code (not 2xx, not 500, and not moderation_blocked)
                    # This 'else' now covers non-2xx, non-500 errors that weren't moderation blocks.
                    raise Exception(f"Image generation failed with status {resp.status_code}: {resp.text}")
                    
            except requests.exceptions.RequestException as e:
                # Handle network-related errors
                attempt += 1
                if attempt > max_retries:
                    raise Exception(f"Max retries ({max_retries}) exceeded. Last error: {str(e)}")
                
                wait_time = initial_wait * (2 ** (attempt - 1))
                print(f"Network error, attempt {attempt}/{max_retries}. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                continue
        
        raise Exception("Image generation failed after all retries")