"""
News fetcher module - fetches news articles from various sources
"""
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from urllib.parse import quote


class NewsArticle:
    """Represents a news article"""
    def __init__(self, title: str, description: str, url: str,
                 published_at: str, source: str):
        self.title = title
        self.description = description
        self.url = url
        self.published_at = published_at
        self.source = source

    def __repr__(self):
        return f"NewsArticle(title='{self.title[:50]}...', source='{self.source}')"


class NewsFetcher:
    """Fetches news from multiple sources"""

    def __init__(self, config: Dict):
        self.config = config
        self.newsapi_key = os.getenv('NEWSAPI_KEY')

    def fetch_company_news(self, company: Dict, lookback_hours: int = 24) -> List[NewsArticle]:
        """Fetch news for a specific company"""
        articles = []

        # Fetch from NewsAPI if enabled and key is available
        if (self.config.get('news_sources', {}).get('newsapi', {}).get('enabled', False)
            and self.newsapi_key):
            articles.extend(self._fetch_from_newsapi(company, lookback_hours))

        # RSS feeds disabled (requires additional dependencies)
        # if self.config.get('news_sources', {}).get('rss_feeds', {}).get('enabled', False):
        #     articles.extend(self._fetch_from_rss(company, lookback_hours))

        # Remove duplicates based on title similarity
        articles = self._deduplicate_articles(articles)

        # Sort by published date (most recent first)
        articles.sort(key=lambda x: x.published_at, reverse=True)

        # Limit number of articles
        max_articles = self.config.get('report', {}).get('max_articles_per_company', 10)
        return articles[:max_articles]

    def _fetch_from_newsapi(self, company: Dict, lookback_hours: int) -> List[NewsArticle]:
        """Fetch news from NewsAPI.org"""
        articles = []

        try:
            # Build search query from company keywords
            keywords = company.get('keywords', [company['name']])
            query = ' OR '.join(f'"{keyword}"' for keyword in keywords)

            # Calculate date range
            from_date = (datetime.now() - timedelta(hours=lookback_hours)).isoformat()

            # Make API request
            url = 'https://newsapi.org/v2/everything'
            params = {
                'q': query,
                'from': from_date,
                'language': self.config['news_sources']['newsapi'].get('language', 'en'),
                'sortBy': self.config['news_sources']['newsapi'].get('sort_by', 'publishedAt'),
                'apiKey': self.newsapi_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            for article in data.get('articles', []):
                if article.get('title') and article.get('title') != '[Removed]':
                    articles.append(NewsArticle(
                        title=article.get('title', ''),
                        description=article.get('description', ''),
                        url=article.get('url', ''),
                        published_at=article.get('publishedAt', ''),
                        source=article.get('source', {}).get('name', 'NewsAPI')
                    ))

        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to fetch from NewsAPI for {company['name']}: {e}")
        except Exception as e:
            print(f"Warning: Error processing NewsAPI results for {company['name']}: {e}")

        return articles

    def _fetch_from_rss(self, company: Dict, lookback_hours: int) -> List[NewsArticle]:
        """Fetch news from RSS feeds (currently disabled - requires feedparser)"""
        # RSS feed functionality disabled to reduce dependencies
        # To enable: install feedparser and uncomment this code
        return []

    def _deduplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on title similarity"""
        seen_titles = set()
        unique_articles = []

        for article in articles:
            # Normalize title for comparison
            normalized_title = article.title.lower().strip()

            if normalized_title not in seen_titles:
                seen_titles.add(normalized_title)
                unique_articles.append(article)

        return unique_articles
