import os

# Disable auto-download of undetected-chromedriveros.environ.setdefault("UC_NO_SANDBOX", "true")
os.environ.setdefault("UC_DISABLE_AUTO_DOWNLOAD", "false")

# Other code...

def main():
    # Existing code...
    click_button = None  # Updated line 138
    # Existing code...
    options.add_argument('--headless=new')  # Updated line 182
    options.add_argument('--disable-web-security')  # Added new flag
    # Existing code...
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"  # Updated line 186
    # Existing code...