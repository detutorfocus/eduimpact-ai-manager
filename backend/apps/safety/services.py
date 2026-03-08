"""
Safety Module — Services
Validates generated content before it is published.
Checks for banned words, spam, duplicates, API limits, and more.
"""
import re
import logging
import hashlib
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from apps.brands.models import Brand, PostLog

logger = logging.getLogger(__name__)


class SafetyCheckResult:
    """Structured result from a safety check."""

    def __init__(self, passed: bool, reason: str = "", severity: str = "info"):
        self.passed = passed
        self.reason = reason
        self.severity = severity  # info | warning | blocked

    def __bool__(self):
        return self.passed

    def __str__(self):
        status = "✅ PASSED" if self.passed else f"🚫 BLOCKED ({self.severity})"
        return f"{status}: {self.reason}"


class SafetyService:
    """
    Multi-layer content safety and moderation checks.
    """

    def __init__(self):
        self.banned_words = [
            w.strip().lower()
            for w in getattr(settings, "SAFETY_BANNED_WORDS", [])
        ]
        self.duplicate_window_hours = getattr(
            settings, "MAX_DUPLICATE_WINDOW_HOURS", 24
        )

    # ── Master check ──────────────────────────────────────────────────────────

    def check_content(self, post_text: str, brand: Brand) -> SafetyCheckResult:
        """
        Run all safety checks on the generated content.
        Returns a SafetyCheckResult; if passed=False, the post should be blocked.
        """
        checks = [
            self._check_empty_content(post_text),
            self._check_banned_words(post_text),
            self._check_spam_patterns(post_text),
            self._check_excessive_length(post_text),
            self._check_duplicate(post_text, brand),
            self._check_daily_limit(brand),
        ]

        for result in checks:
            if not result.passed:
                logger.warning(
                    f"[Safety] Post BLOCKED for '{brand.slug}': {result.reason}"
                )
                return result

        logger.info(f"[Safety] All checks PASSED for '{brand.slug}'")
        return SafetyCheckResult(passed=True, reason="All checks passed")

    # ── Individual Checks ─────────────────────────────────────────────────────

    def _check_empty_content(self, text: str) -> SafetyCheckResult:
        """Block empty or too-short posts."""
        cleaned = text.strip()
        if not cleaned:
            return SafetyCheckResult(
                passed=False, reason="Post text is empty", severity="blocked"
            )
        if len(cleaned) < 20:
            return SafetyCheckResult(
                passed=False,
                reason=f"Post too short ({len(cleaned)} chars). Minimum: 20.",
                severity="blocked",
            )
        return SafetyCheckResult(passed=True)

    def _check_banned_words(self, text: str) -> SafetyCheckResult:
        """Block posts containing banned words."""
        text_lower = text.lower()
        for word in self.banned_words:
            if word and re.search(r'\b' + re.escape(word) + r'\b', text_lower):
                return SafetyCheckResult(
                    passed=False,
                    reason=f"Contains restricted keyword: '{word}'",
                    severity="blocked",
                )
        return SafetyCheckResult(passed=True)

    def _check_spam_patterns(self, text: str) -> SafetyCheckResult:
        """Detect common spam patterns."""
        spam_patterns = [
            (r'(.)\1{8,}', "Excessive character repetition"),
            (r'([A-Z]{20,})', "Excessive ALL CAPS text"),
            (r'(!!!){3,}', "Excessive exclamation marks"),
            (r'https?://\S+\s+https?://\S+\s+https?://\S+', "Too many URLs"),
            (r'(\$\$\$|\€\€\€|💰💰💰)', "Spam financial symbols"),
        ]
        for pattern, description in spam_patterns:
            if re.search(pattern, text):
                return SafetyCheckResult(
                    passed=False,
                    reason=f"Spam pattern detected: {description}",
                    severity="warning",
                )
        return SafetyCheckResult(passed=True)

    def _check_excessive_length(self, text: str) -> SafetyCheckResult:
        """Warn if the post text is unreasonably long."""
        MAX_CHARS = 2000
        if len(text) > MAX_CHARS:
            return SafetyCheckResult(
                passed=False,
                reason=f"Post too long ({len(text)} chars). Maximum: {MAX_CHARS}.",
                severity="warning",
            )
        return SafetyCheckResult(passed=True)

    def _check_duplicate(self, text: str, brand: Brand) -> SafetyCheckResult:
        """
        Prevent posting the exact same content twice within the duplicate window.
        Uses MD5 hash comparison for efficiency.
        """
        content_hash = hashlib.md5(text.strip().lower().encode()).hexdigest()
        cutoff = timezone.now() - timedelta(hours=self.duplicate_window_hours)

        # Check recent posts for the same brand
        recent_posts = PostLog.objects.filter(
            brand=brand,
            created_at__gte=cutoff,
            status=PostLog.Status.PUBLISHED,
        ).values_list("post_text", flat=True)

        for recent_text in recent_posts:
            recent_hash = hashlib.md5(
                recent_text.strip().lower().encode()
            ).hexdigest()
            if content_hash == recent_hash:
                return SafetyCheckResult(
                    passed=False,
                    reason=f"Duplicate content detected within the last {self.duplicate_window_hours}h",
                    severity="blocked",
                )

        return SafetyCheckResult(passed=True)

    def _check_daily_limit(self, brand: Brand) -> SafetyCheckResult:
        """Enforce daily posting limit per brand."""
        daily_limit = settings.DAILY_POST_LIMIT
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

        today_count = PostLog.objects.filter(
            brand=brand,
            status=PostLog.Status.PUBLISHED,
            published_at__gte=today_start,
        ).count()

        if today_count >= daily_limit:
            return SafetyCheckResult(
                passed=False,
                reason=f"Daily post limit reached ({today_count}/{daily_limit}) for brand '{brand.slug}'",
                severity="warning",
            )
        return SafetyCheckResult(passed=True)

    def validate_image(self, image_path: str) -> SafetyCheckResult:
        """Basic validation that the image file exists and is a valid image."""
        import os
        if not image_path:
            return SafetyCheckResult(
                passed=False, reason="No image path provided", severity="warning"
            )
        if not os.path.exists(image_path):
            return SafetyCheckResult(
                passed=False,
                reason=f"Image file not found: {image_path}",
                severity="warning",
            )
        # Check file size (max 8MB for Facebook)
        size_mb = os.path.getsize(image_path) / (1024 * 1024)
        if size_mb > 8:
            return SafetyCheckResult(
                passed=False,
                reason=f"Image too large: {size_mb:.1f}MB (max 8MB)",
                severity="warning",
            )
        return SafetyCheckResult(passed=True)
