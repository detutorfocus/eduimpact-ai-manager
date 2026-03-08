"""
Publisher Module — Facebook Publisher
Handles posting text and image content to Facebook Pages via Graph API.
"""
import logging
import requests
from django.conf import settings
from apps.brands.models import Brand

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v18.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


class FacebookPublisher:
    """
    Posts content to a Facebook Page using the Graph API.
    Supports text-only and photo posts.
    """

    def __init__(self, brand: Brand):
        """
        Initialize with brand-specific credentials.
        Falls back to global settings if brand credentials are empty.
        """
        self.page_id = brand.facebook_page_id or settings.FACEBOOK_PAGE_ID
        self.access_token = brand.facebook_access_token or settings.FACEBOOK_ACCESS_TOKEN
        self.brand = brand

        if not self.page_id or not self.access_token:
            raise ValueError(
                f"Facebook credentials not configured for brand: {brand.slug}"
            )

    def post_text(self, message: str) -> dict:
        """
        Publish a text-only post to the Facebook Page.

        Returns:
            dict with 'post_id' on success, 'error' on failure.
        """
        url = f"{GRAPH_API_BASE}/{self.page_id}/feed"
        payload = {
            "message": message,
            "access_token": self.access_token,
        }

        try:
            response = requests.post(url, data=payload, timeout=30)
            data = response.json()

            if response.status_code == 200 and "id" in data:
                post_id = data["id"]
                logger.info(f"[Facebook] Text post published for '{self.brand.slug}': {post_id}")
                return {"success": True, "post_id": post_id}
            else:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                logger.error(f"[Facebook] Post failed for '{self.brand.slug}': {error_msg}")
                return {"success": False, "error": error_msg}

        except requests.exceptions.RequestException as e:
            logger.error(f"[Facebook] Network error for '{self.brand.slug}': {e}")
            return {"success": False, "error": str(e)}

    def post_with_image(self, message: str, image_path: str) -> dict:
        """
        Publish a photo post with caption to the Facebook Page.

        Args:
            message: The post caption/message
            image_path: Absolute path to the image file

        Returns:
            dict with 'post_id' on success, 'error' on failure.
        """
        url = f"{GRAPH_API_BASE}/{self.page_id}/photos"

        try:
            with open(image_path, "rb") as img_file:
                payload = {
                    "caption": message,
                    "access_token": self.access_token,
                }
                files = {"source": img_file}
                response = requests.post(url, data=payload, files=files, timeout=60)

            data = response.json()

            if response.status_code == 200 and "id" in data:
                post_id = data["id"]
                logger.info(
                    f"[Facebook] Photo post published for '{self.brand.slug}': {post_id}"
                )
                return {"success": True, "post_id": post_id}
            else:
                error_msg = data.get("error", {}).get("message", "Unknown error")
                logger.error(
                    f"[Facebook] Photo post failed for '{self.brand.slug}': {error_msg}"
                )
                return {"success": False, "error": error_msg}

        except FileNotFoundError:
            logger.error(f"[Facebook] Image file not found: {image_path}")
            return {"success": False, "error": f"Image not found: {image_path}"}
        except requests.exceptions.RequestException as e:
            logger.error(f"[Facebook] Network error for '{self.brand.slug}': {e}")
            return {"success": False, "error": str(e)}

    def verify_credentials(self) -> bool:
        """Test if the page credentials are valid."""
        url = f"{GRAPH_API_BASE}/{self.page_id}"
        params = {
            "fields": "name,id",
            "access_token": self.access_token,
        }
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            if "id" in data:
                logger.info(f"[Facebook] Credentials valid for page: {data.get('name')}")
                return True
            logger.warning(f"[Facebook] Invalid credentials: {data}")
            return False
        except Exception as e:
            logger.error(f"[Facebook] Credential check failed: {e}")
            return False
