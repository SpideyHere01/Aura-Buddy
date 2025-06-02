"""Configuration settings for the drop game"""

GAME_SETTINGS = {
    'drop_timeout': 30,
    'claim_cooldown': 600,
    'card_dimensions': {
        'normal': (350, 600),
        'claimed': (200, 280)
    },
    'probabilities': {
        'normal': 0.80,
        'legendary': 0.15,
        'loser': 0.05
    }
}

import os
from PIL import ImageFont

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_PATHS = {
    'bold': [
        os.path.join(CURRENT_DIR, 'fonts', 'Roboto-Bold.ttf'),
        os.path.join(CURRENT_DIR, '..', 'fonts', 'Roboto-Bold.ttf'),
        'C:/Windows/Fonts/Arial.ttf',  # Windows system font
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',  # Linux system font
    ],
    'regular': [
        os.path.join(CURRENT_DIR, 'fonts', 'Roboto-Regular.ttf'),
        os.path.join(CURRENT_DIR, '..', 'fonts', 'Roboto-Regular.ttf'),
        'C:/Windows/Fonts/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ],
    'light': [
        os.path.join(CURRENT_DIR, 'fonts', 'Roboto-Light.ttf'),
        os.path.join(CURRENT_DIR, '..', 'fonts', 'Roboto-Light.ttf'),
        'C:/Windows/Fonts/Arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
}

def load_font(font_type: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font, trying multiple paths and falling back to default if needed."""
    if font_type not in FONT_PATHS:
        return ImageFont.load_default()
        
    for path in FONT_PATHS[font_type]:
        try:
            if os.path.exists(path):
                return ImageFont.truetype(path, size)
        except Exception:
            continue
            
    return ImageFont.load_default() 