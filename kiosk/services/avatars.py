"""Avatar generation and management for kid cards."""
import os
from pathlib import Path

# Sci-fi themed color palettes for generated avatars
AVATAR_COLORS = [
    "#00E5FF",  # Cyan
    "#FF6B35",  # Orange
    "#7B2FBE",  # Purple
    "#00C853",  # Green
    "#FF1744",  # Red
    "#FFD600",  # Gold
    "#2979FF",  # Blue
    "#F50057",  # Pink
    "#00BFA5",  # Teal
    "#FF9100",  # Amber
]

# Preset avatar SVGs — simple geometric sci-fi icons
PRESET_AVATARS = {
    "robot": '''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <rect x="20" y="30" width="60" height="50" rx="8" fill="{color}" opacity="0.9"/>
        <rect x="35" y="10" width="30" height="25" rx="5" fill="{color}" opacity="0.7"/>
        <circle cx="38" cy="50" r="8" fill="#0a0a2e"/>
        <circle cx="62" cy="50" r="8" fill="#0a0a2e"/>
        <circle cx="38" cy="50" r="4" fill="#00E5FF"/>
        <circle cx="62" cy="50" r="4" fill="#00E5FF"/>
        <rect x="40" y="65" width="20" height="5" rx="2" fill="#0a0a2e"/>
        <rect x="10" y="45" width="12" height="8" rx="3" fill="{color}" opacity="0.6"/>
        <rect x="78" y="45" width="12" height="8" rx="3" fill="{color}" opacity="0.6"/>
    </svg>''',
    "rocket": '''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <path d="M50 10 L65 55 L50 50 L35 55 Z" fill="{color}" opacity="0.9"/>
        <path d="M50 50 L65 55 L60 75 L50 70 L40 75 L35 55 Z" fill="{color}" opacity="0.7"/>
        <circle cx="50" cy="38" r="7" fill="#0a0a2e"/>
        <circle cx="50" cy="38" r="4" fill="#00E5FF"/>
        <path d="M35 55 L20 70 L35 65 Z" fill="{color}" opacity="0.5"/>
        <path d="M65 55 L80 70 L65 65 Z" fill="{color}" opacity="0.5"/>
        <path d="M42 75 L50 90 L58 75 Z" fill="#FF6B35" opacity="0.8"/>
    </svg>''',
    "star": '''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <polygon points="50,10 61,38 92,38 67,56 76,85 50,68 24,85 33,56 8,38 39,38" fill="{color}" opacity="0.9"/>
        <polygon points="50,25 57,42 75,42 61,52 66,70 50,60 34,70 39,52 25,42 43,42" fill="{color}" opacity="0.5"/>
    </svg>''',
    "shield": '''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <path d="M50 10 L80 25 L80 55 Q80 80 50 95 Q20 80 20 55 L20 25 Z" fill="{color}" opacity="0.9"/>
        <path d="M50 22 L70 33 L70 53 Q70 72 50 83 Q30 72 30 53 L30 33 Z" fill="#0a0a2e" opacity="0.6"/>
        <path d="M50 35 L60 42 L57 55 L50 50 L43 55 L40 42 Z" fill="{color}" opacity="0.8"/>
    </svg>''',
    "helmet": '''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <path d="M25 55 Q25 20 50 15 Q75 20 75 55 L75 70 Q75 80 50 85 Q25 80 25 70 Z" fill="{color}" opacity="0.9"/>
        <path d="M30 50 L70 50 L70 65 Q70 72 50 75 Q30 72 30 65 Z" fill="#0a0a2e" opacity="0.7"/>
        <rect x="32" y="52" width="36" height="10" rx="3" fill="#00E5FF" opacity="0.6"/>
    </svg>''',
    "planet": '''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="30" fill="{color}" opacity="0.9"/>
        <ellipse cx="50" cy="50" rx="45" ry="12" fill="none" stroke="{color}" stroke-width="3" opacity="0.5" transform="rotate(-20 50 50)"/>
        <circle cx="40" cy="42" r="5" fill="#0a0a2e" opacity="0.3"/>
        <circle cx="58" cy="55" r="8" fill="#0a0a2e" opacity="0.2"/>
    </svg>''',
    "sword": '''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <rect x="47" y="10" width="6" height="55" fill="{color}" opacity="0.9"/>
        <polygon points="50,5 55,15 45,15" fill="{color}"/>
        <rect x="35" y="62" width="30" height="6" rx="2" fill="{color}" opacity="0.7"/>
        <rect x="46" y="68" width="8" height="20" rx="2" fill="{color}" opacity="0.6"/>
        <circle cx="50" cy="91" r="4" fill="{color}" opacity="0.5"/>
    </svg>''',
    "crystal": '''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <polygon points="50,10 70,40 65,85 50,95 35,85 30,40" fill="{color}" opacity="0.9"/>
        <polygon points="50,10 60,40 50,50 40,40" fill="{color}" opacity="0.5"/>
        <polygon points="50,50 65,85 50,95 35,85" fill="{color}" opacity="0.7"/>
        <line x1="50" y1="10" x2="50" y2="95" stroke="#fff" stroke-width="1" opacity="0.3"/>
    </svg>''',
}


def get_avatar_choices():
    """Return list of available avatar identifiers."""
    return list(PRESET_AVATARS.keys())


def parse_avatar_path(avatar_path: str):
    """Parse an avatar_path string into (avatar_name, color_index).

    Supports both legacy bare names ("robot") and the new encoded format
    ("robot:3").  Unknown or empty paths return ("", 0).
    """
    if not avatar_path or avatar_path == "/static/default_avatar.png":
        return ("", 0)
    if ":" in avatar_path:
        parts = avatar_path.split(":", 1)
        name = parts[0]
        try:
            color_index = int(parts[1])
        except ValueError:
            color_index = 0
    else:
        name = avatar_path
        color_index = 0
    # Validate name is a known avatar; fall back to initials if not
    if name not in PRESET_AVATARS:
        name = ""
    return (name, color_index)


def encode_avatar_path(avatar_name: str, color_index: int) -> str:
    """Encode avatar name + color index into a storable string.

    Empty avatar_name means "use initials" and is stored as "".
    """
    if not avatar_name:
        return ""
    return f"{avatar_name}:{color_index}"


def get_avatar_svg(avatar_name: str, color_index: int = 0) -> str:
    """Get SVG string for an avatar with a specific color."""
    color = AVATAR_COLORS[color_index % len(AVATAR_COLORS)]
    template = PRESET_AVATARS.get(avatar_name, PRESET_AVATARS["star"])
    return template.format(color=color)


def get_initials_svg(name: str, color_index: int = 0) -> str:
    """Generate a simple initials-based avatar."""
    color = AVATAR_COLORS[color_index % len(AVATAR_COLORS)]
    initials = "".join(w[0].upper() for w in name.split()[:2]) if name else "?"
    return f'''<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
        <circle cx="50" cy="50" r="45" fill="{color}" opacity="0.2"/>
        <circle cx="50" cy="50" r="45" fill="none" stroke="{color}" stroke-width="3" opacity="0.8"/>
        <text x="50" y="58" text-anchor="middle" font-size="36" font-weight="bold" 
              font-family="Arial, sans-serif" fill="{color}">{initials}</text>
    </svg>'''
