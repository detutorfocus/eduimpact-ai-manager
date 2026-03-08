from rest_framework.views import APIView
from rest_framework.response import Response
from .models import PostAnalytics, BrandAnalyticsSummary


class AnalyticsSummaryView(APIView):
    def get(self, request):
        summaries = BrandAnalyticsSummary.objects.select_related("brand").order_by("-date")[:30]
        data = [
            {
                "brand": s.brand.slug,
                "date": s.date,
                "platform": s.platform,
                "total_posts": s.total_posts,
                "total_likes": s.total_likes,
                "total_shares": s.total_shares,
                "total_reach": s.total_reach,
                "avg_engagement_rate": s.avg_engagement_rate,
            }
            for s in summaries
        ]
        return Response(data)


class PostAnalyticsListView(APIView):
    def get(self, request):
        brand_slug = request.query_params.get("brand")
        qs = PostAnalytics.objects.select_related("brand").order_by("-snapshot_at")[:50]
        if brand_slug:
            qs = qs.filter(brand__slug=brand_slug)
        data = [
            {
                "brand": a.brand.slug,
                "platform": a.platform,
                "likes": a.likes,
                "shares": a.shares,
                "comments": a.comments,
                "reach": a.reach,
                "engagement_rate": a.engagement_rate,
                "snapshot_at": a.snapshot_at,
            }
            for a in qs
        ]
        return Response(data)
