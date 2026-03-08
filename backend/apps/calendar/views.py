from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ScheduledPost
from .services import CalendarService


class ScheduledPostListView(APIView):
    def get(self, request):
        posts = ScheduledPost.objects.filter(
            status=ScheduledPost.Status.QUEUED
        ).select_related("brand").order_by("scheduled_at")[:100]
        data = [
            {
                "id": p.id,
                "brand": p.brand.slug,
                "content_type": p.content_type,
                "scheduled_at": p.scheduled_at,
                "status": p.status,
            }
            for p in posts
        ]
        return Response(data)


class BuildScheduleView(APIView):
    def post(self, request):
        days = int(request.data.get("days_ahead", 7))
        service = CalendarService()
        results = service.build_schedule_all_brands(days_ahead=days)
        summary = {slug: len(slots) for slug, slots in results.items()}
        return Response({"created": summary})
