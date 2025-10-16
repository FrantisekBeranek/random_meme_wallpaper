"""
Random Meme Wallpaper Setter

This module downloads random meme from Reddit using the Meme API and sets it as desktop wallpaper.
Supports multiple platforms (Windows, macOS, Linux) and maintains a history of shown memes to avoid
repetition. The script can be configured through settings.json file.

The module uses the Meme API (https://github.com/D3vd/Meme_Api) to fetch memes.
"""

import os
import random
import tempfile
import json
import textwrap
import platform
from io import BytesIO
import subprocess
import certifi
import requests
from PIL import Image, ImageDraw, ImageFont

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "meme_history.json")
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

DEFAULT_SETTINGS = {
    "font": {
        "name": "arial.ttf",
        "size": 40
    },
    "bottom_strip_height": 50,
    "max_history": 100,
    "subreddits": [
        None,
        "programmingmemes",
        "ProgrammerHumor",
        "lotrmemes",
        "MEOW_IRL",
        "YouSeeComrade",
        "DunderMifflin",
        "workmemes"
    ]
}

def load_history():
    """
    Load history of previously shown memes from a JSON file.

    Returns:
        list: List of meme URLs that have been previously shown
    """
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)['shown_memes']
    return []

def save_history(history):
    """
    Save the history of shown memes to a JSON file.

    Args:
        history (list): List of meme URLs to save
    """
    with open(HISTORY_FILE, 'w') as f:
        json.dump({'shown_memes': history}, f)

def get_random_meme(subreddits: list):
    """
    Fetch a random meme from specified subreddits using the Meme API.

    Args:
        subreddits (list): List of subreddit names to fetch from (None means random)

    Returns:
        tuple: (meme_title, meme_url) if successful, None if failed
    """
    history = load_history()
    max_attempts = 25

    for _ in range(max_attempts):
        index = random.randint(0, len(subreddits) - 1)
        subreddit = subreddits[index]
        print(f"Selected subreddit: {subreddit if subreddit else 'Default'}")
        url = "https://meme-api.com/gimme"
        if subreddit:
            url += f"/{subreddit}"
        response = requests.get(url, verify=certifi.where())
        if response.status_code == 200:
            data = response.json()
            meme_url = data.get("url")
            meme_title = data.get("title")
            if meme_url not in history:
                history.append(meme_url)
                if len(history) > MAX_HISTORY:
                    history = history[-MAX_HISTORY:]
                save_history(history)
                return meme_title, meme_url
    return None, None

def get_setting(key, default=None):
    """
    Get setting value using dot notation with fallback to default.

    Args:
        key (str): Setting key using dot notation (e.g., 'font.size')
        default: Value to return if key not found (defaults to None)

    Returns:
        The setting value or default/DEFAULT_SETTINGS value if not found
    """
    try:
        value = SETTINGS
        for k in key.split('.'):
            value = value[k]
        return value
    except (KeyError, TypeError):
        return default if default is not None else DEFAULT_SETTINGS.get(key)

def load_settings():
    """
    Load user settings from JSON file with fallback to defaults.

    Returns:
        dict: Dictionary containing user settings or default settings
    """
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return DEFAULT_SETTINGS

SETTINGS = load_settings()
MAX_HISTORY = get_setting('max_history')

def add_title_to_image(image, title):
    """
    Add title text above the image and black strip below.

    Args:
        image (PIL.Image): Source image
        title (str): Text to add above the image

    Returns:
        PIL.Image: New image with added title and bottom strip
    """
    # Try to use configured font, fallback to default if not available
    try:
        font = ImageFont.truetype(
            get_setting('font.name'),
            get_setting('font.size')
        )
    except:
        font = ImageFont.load_default()

    # Wrap text to fit image width
    margin = 20
    max_width = image.width - 2 * margin
    wrapped_text = textwrap.fill(title, width=int(max_width/20))

    # Calculate text height
    dummy_draw = ImageDraw.Draw(image)
    text_bbox = dummy_draw.textbbox((0, 0), wrapped_text, font=font)
    text_height = text_bbox[3] - text_bbox[1] + 2 * margin

    # Add bottom strip height from settings
    bottom_strip_height = get_setting('bottom_strip_height')

    # Create new image with space for title and bottom strip
    new_img = Image.new('RGB',
                        (image.width, image.height + text_height + bottom_strip_height),
                        (0, 0, 0))

    # Add original image in the middle
    new_img.paste(image, (0, text_height))

    # Add title text
    draw = ImageDraw.Draw(new_img)
    draw.text((margin, margin), wrapped_text, font=font, fill='white')

    return new_img

def get_screen_resolution():
    """
    Get primary screen resolution in an OS-independent way.

    Returns:
        tuple: (width, height) of the primary screen, defaults to (1920, 1080)
    """
    try:
        if platform.system() == 'Windows':
            import ctypes
            user32 = ctypes.windll.user32
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        elif platform.system() == 'Linux':
            output = subprocess.Popen(r'xrandr | grep "\*" | cut -d" " -f4',
                                      shell=True, stdout=subprocess.PIPE).communicate()[0]
            resolution = output.split()[0].split(b'x')
            return int(resolution[0]), int(resolution[1])
        elif platform.system() == 'Darwin':  # macOS
            output = subprocess.check_output(['system_profiler', 'SPDisplaysDataType'])
            res = [l for l in output.decode().split('\n') if 'Resolution' in l][0]
            return map(int, res.split(':')[1].strip().split(' x '))
    except:
        return 1920, 1080  # fallback resolution

def resize_image(image, target_width, target_height):
    """
    Resize image to fit screen by adding black bars if needed.

    Args:
        image (PIL.Image): Image to resize
        target_width (int): Target width in pixels
        target_height (int): Target height in pixels

    Returns:
        PIL.Image: Resized image that fits the screen with black bars if needed
    """
    # Calculate ratios
    original_ratio = image.width / image.height
    target_ratio = target_width / target_height

    if target_ratio > original_ratio:
        # Screen is wider than image - fit to height
        new_height = target_height
        new_width = int(target_height * original_ratio)
    else:
        # Screen is taller than image - fit to width
        new_width = target_width
        new_height = int(target_width / original_ratio)

    # Resize image while maintaining aspect ratio
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create black background of target size
    final_image = Image.new('RGB', (target_width, target_height), (0, 0, 0))

    # Calculate position to center the image
    x = (target_width - new_width) // 2
    y = (target_height - new_height) // 2

    # Paste resized image onto black background
    final_image.paste(resized_image, (x, y))

    return final_image

def download_image(url, title):
    """
    Download image from URL and prepare it as wallpaper.

    Args:
        url (str): URL of the image to download
        title (str): Title text to add to the image

    Returns:
        str: Path to the saved wallpaper image or None if failed
    """
    response = requests.get(url, verify=certifi.where())
    if response.status_code == 200:
        # Open image from bytes
        image = Image.open(BytesIO(response.content))

        # Convert to RGB if necessary (for PNG images)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Add title to image
        image = add_title_to_image(image, title)

        # Save the modified image
        file_path = os.path.join(tempfile.gettempdir(), "random_meme_wallpaper.jpg")
        image.save(file_path, "JPEG", quality=95)
        return file_path
    return None

def set_wallpaper(image_path):
    """
    Set wallpaper in an OS-independent way.

    Supports Windows, macOS, and Linux (GNOME, KDE, XFCE).

    Args:
        image_path (str): Path to the image file to use as wallpaper

    Returns:
        bool: True if successful, False otherwise
    """
    # Adjust image to screen size
    image = Image.open(image_path)
    screen_width, screen_height = get_screen_resolution()
    image = resize_image(image, screen_width, screen_height)
    image_path = os.path.join(tempfile.gettempdir(), "random_meme_wallpaper.jpg")
    image.save(image_path, "JPEG", quality=95)

    system = platform.system()

    try:
        if system == 'Windows':
            import ctypes
            ctypes.windll.user32.SystemParametersInfoW(20, 0, image_path, 3)

        elif system == 'Darwin':  # macOS
            script = f'''
                tell application "Finder"
                set desktop picture to POSIX file "{image_path}"
                end tell
                '''
            subprocess.run(['osascript', '-e', script])

        elif system == 'Linux':
            # Try common Linux desktop environments
            desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()

            if 'gnome' in desktop or 'unity' in desktop:
                subprocess.run(['gsettings', 'set', 'org.gnome.desktop.background', 
                             'picture-uri', f'file://{image_path}'])

            elif 'kde' in desktop:
                script = f"""
                var allDesktops = desktops();
                for (i=0; i < allDesktops.length; i++) {{
                    d = allDesktops[i];
                    d.wallpaperPlugin = "org.kde.image";
                    d.currentConfigGroup = Array("Wallpaper", "org.kde.image", "General");
                    d.writeConfig("Image", "file://{image_path}")
                }}
                """
                subprocess.run(['qdbus', 'org.kde.plasmashell', '/PlasmaShell', 
                             'org.kde.PlasmaShell.evaluateScript', script])

            elif 'xfce' in desktop:
                subprocess.run(['xfconf-query', '-c', 'xfce4-desktop', '-p', 
                             '/backdrop/screen0/monitor0/workspace0/last-image', 
                             '-s', image_path])

        return True
    except Exception as e:
        print(f"Failed to set wallpaper: {str(e)}")
        return False

if __name__ == "__main__":
    meme_title, meme_url = get_random_meme(get_setting('subreddits'))
    if meme_url:
        img_path = download_image(meme_url, meme_title)
    else:
        img_path = os.path.join(os.path.dirname(__file__), "fallback_balrog.jpg")
    if img_path and set_wallpaper(img_path):
        print(f"Wallpaper updated! ({img_path})")
    else:
        print("Failed to update wallpaper.")
