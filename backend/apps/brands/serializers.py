from rest_framework import serializers
from .models import Brand, PostLog


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            "id", "name", "slug", "description", "tone", "content_type",
            "hashtags", "posts_per_day", "post_to_facebook", "post_to_x", "is_active",
        ]


class PostLogSerializer(serializers.ModelSerializer):
    brand_name = serializers.CharField(source="brand.name", read_only=True)

    class Meta:
        model = PostLog
        fields = [
            "id", "brand_name", "platform", "status", "post_text",
            "caption", "hashtags_used", "image_path", "platform_post_id",
            "error_message", "retry_count", "scheduled_at", "published_at", "created_at",
        ]
