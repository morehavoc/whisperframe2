import io
import requests
import time
from abc import ABC, abstractmethod

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
            "type": "whisperframe",
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
                
                elif resp.status_code == 500:
                    attempt += 1
                    if attempt > max_retries:
                        raise Exception(f"Max retries ({max_retries}) exceeded. Last error: {resp.text}")
                    
                    wait_time = initial_wait * (2 ** (attempt - 1))  # exponential backoff
                    print(f"Got 500 error, attempt {attempt}/{max_retries}. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                
                else:
                    # For any other error status code, fail immediately
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