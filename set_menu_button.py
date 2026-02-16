import requests
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
FRONTEND_URL = os.getenv("FRONTEND_URL")

if not BOT_TOKEN:
    print("Error: BOT_TOKEN not found in .env")
    exit(1)

if not FRONTEND_URL:
    print("Error: FRONTEND_URL not found in .env")
    exit(1)

def set_menu_button():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setChatMenuButton"
    
    payload = {
        "menu_button": {
            "type": "web_app",
            "text": "Open App",
            "web_app": {
                "url": FRONTEND_URL
            }
        }
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(f"Success! Response: {response.json()}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        if e.response:
            print(f"Details: {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print(f"Setting Menu Button for URL: {FRONTEND_URL}")
    set_menu_button()
