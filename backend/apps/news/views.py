from rest_framework.views import APIView
from rest_framework.response import Response
from .models import NewsItem
from .tasks import fetch_and_store_news


class NewsListView(APIView):
    def get(self, request):
        category = request.query_params.get("category", None)
        qs = NewsItem.objects.filter(is_used=False).order_by("-created_at")[:30]
        if category:
            qs = qs.filter(category=category)
        data = [
            {"id": n.id, "title": n.title, "category": n.category, "source": n.source}
            for n in qs
        ]
        return Response(data)


class TriggerFetchView(APIView):
    def post(self, request):
        task = fetch_and_store_news.delay()
        return Response({"task_id": task.id, "status": "queued"})
