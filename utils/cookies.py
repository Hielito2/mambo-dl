from pathlib import Path
import json

COOKIES_DIR = Path(__file__).parent.parent.resolve() / 'cookies' 

def get_cookie_filename(source_name: str) -> Path:
    """Generates a site-specific cookie filename."""
    return COOKIES_DIR / f"{source_name}_cookies.json"

# --- Saving Cookies in SourceA.py or main script ---
def save_cookies(cookies, source_name: str):
    """Saves httpx.Cookies object to a site-specific JSON file."""
    cookie_file = get_cookie_filename(source_name)
    
    with open(cookie_file, 'w') as f:
        json.dump(dict(cookies), f, indent=4)
    print(f"Cookies saved to {cookie_file.stem}")

# --- Loading Cookies in SourceA.py or main script ---
def load_cookies(source_name: str):
    """Loads cookies from a site-specific JSON file."""
    cookie_file = get_cookie_filename(source_name)
    
    if not cookie_file.exists():
        print("Not cookies found\n")
        return {}
        
    with open(cookie_file, 'r') as f:
        cookies_dict = json.load(f)
        
    print(f"Cookies loaded from {cookie_file.stem}")
    return cookies_dict