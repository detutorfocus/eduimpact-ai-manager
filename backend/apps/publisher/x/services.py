"""
Publisher Module — X (Twitter) Publisher
Posts text and image content to X using the Tweepy v2 API.
"""
import logging
import tweepy
from django.conf import settings
from apps.brands.models import Brand

logger = logging.getLogger(__name__)


class XPublisher:
    """
    Posts content to X (Twitter) using Tweepy OAuth1 v2 API.
    """

    def __init__(self, brand: Brand):
        """Initialize with brand-specific or global X credentials."""
        api_key = brand.x_api_key or settings.X_API_KEY
        api_secret = brand.x_api_secret or settings.X_API_SECRET
        access_token = brand.x_access_token or settings.X_ACCESS_TOKEN
        access_secret = brand.x_access_token_secret or settings.X_ACCESS_TOKEN_SECRET
        bearer_token = settings.X_BEARER_TOKEN

        if not all([api_key, api_secret, access_token, access_secret]):
            raise ValueError(
                f"X (Twitter) credentials not configured for brand: {brand.slug}"
            )

        self.brand = brand

        # v2 client for posting
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
            wait_on_rate_limit=True,
        )

        # v1.1 API for media upload (still required for images)
        auth = tweepy.OAuth1UserHandler(
            api_key, api_secret, access_token, access_secret
        )
        self.v1_api = tweepy.API(auth, wait_on_rate_limit=True)

    def post_text(self, text: str) -> dict:
        """
        Post a text tweet. X has a 280 character limit.

        Returns:
            dict with 'post_id' on success, 'error' on failure.
        """
        # Truncate to 280 characters
        if len(text) > 280:
            text = text[:277] + "..."

        try:
            response = self.client.create_tweet(text=text)
            tweet_id = str(response.data["id"])
            logger.info(f"[X] Tweet posted for '{self.brand.slug}': {tweet_id}")
            return {"success": True, "post_id": tweet_id}
        except tweepy.TweepyException as e:
            logger.error(f"[X] Tweet failed for '{self.brand.slug}': {e}")
            return {"success": False, "error": str(e)}

    def post_with_image(self, text: str, image_path: str) -> dict:
        """
        Upload image first via v1 API, then post tweet with media.

        Args:
            text: Tweet text
            image_path: Absolute path to image file

        Returns:
            dict with 'post_id' on success, 'error' on failure.
        """
        try:
            # Upload media via v1 API
            media = self.v1_api.media_upload(filename=image_path)
            media_id = str(media.media_id)
            logger.info(f"[X] Media uploaded: {media_id}")
        except (tweepy.TweepyException, FileNotFoundError) as e:
            logger.error(f"[X] Media upload failed for '{self.brand.slug}': {e}")
            return {"success": False, "error": f"Media upload failed: {e}"}

        # Truncate text
        if len(text) > 280:
            text = text[:277] + "..."

        try:
            response = self.client.create_tweet(text=text, media_ids=[media_id])
            tweet_id = str(response.data["id"])
            logger.info(f"[X] Tweet with image posted for '{self.brand.slug}': {tweet_id}")
            return {"success": True, "post_id": tweet_id}
        except tweepy.TweepyException as e:
            logger.error(f"[X] Tweet with image failed for '{self.brand.slug}': {e}")
            return {"success": False, "error": str(e)}

    def verify_credentials(self) -> bool:
        """Verify the X credentials are valid."""
        try:
            user = self.client.get_me()
            if user and user.data:
                logger.info(f"[X] Credentials valid for @{user.data.username}")
                return True
            return False
        except tweepy.TweepyException as e:
            logger.error(f"[X] Credential check failed: {e}")
            return False
