import os
import random
import tempfile
import json
import textwrap
import platform
from io import BytesIO
import subprocess
import requests
from PIL import Image, ImageDraw, ImageFont

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "meme_history.json")
MAX_HISTORY = 100

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)['shown_memes']
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump({'shown_memes': history}, f)

def get_random_meme(subreddits: list):
    """
    Fetches a random meme from the Meme API (no authentication needed)
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
        response = requests.get(url)
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
    return None

def add_title_to_image(image, title):
    """Add title text above the image and black strip below"""
    # Try to use Arial font, fallback to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 40)
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

    # Add bottom strip height (50 pixels)
    bottom_strip_height = 50

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
    """Get the primary screen resolution in an OS-independent way"""
    try:
        if platform.system() == 'Windows':
            import ctypes
            user32 = ctypes.windll.user32
            return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        elif platform.system() == 'Linux':
            output = subprocess.check_output(['xrandr']).decode()
            current = [l for l in output.splitlines() if ' connected' in l][0]
            return map(int, current.split()[2].split('x'))
        elif platform.system() == 'Darwin':  # macOS
            output = subprocess.check_output(['system_profiler', 'SPDisplaysDataType'])
            res = [l for l in output.decode().split('\n') if 'Resolution' in l][0]
            return map(int, res.split(':')[1].strip().split(' x '))
    except:
        return 1920, 1080  # fallback resolution

def resize_image(image, target_width, target_height):
    """Resize image to fill screen while maintaining aspect ratio"""
    original_ratio = image.width / image.height
    target_ratio = target_width / target_height

    if target_ratio > original_ratio:
        # Screen is wider than image
        new_height = target_height
        new_width = int(original_ratio * new_height)
    else:
        # Screen is taller than image
        new_width = target_width
        new_height = int(new_width / original_ratio)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

def download_image(url, title):
    response = requests.get(url)
    if response.status_code == 200:
        # Open image from bytes
        image = Image.open(BytesIO(response.content))

        # Convert to RGB if necessary (for PNG images)
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Get screen resolution and resize image
        screen_width, screen_height = get_screen_resolution()
        image = resize_image(image, screen_width, screen_height)

        # Add title to image
        image = add_title_to_image(image, title)

        # Save the modified image
        file_path = os.path.join(tempfile.gettempdir(), "random_meme_wallpaper.jpg")
        image.save(file_path, "JPEG", quality=95)
        return file_path
    return None

def set_wallpaper(image_path):
    """Set wallpaper in an OS-independent way"""
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
    subreddits = [None,
                  "programmingmemes",
                  "ProgrammerHumor",
                  "lotrmemes",
                  "MEOW_IRL",
                  "YouSeeComrade",
                  "DunderMifflin",
                  "workmemes"]
    meme_title, meme_url = get_random_meme(subreddits)
    if meme_url:
        img_path = download_image(meme_url, meme_title)
    else:
        img_path = os.path.join(os.path.dirname(__file__), "fallback_balrog.jpg")
    if img_path and set_wallpaper(img_path):
        print(f"Wallpaper updated! ({img_path})")
    else:
        print("Failed to update wallpaper.")
