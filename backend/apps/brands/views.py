"""
Brands Module — API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Brand, PostLog
from .serializers import BrandSerializer, PostLogSerializer


class BrandListView(APIView):
    def get(self, request):
        brands = Brand.objects.filter(is_active=True)
        serializer = BrandSerializer(brands, many=True)
        return Response(serializer.data)


class BrandDetailView(APIView):
    def get(self, request, slug):
        try:
            brand = Brand.objects.get(slug=slug)
        except Brand.DoesNotExist:
            return Response({"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = BrandSerializer(brand)
        return Response(serializer.data)


class BrandPostLogsView(APIView):
    def get(self, request, slug):
        try:
            brand = Brand.objects.get(slug=slug)
        except Brand.DoesNotExist:
            return Response({"error": "Brand not found"}, status=status.HTTP_404_NOT_FOUND)
        logs = PostLog.objects.filter(brand=brand).order_by("-created_at")[:50]
        serializer = PostLogSerializer(logs, many=True)
        return Response(serializer.data)
