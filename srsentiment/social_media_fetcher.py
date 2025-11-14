"""
Social media fetcher module - fetches posts from social media platforms
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import attrs

from .config import Config, Company


@attrs.define
class SocialMediaPost:
    """Represents a social media post"""
    title: str
    content: str
    url: str
    published_at: str
    source: str
    platform: str  # reddit, twitter, etc.
    score: int = 0  # upvotes, likes, etc.

    def __repr__(self):
        return f"SocialMediaPost(title='{self.title[:50]}...', platform='{self.platform}', source='{self.source}')"


@attrs.define
class SocialMediaFetcher:
    """Fetches posts from social media platforms"""
    config: Config

    def fetch_company_posts(self, company: "Company", lookback_hours: int = 24) -> List[SocialMediaPost]:
        """Fetch social media posts for a specific company"""
        posts = []

        # Fetch from Reddit if enabled
        if self.config.social_media_sources.reddit.enabled:
            posts.extend(self._fetch_from_reddit(company, lookback_hours))

        # Sort by published date (most recent first) and score
        posts.sort(key=lambda x: (x.published_at, x.score), reverse=True)

        # Limit number of posts
        max_posts = self.config.report.max_articles_per_company
        return posts[:max_posts]

    def _fetch_from_reddit(self, company: "Company", lookback_hours: int) -> List[SocialMediaPost]:
        """Fetch posts from Reddit using the public API"""
        posts = []

        try:
            # Build search query from company keywords
            keywords = company.keywords if company.keywords else [company.name]

            # Get subreddits to search
            subreddits = self.config.social_media_sources.reddit.subreddits

            # Calculate timestamp threshold
            time_threshold = datetime.now() - timedelta(hours=lookback_hours)

            for subreddit in subreddits:
                for keyword in keywords:
                    try:
                        # Search Reddit using public API
                        # Note: Reddit's public API doesn't require authentication for basic searches
                        url = f"https://www.reddit.com/r/{subreddit}/search.json"
                        params = {
                            'q': keyword,
                            'sort': 'new',
                            'limit': 25,
                            'restrict_sr': 'on',
                            't': 'day' if lookback_hours <= 24 else 'week'
                        }
                        headers = {'User-Agent': 'News Sentiment Bot/1.0'}

                        response = requests.get(url, params=params, headers=headers, timeout=10)
                        response.raise_for_status()

                        data = response.json()

                        # Process posts
                        if 'data' in data and 'children' in data['data']:
                            for item in data['data']['children']:
                                post_data = item['data']

                                # Check if post is within time range
                                post_time = datetime.fromtimestamp(post_data['created_utc'])
                                if post_time < time_threshold:
                                    continue

                                # Skip removed/deleted posts
                                if post_data.get('removed_by_category') or post_data.get('selftext') == '[removed]':
                                    continue

                                posts.append(SocialMediaPost(
                                    title=post_data.get('title', ''),
                                    content=post_data.get('selftext', '')[:500],  # Limit content length
                                    url=f"https://www.reddit.com{post_data.get('permalink', '')}",
                                    published_at=post_time.isoformat(),
                                    source=f"r/{subreddit}",
                                    platform='reddit',
                                    score=post_data.get('score', 0)
                                ))

                    except Exception as e:
                        print(f"Warning: Failed to fetch from r/{subreddit} for '{keyword}': {e}")
                        continue

        except Exception as e:
            print(f"Warning: Failed to fetch Reddit posts for {company.name}: {e}")

        return posts
