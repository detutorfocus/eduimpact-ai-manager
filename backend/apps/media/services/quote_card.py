"""
Media Module — Quote Card Generator
Converts text content into branded quote card images using Pillow.
"""
import os
import logging
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from django.conf import settings
from .text_utils import split_into_lines_by_pixel_width, clean_hashtags, get_font

logger = logging.getLogger(__name__)

# ─── Brand Themes ─────────────────────────────────────────────────────────────
BRAND_THEMES = {
    "devotional": {
        "bg_color": (35, 30, 60),          # Deep purple
        "accent_color": (212, 175, 55),    # Gold
        "text_color": (255, 255, 240),     # Warm white
        "subtitle_color": (200, 190, 150),
        "watermark": "✦ Faith & Grace ✦",
    },
    "programming": {
        "bg_color": (15, 20, 35),          # Dark navy
        "accent_color": (0, 200, 100),     # Green (code)
        "text_color": (220, 255, 220),
        "subtitle_color": (150, 200, 150),
        "watermark": "< CodeHub />",
    },
    "education": {
        "bg_color": (20, 45, 90),          # Deep blue
        "accent_color": (255, 180, 0),     # Amber
        "text_color": (255, 255, 255),
        "subtitle_color": (200, 210, 240),
        "watermark": "EduImpactHub",
    },
    "forex": {
        "bg_color": (10, 25, 15),          # Dark green
        "accent_color": (0, 220, 130),     # Bright green
        "text_color": (230, 255, 230),
        "subtitle_color": (150, 220, 160),
        "watermark": "FX Insights",
    },
    "motivation": {
        "bg_color": (80, 20, 20),          # Deep red
        "accent_color": (255, 120, 50),    # Orange
        "text_color": (255, 245, 235),
        "subtitle_color": (240, 180, 140),
        "watermark": "Rise & Win",
    },
    "general": {
        "bg_color": (30, 30, 40),
        "accent_color": (100, 150, 255),
        "text_color": (240, 240, 255),
        "subtitle_color": (180, 180, 220),
        "watermark": "EduImpact",
    },
}

DEFAULT_THEME = BRAND_THEMES["general"]

# ─── Font Paths ───────────────────────────────────────────────────────────────
FONTS_DIR = os.path.join(settings.BASE_DIR, "assets", "fonts")
FONT_BOLD = os.path.join(FONTS_DIR, "Montserrat-Bold.ttf")
FONT_REGULAR = os.path.join(FONTS_DIR, "Montserrat-Regular.ttf")
FONT_ITALIC = os.path.join(FONTS_DIR, "Montserrat-Italic.ttf")

# Card dimensions (Facebook/Instagram optimised 1:1)
CARD_WIDTH = 1080
CARD_HEIGHT = 1080

# Output directory
OUTPUT_DIR = os.path.join(settings.MEDIA_ROOT, "quote_cards")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class QuoteCardGenerator:
    """
    Generates branded quote card images from text content.
    """

    def generate(
        self,
        post_text: str,
        brand_name: str,
        caption: str = "",
        hashtags: list = None,
        content_type: str = "general",
    ) -> str:
        """
        Creates a quote card image and returns the file path.

        Args:
            post_text: Main quote text
            brand_name: Brand display name
            caption: Subtitle / CTA text
            hashtags: List of hashtags
            content_type: Used to select the theme

        Returns:
            Absolute path to the saved image file.
        """
        theme = BRAND_THEMES.get(content_type, DEFAULT_THEME)
        img = self._create_background(theme)
        draw = ImageDraw.Draw(img)

        # Load fonts
        font_title = get_font(FONT_BOLD, 62)
        font_caption = get_font(FONT_REGULAR, 38)
        font_watermark = get_font(FONT_BOLD, 28)
        font_hashtag = get_font(FONT_ITALIC, 26)

        padding = 80
        usable_width = CARD_WIDTH - (padding * 2)

        # ── Top accent bar ──
        draw.rectangle(
            [(padding, 70), (CARD_WIDTH - padding, 76)],
            fill=theme["accent_color"],
        )

        # ── Main quote text ──
        lines = split_into_lines_by_pixel_width(post_text, font_title, usable_width)
        text_y = 130
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font_title)
            text_w = bbox[2] - bbox[0]
            x = (CARD_WIDTH - text_w) // 2  # center
            draw.text((x, text_y), line, font=font_title, fill=theme["text_color"])
            text_y += (bbox[3] - bbox[1]) + 18

        # ── Divider line ──
        text_y += 20
        draw.line(
            [(padding + 80, text_y), (CARD_WIDTH - padding - 80, text_y)],
            fill=theme["accent_color"],
            width=2,
        )
        text_y += 30

        # ── Caption ──
        if caption:
            caption_lines = split_into_lines_by_pixel_width(caption, font_caption, usable_width)
            for line in caption_lines:
                bbox = draw.textbbox((0, 0), line, font=font_caption)
                text_w = bbox[2] - bbox[0]
                x = (CARD_WIDTH - text_w) // 2
                draw.text((x, text_y), line, font=font_caption, fill=theme["subtitle_color"])
                text_y += (bbox[3] - bbox[1]) + 12
            text_y += 10

        # ── Hashtags ──
        if hashtags:
            tag_str = clean_hashtags(hashtags)
            bbox = draw.textbbox((0, 0), tag_str, font=font_hashtag)
            tag_w = bbox[2] - bbox[0]
            x = (CARD_WIDTH - tag_w) // 2
            draw.text((x, CARD_HEIGHT - 160), tag_str, font=font_hashtag, fill=theme["accent_color"])

        # ── Watermark / Brand name ──
        watermark = theme.get("watermark", brand_name)
        wm_bbox = draw.textbbox((0, 0), watermark, font=font_watermark)
        wm_w = wm_bbox[2] - wm_bbox[0]
        draw.text(
            ((CARD_WIDTH - wm_w) // 2, CARD_HEIGHT - 90),
            watermark,
            font=font_watermark,
            fill=theme["accent_color"],
        )

        # ── Bottom accent bar ──
        draw.rectangle(
            [(padding, CARD_HEIGHT - 70), (CARD_WIDTH - padding, CARD_HEIGHT - 64)],
            fill=theme["accent_color"],
        )

        # ── Save ──
        filename = f"{content_type}_{uuid.uuid4().hex[:10]}_{datetime.now():%Y%m%d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        img.save(filepath, "PNG", quality=95)
        logger.info(f"Quote card saved: {filepath}")
        return filepath

    def _create_background(self, theme: dict) -> Image.Image:
        """
        Creates a rich gradient-like background using the theme colors.
        """
        img = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), theme["bg_color"])

        # Subtle texture: overlay semi-transparent rectangles
        overlay = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Corner accents
        r, g, b = theme["accent_color"]
        draw.rectangle([(0, 0), (200, 200)], fill=(r, g, b, 20))
        draw.rectangle(
            [(CARD_WIDTH - 200, CARD_HEIGHT - 200), (CARD_WIDTH, CARD_HEIGHT)],
            fill=(r, g, b, 20),
        )

        # Blend overlay onto base
        base = img.convert("RGBA")
        combined = Image.alpha_composite(base, overlay)
        return combined.convert("RGB")
