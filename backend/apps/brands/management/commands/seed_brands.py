"""
Management Command: seed_brands
Creates the default EduImpact brands with their posting windows.

Usage:
    python manage.py seed_brands
"""
from django.core.management.base import BaseCommand
from apps.brands.models import Brand
from apps.calendar.models import PostingWindow


DEFAULT_BRANDS = [
    {
        "name": "EduImpactHub",
        "slug": "eduimpacthub",
        "description": "Educational content covering math tips, science, and everyday learning.",
        "tone": Brand.Tone.EDUCATIONAL,
        "content_type": Brand.ContentType.EDUCATION,
        "hashtags": "#EduImpact,#LearnEveryDay,#Education,#Growth,#Knowledge",
        "posts_per_day": 3,
        "post_to_facebook": True,
        "post_to_x": True,
        "windows": [
            (0, 8), (0, 12), (0, 18),   # Mon
            (1, 8), (1, 12), (1, 18),   # Tue
            (2, 8), (2, 12), (2, 18),   # Wed
            (3, 8), (3, 12), (3, 18),   # Thu
            (4, 8), (4, 12), (4, 18),   # Fri
            (5, 9), (5, 15),             # Sat
            (6, 10),                     # Sun
        ],
    },
    {
        "name": "Faith Devotional",
        "slug": "devotional",
        "description": "Daily faith-based devotionals and scripture-inspired messages.",
        "tone": Brand.Tone.DEVOTIONAL,
        "content_type": Brand.ContentType.DEVOTIONAL,
        "custom_voice_prompt": "Keep messages uplifting and Christocentric, grounded in scripture, and appropriate for all ages.",
        "hashtags": "#DailyDevotion,#Faith,#God,#Prayer,#Blessed",
        "posts_per_day": 2,
        "post_to_facebook": True,
        "post_to_x": True,
        "windows": [
            (0, 7), (0, 19),
            (1, 7), (1, 19),
            (2, 7), (2, 19),
            (3, 7), (3, 19),
            (4, 7), (4, 19),
            (5, 7), (5, 19),
            (6, 7), (6, 19),
        ],
    },
    {
        "name": "Coding Corner",
        "slug": "coding",
        "description": "Programming tips, code snippets, and developer wisdom.",
        "tone": Brand.Tone.EDUCATIONAL,
        "content_type": Brand.ContentType.PROGRAMMING,
        "custom_voice_prompt": "Be practical and include code examples where helpful. Target beginner to intermediate developers.",
        "hashtags": "#Python,#Coding,#Programming,#DevTips,#100DaysOfCode",
        "posts_per_day": 3,
        "post_to_facebook": True,
        "post_to_x": True,
        "windows": [
            (0, 9), (0, 15), (0, 20),
            (1, 9), (1, 15), (1, 20),
            (2, 9), (2, 15), (2, 20),
            (3, 9), (3, 15), (3, 20),
            (4, 9), (4, 15), (4, 20),
            (5, 10), (5, 16),
            (6, 11),
        ],
    },
    {
        "name": "Forex Insights",
        "slug": "forex",
        "description": "Forex trading tips, market insights, and financial education.",
        "tone": Brand.Tone.PROFESSIONAL,
        "content_type": Brand.ContentType.FOREX,
        "custom_voice_prompt": "Focus on education, excellent financial attitude and risk management. NEVER give specific buy/sell signals or financial advice.",
        "hashtags": "#Forex,#Trading,#FX,#FinanceTips,#TraderMindset",
        "posts_per_day": 2,
        "post_to_facebook": True,
        "post_to_x": True,
        "windows": [
            (0, 8), (0, 17),
            (1, 8), (1, 17),
            (2, 8), (2, 17),
            (3, 8), (3, 17),
            (4, 8), (4, 17),
            (5, 9),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed default EduImpact brands and their posting windows."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Seeding EduImpact brands..."))
        created_count = 0

        for brand_data in DEFAULT_BRANDS:
            windows = brand_data.pop("windows", [])
            brand, created = Brand.objects.get_or_create(
                slug=brand_data["slug"],
                defaults=brand_data,
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"  ✅ Created brand: {brand.name}"))
                created_count += 1
            else:
                self.stdout.write(f"  ⏭  Brand already exists: {brand.name}")

            # Create posting windows
            window_count = 0
            for day, hour in windows:
                _, win_created = PostingWindow.objects.get_or_create(
                    brand=brand,
                    day_of_week=day,
                    post_hour=hour,
                    defaults={"post_minute": 0, "is_active": True},
                )
                if win_created:
                    window_count += 1

            if window_count:
                self.stdout.write(f"     📅 Created {window_count} posting windows for {brand.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n✅ Done! Created {created_count}/{len(DEFAULT_BRANDS)} brands."
            )
        )
