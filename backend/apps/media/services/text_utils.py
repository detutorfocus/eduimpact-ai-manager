"""
Media Module — Text Utilities
Handles text formatting and truncation for quote cards.
"""
import textwrap
from PIL import ImageFont
import os


def wrap_text(text: str, max_chars_per_line: int = 30) -> list:
    """
    Wrap text into lines of max_chars_per_line.
    Returns a list of strings.
    """
    return textwrap.wrap(text, width=max_chars_per_line)


def truncate_text(text: str, max_length: int = 120, suffix: str = "...") -> str:
    """Truncate text to max_length characters."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rstrip() + suffix


def clean_hashtags(hashtags: list) -> str:
    """Format a list of hashtags into a string. Adds # if missing."""
    result = []
    for tag in hashtags[:5]:  # max 5 on image
        tag = tag.strip()
        if not tag.startswith("#"):
            tag = f"#{tag}"
        result.append(tag)
    return "  ".join(result)


def get_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a TTF font, fall back to default if not found."""
    try:
        return ImageFont.truetype(font_path, size)
    except (IOError, OSError):
        return ImageFont.load_default()


def estimate_text_height(text: str, font, line_spacing: int = 10) -> int:
    """Estimate pixel height of wrapped text block."""
    lines = wrap_text(text, max_chars_per_line=28)
    # Approximate: each line ~font_size + spacing pixels
    try:
        bbox = font.getbbox("A")
        line_height = bbox[3] - bbox[1]
    except AttributeError:
        line_height = 20
    return len(lines) * (line_height + line_spacing)


def split_into_lines_by_pixel_width(
    text: str, font, max_width: int
) -> list:
    """
    Split text into lines that fit within max_width pixels.
    More precise than character-count wrapping.
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = " ".join(current_line + [word])
        try:
            bbox = font.getbbox(test_line)
            line_width = bbox[2] - bbox[0]
        except AttributeError:
            line_width = len(test_line) * 12  # fallback estimate

        if line_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines
