"""
News fetcher module - fetches news articles from various sources
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from newsapi import NewsApiClient
import attrs

@attrs.define
class NewsArticle:
    title: str
    description: str
    url: str
    published_at: str
    source: str
    def __repr__(self):
        return f"NewsArticle(title='{self.title[:50]}...', source='{self.source}')"


@attrs.define
class NewsFetcher:
    """Fetches news from multiple sources"""
    config: Dict


    def __init__(self, config: Dict):
        self.config = config
        self.newsapi_key = os.getenv('NEWSAPI_KEY')

        # Initialize NewsAPI client if key is available
        self.newsapi_client = None
        if self.newsapi_key:
            self.newsapi_client = NewsApiClient(api_key=self.newsapi_key)

    def fetch_company_news(self, company: Dict, lookback_hours: int = 24) -> List[NewsArticle]:
        """Fetch news for a specific company"""
        articles = []

        # Fetch from NewsAPI if enabled and client is available
        if (self.config.get('news_sources', {}).get('newsapi', {}).get('enabled', False)
            and self.newsapi_client):
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
        """Fetch news from NewsAPI.org using the official newsapi-python client"""
        articles = []

        try:
            # Build search query from company keywords
            keywords = company.get('keywords', [company['name']])
            query = ' OR '.join(f'"{keyword}"' for keyword in keywords)

            # Calculate date range
            from_date = (datetime.now() - timedelta(hours=lookback_hours)).strftime('%Y-%m-%d')

            # Get configuration options
            language = self.config['news_sources']['newsapi'].get('language', 'en')
            sort_by = self.config['news_sources']['newsapi'].get('sort_by', 'publishedAt')

            # Fetch articles using NewsAPI client
            response = self.newsapi_client.get_everything(
                q=query,
                from_param=from_date,
                language=language,
                sort_by=sort_by
            )

            # Process articles from response
            if response.get('status') == 'ok':
                for article in response.get('articles', []):
                    if article.get('title') and article.get('title') != '[Removed]':
                        articles.append(NewsArticle(
                            title=article.get('title', ''),
                            description=article.get('description', ''),
                            url=article.get('url', ''),
                            published_at=article.get('publishedAt', ''),
                            source=article.get('source', {}).get('name', 'NewsAPI')
                        ))
            else:
                print(f"Warning: NewsAPI returned status '{response.get('status')}' for {company['name']}")

        except Exception as e:
            print(f"Warning: Failed to fetch from NewsAPI for {company['name']}: {e}")

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
