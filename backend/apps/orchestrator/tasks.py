"""
Orchestrator Module — Celery Tasks
The brain of EduImpact AI Manager v1.

Controls the full automated pipeline:
  1. Generate AI content
  2. Create quote card image
  3. Run safety checks
  4. Publish to platforms
  5. Log results
  6. Retry failures
"""
import logging
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from django.conf import settings

from apps.brands.models import Brand, PostLog
from apps.generator.services.ai_generator import AIGenerator
from apps.media.services.quote_card import QuoteCardGenerator
from apps.safety.services import SafetyService
from apps.publisher.facebook.services import FacebookPublisher
from apps.publisher.x.services import XPublisher

logger = logging.getLogger(__name__)


# ─── Main Pipeline ────────────────────────────────────────────────────────────

@shared_task(
    name="apps.orchestrator.tasks.run_full_pipeline",
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 min retry delay
)
def run_full_pipeline(self, brand_slug: str, content_type: str = None, topic: str = None):
    """
    Full automation pipeline for a single brand post.

    Steps:
      1. Load brand profile
      2. Generate AI content
      3. Create quote card image
      4. Safety check
      5. Publish to Facebook (if enabled)
      6. Publish to X (if enabled)
      7. Log all results

    Args:
        brand_slug: Brand identifier (e.g. 'eduimpacthub')
        content_type: Override content type (uses brand default if None)
        topic: Optional topic hint for the AI generator
    """
    logger.info(f"🚀 Pipeline START | brand={brand_slug} | type={content_type}")

    # ── Step 1: Load Brand ──────────────────────────────────────────────────
    try:
        brand = Brand.objects.get(slug=brand_slug, is_active=True)
    except Brand.DoesNotExist:
        logger.error(f"Brand not found or inactive: {brand_slug}")
        return {"error": f"Brand '{brand_slug}' not found"}

    effective_content_type = content_type or brand.content_type

    # ── Step 2: Generate AI Content ─────────────────────────────────────────
    try:
        logger.info(f"🤖 Generating content for '{brand.name}'...")
        generator = AIGenerator()
        content = generator.generate(
            brand_name=brand.name,
            content_type=effective_content_type,
            tone=brand.tone,
            topic=topic,
            custom_voice_prompt=brand.custom_voice_prompt,
            brand_hashtags=brand.get_hashtags_list(),
        )
        logger.info(f"✍ Content generated: {content.post_text[:80]}...")
    except Exception as exc:
        logger.error(f"AI generation failed for '{brand_slug}': {exc}")
        _log_failed_post(brand, "", str(exc), effective_content_type)
        raise self.retry(exc=exc)

    # ── Step 3: Create Quote Card ────────────────────────────────────────────
    image_path = ""
    try:
        logger.info(f"🖼 Creating quote card for '{brand.name}'...")
        card_gen = QuoteCardGenerator()
        image_path = card_gen.generate(
            post_text=content.post_text,
            brand_name=brand.name,
            caption=content.caption,
            hashtags=content.hashtags,
            content_type=effective_content_type,
        )
        logger.info(f"✅ Quote card created: {image_path}")
    except Exception as exc:
        logger.warning(f"Quote card creation failed for '{brand_slug}': {exc}. Continuing without image.")
        image_path = ""

    # ── Step 4: Safety Check ─────────────────────────────────────────────────
    safety_service = SafetyService()
    full_text = content.full_post()
    safety_result = safety_service.check_content(full_text, brand)

    if not safety_result.passed:
        logger.warning(f"🛡 Content BLOCKED for '{brand_slug}': {safety_result.reason}")
        _create_post_log(
            brand=brand,
            platform=PostLog.Platform.BOTH,
            status=PostLog.Status.BLOCKED,
            post_text=full_text,
            caption=content.caption,
            hashtags=" ".join(content.hashtags),
            image_path=image_path,
            error_message=safety_result.reason,
        )
        return {"status": "blocked", "reason": safety_result.reason}

    # ── Step 5 & 6: Publish to Platforms ─────────────────────────────────────
    results = {}

    if brand.post_to_facebook:
        fb_result = _publish_to_facebook(brand, full_text, image_path)
        results["facebook"] = fb_result

    if brand.post_to_x:
        x_result = _publish_to_x(brand, full_text, image_path)
        results["x"] = x_result

    # ── Step 7: Log Results ──────────────────────────────────────────────────
    for platform, result in results.items():
        platform_map = {"facebook": PostLog.Platform.FACEBOOK, "x": PostLog.Platform.X}
        status = PostLog.Status.PUBLISHED if result.get("success") else PostLog.Status.FAILED

        log = _create_post_log(
            brand=brand,
            platform=platform_map.get(platform, PostLog.Platform.BOTH),
            status=status,
            post_text=full_text,
            caption=content.caption,
            hashtags=" ".join(content.hashtags),
            image_path=image_path,
            platform_post_id=result.get("post_id", ""),
            error_message=result.get("error", ""),
        )

        if status == PostLog.Status.PUBLISHED:
            logger.info(
                f"✅ Published to {platform} for '{brand_slug}' | ID: {result.get('post_id')}"
            )
        else:
            logger.error(
                f"❌ Failed to publish to {platform} for '{brand_slug}': {result.get('error')}"
            )

    logger.info(f"🏁 Pipeline COMPLETE | brand={brand_slug} | results={results}")
    return {"status": "complete", "brand": brand_slug, "results": results}


# ─── Platform Publishing Helpers ─────────────────────────────────────────────

def _publish_to_facebook(brand: Brand, text: str, image_path: str) -> dict:
    """Publish to Facebook with or without image."""
    try:
        publisher = FacebookPublisher(brand)
        if image_path:
            return publisher.post_with_image(text, image_path)
        else:
            return publisher.post_text(text)
    except ValueError as e:
        logger.error(f"[Facebook] Config error for '{brand.slug}': {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"[Facebook] Unexpected error for '{brand.slug}': {e}")
        return {"success": False, "error": str(e)}


def _publish_to_x(brand: Brand, text: str, image_path: str) -> dict:
    """Publish to X (Twitter) with or without image."""
    try:
        publisher = XPublisher(brand)
        if image_path:
            return publisher.post_with_image(text, image_path)
        else:
            return publisher.post_text(text)
    except ValueError as e:
        logger.error(f"[X] Config error for '{brand.slug}': {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"[X] Unexpected error for '{brand.slug}': {e}")
        return {"success": False, "error": str(e)}


# ─── Logging Helpers ──────────────────────────────────────────────────────────

def _create_post_log(
    brand, platform, status, post_text, caption="",
    hashtags="", image_path="", platform_post_id="", error_message=""
) -> PostLog:
    return PostLog.objects.create(
        brand=brand,
        platform=platform,
        status=status,
        post_text=post_text,
        caption=caption,
        hashtags_used=hashtags,
        image_path=image_path,
        platform_post_id=platform_post_id,
        error_message=error_message,
        published_at=timezone.now() if status == PostLog.Status.PUBLISHED else None,
    )


def _log_failed_post(brand, text, error, content_type=""):
    return _create_post_log(
        brand=brand,
        platform=PostLog.Platform.BOTH,
        status=PostLog.Status.FAILED,
        post_text=text or f"[Generation failed - {content_type}]",
        error_message=error,
    )


# ─── Retry Failed Posts ───────────────────────────────────────────────────────

@shared_task(name="apps.orchestrator.tasks.retry_failed_posts", bind=True)
def retry_failed_posts(self):
    """
    Scan for failed posts and retry them (up to POST_RETRY_ATTEMPTS).
    Runs every 30 minutes via beat schedule.
    """
    max_retries = settings.POST_RETRY_ATTEMPTS
    failed_posts = PostLog.objects.filter(
        status=PostLog.Status.FAILED,
        retry_count__lt=max_retries,
    ).select_related("brand")

    count = 0
    for log in failed_posts:
        # Update retry count
        log.retry_count += 1
        log.status = PostLog.Status.RETRYING
        log.save(update_fields=["retry_count", "status"])

        # Dispatch a fresh pipeline run for this brand
        run_full_pipeline.delay(
            brand_slug=log.brand.slug,
            content_type=log.brand.content_type,
        )
        count += 1
        logger.info(f"🔄 Retrying post for '{log.brand.slug}' (attempt {log.retry_count})")

    if count:
        logger.info(f"Retry task: queued {count} posts for retry")
    return {"retried": count}


# ─── Bulk Run (run all brands now) ───────────────────────────────────────────

@shared_task(name="apps.orchestrator.tasks.run_all_brands")
def run_all_brands():
    """
    Trigger the full pipeline for ALL active brands immediately.
    Useful for manual testing or emergency runs.
    """
    brands = Brand.objects.filter(is_active=True)
    tasks_queued = []
    for brand in brands:
        task = run_full_pipeline.delay(
            brand_slug=brand.slug,
            content_type=brand.content_type,
        )
        tasks_queued.append({"brand": brand.slug, "task_id": str(task.id)})
        logger.info(f"Queued pipeline for brand: {brand.slug}")

    logger.info(f"run_all_brands: {len(tasks_queued)} pipelines queued")
    return tasks_queued
