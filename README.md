# Random Meme Wallpaper

A cross-platform Python script that fetches random memes from Reddit and sets them as your desktop wallpaper. The script adds the meme title at the top of the image and keeps track of shown memes to avoid repetition.

## Features

- Fetches random memes from multiple subreddits
- Cross-platform support (Windows, MacOS, Linux)
- Adds meme title to the wallpaper
- Maintains aspect ratio when resizing
- Keeps history of shown memes to avoid repetition
- Supports multiple desktop environments on Linux (GNOME, KDE, XFCE)
- Automatically resizes images to fit your screen resolution
- Adds convenient black strips for better desktop icon visibility

## API

This project uses the [Meme_Api](https://github.com/D3vd/Meme_Api) (also known as "Meme Developer API"), which provides a simple way to fetch random memes from various subreddits. The API is free to use and requires no authentication.

## Installation

1. Clone this repository:

```bash
git clone https://github.com/yourusername/random_meme_wallpaper.git
cd random_meme_wallpaper
```

2. Install required packages:

```bash
pip install Pillow requests
```

3. Additional requirements for Linux users (depending on your desktop environment):
- GNOME: `gsettings` (usually pre-installed)
- KDE: `qdbus-qt5`
- XFCE: `xfconf`

## Usage

Simply run the script:

```bash
python random_meme.py
```

The script will:
1. Select a random subreddit from the configured list
2. Download a random meme
3. Resize it to fit your screen
4. Add the meme title at the top
5. Set it as your desktop wallpaper

## Configuration

The script can be configured through the `settings.json` file:

```json
{
    "font": {
        "name": "arial.ttf",
        "size": 40
    },
    "bottom_strip_height": 50,
    "max_history": 100,
    "subreddits": [
        null,
        "programmingmemes",
        "ProgrammerHumor",
        "lotrmemes",
        "MEOW_IRL",
        "YouSeeComrade",
        "DunderMifflin",
        "workmemes"
    ]
}
```

### Settings Options

- `font.name`: The font file to use for the meme title
- `font.size`: Font size for the meme title
- `bottom_strip_height`: Height of the black strip at the bottom (in pixels)
- `max_history`: Number of memes to keep in history to avoid repetition
- `subreddits`: List of subreddits to fetch memes from (null means random from all)

## Notes

- The script maintains a history of the last 100 shown memes to avoid repetition
- If a meme cannot be fetched, it will use a fallback image
- Images are temporarily stored in your system's temp directory
- For now tested on Windows only
![Fallback Balrog](./fallback_balrog.jpg)

## Requirements

- Python 3.6+
- Pillow
- Requests

## License

This project is open source and available under the MIT License.

:sheep:
