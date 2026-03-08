"""
News Module — Services
Fetches trending news and educational content for AI-powered post generation.
"""
import logging
import requests
import feedparser
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import NewsItem

logger = logging.getLogger(__name__)

# News categories mapped to RSS feeds and API topics
NEWS_SOURCES = {
    "education": [
        "https://feeds.feedburner.com/educationweek/news",
        "https://www.edsurge.com/news.rss",
    ],
    "programming": [
        "https://feeds.feedburner.com/PythonInsider",
        "https://dev.to/feed",
        "https://www.infoq.com/feed/",
    ],
    "ai_tech": [
        "https://techcrunch.com/feed/",
        "https://feeds.feedburner.com/venturebeat/SZYF",
    ],
    "forex": [
        "https://www.forexlive.com/feed/news",
        "https://www.dailyfx.com/feeds/all",
    ],
}

NEWSAPI_ENDPOINT = "https://newsapi.org/v2/top-headlines"
NEWSAPI_EVERYTHING = "https://newsapi.org/v2/everything"


class NewsService:
    """
    Fetches news from multiple sources: NewsAPI.org and RSS feeds.
    """

    def fetch_from_newsapi(
        self, topic: str, max_results: int = 10
    ) -> list:
        """
        Fetch articles from NewsAPI.org for a given topic.
        """
        if not settings.NEWS_API_KEY:
            logger.warning("NEWS_API_KEY not configured. Skipping NewsAPI fetch.")
            return []

        params = {
            "q": topic,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": max_results,
            "apiKey": settings.NEWS_API_KEY,
        }

        try:
            response = requests.get(NEWSAPI_EVERYTHING, params=params, timeout=15)
            data = response.json()

            if data.get("status") != "ok":
                logger.warning(f"NewsAPI error: {data.get('message', 'unknown')}")
                return []

            articles = []
            for article in data.get("articles", []):
                if article.get("title") and article.get("description"):
                    articles.append({
                        "title": article["title"],
                        "description": article.get("description", ""),
                        "url": article.get("url", ""),
                        "source": article.get("source", {}).get("name", "NewsAPI"),
                        "published_at": article.get("publishedAt", ""),
                        "category": topic,
                    })
            logger.info(f"NewsAPI: fetched {len(articles)} articles for '{topic}'")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"NewsAPI request failed: {e}")
            return []

    def fetch_from_rss(self, category: str) -> list:
        """
        Fetch articles from RSS feeds for a category.
        """
        feed_urls = NEWS_SOURCES.get(category, [])
        articles = []

        for url in feed_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    articles.append({
                        "title": entry.get("title", ""),
                        "description": entry.get("summary", entry.get("description", ""))[:500],
                        "url": entry.get("link", ""),
                        "source": feed.feed.get("title", url),
                        "published_at": entry.get("published", ""),
                        "category": category,
                    })
                logger.info(f"RSS: fetched {len(feed.entries[:5])} from {url}")
            except Exception as e:
                logger.warning(f"RSS fetch failed for {url}: {e}")

        return articles

    def fetch_all(self) -> dict:
        """
        Fetch news for all categories and store in database.
        Returns summary dict.
        """
        summary = {}
        topics = {
            "education": ["education technology", "learning"],
            "programming": ["python programming", "software development"],
            "ai_tech": ["artificial intelligence", "tech news"],
            "forex": ["forex trading", "currency markets"],
        }

        for category, search_terms in topics.items():
            count = 0
            for term in search_terms:
                articles = self.fetch_from_newsapi(term, max_results=5)
                for article in articles:
                    article["category"] = category
                    saved = self._save_article(article)
                    if saved:
                        count += 1

            # Also try RSS
            rss_articles = self.fetch_from_rss(category)
            for article in rss_articles:
                saved = self._save_article(article)
                if saved:
                    count += 1

            summary[category] = count

        logger.info(f"News fetch complete: {summary}")
        return summary

    def _save_article(self, article: dict) -> bool:
        """Save an article to the database if not duplicate."""
        url = article.get("url", "")
        if not url or NewsItem.objects.filter(url=url).exists():
            return False

        NewsItem.objects.create(
            title=article["title"][:500],
            description=article.get("description", "")[:2000],
            url=url,
            source=article.get("source", "")[:200],
            category=article.get("category", "general"),
        )
        return True

    def get_topics_for_brand(
        self, content_type: str, count: int = 3
    ) -> list:
        """
        Get recent news topics relevant to a brand's content type.
        Returns list of topic strings for the AI generator.
        """
        category_map = {
            "education": "education",
            "programming": "programming",
            "forex": "forex",
            "ai_tech": "ai_tech",
        }
        db_category = category_map.get(content_type, "education")

        cutoff = timezone.now() - timedelta(days=2)
        items = NewsItem.objects.filter(
            category=db_category,
            is_used=False,
            created_at__gte=cutoff,
        ).order_by("?")[:count]  # random selection

        topics = []
        for item in items:
            # Build a topic hint from title + snippet
            topic = f"{item.title}. {item.description[:150]}"
            topics.append(topic)
            item.is_used = True
            item.save(update_fields=["is_used"])

        return topics
