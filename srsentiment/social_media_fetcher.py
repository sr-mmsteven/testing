"""
Social media fetcher module - fetches posts and sentiment from social media platforms
"""
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, TYPE_CHECKING
import requests
import attrs

if TYPE_CHECKING:
    from .config import Config, Company


@attrs.define
class SocialPost:
    """Represents a social media post"""
    text: str
    author: str
    platform: str
    created_at: str
    url: str
    engagement: Dict = attrs.field(factory=dict)  # likes, shares, comments, etc.

    def __repr__(self):
        return f"SocialPost(platform='{self.platform}', author='{self.author}', text='{self.text[:50]}...')"


@attrs.define
class SocialMediaFetcher:
    """Fetches social media posts from various platforms"""
    config: "Config"
    reddit_client_id: str = attrs.field(init=False, default=attrs.Factory(lambda: os.getenv('REDDIT_CLIENT_ID', '')))
    reddit_client_secret: str = attrs.field(init=False, default=attrs.Factory(lambda: os.getenv('REDDIT_CLIENT_SECRET', '')))

    def fetch_company_posts(self, company: "Company", lookback_hours: int = 24) -> List[SocialPost]:
        """Fetch social media posts for a specific company"""
        posts = []

        # Fetch from Reddit if enabled
        if self.config.social_media.reddit.enabled:
            posts.extend(self._fetch_from_reddit(company, lookback_hours))

        # Sort by created date (most recent first)
        posts.sort(key=lambda x: x.created_at, reverse=True)

        # Limit number of posts
        max_posts = self.config.social_media.max_posts_per_company
        return posts[:max_posts]

    def _fetch_from_reddit(self, company: "Company", lookback_hours: int) -> List[SocialPost]:
        """Fetch posts from Reddit about the company"""
        posts = []

        try:
            # Build search query from company keywords
            keywords = company.keywords if company.keywords else [company.name]

            # Get subreddits to search
            subreddits = self.config.social_media.reddit.subreddits

            # Calculate time threshold
            time_threshold = datetime.now() - timedelta(hours=lookback_hours)

            # Search each subreddit
            for subreddit in subreddits:
                for keyword in keywords:
                    # Use Reddit JSON API (no authentication required for public data)
                    url = f"https://www.reddit.com/r/{subreddit}/search.json"
                    params = {
                        'q': keyword,
                        'restrict_sr': '1',
                        'sort': 'new',
                        'limit': 25,
                        't': 'day' if lookback_hours <= 24 else 'week'
                    }

                    headers = {
                        'User-Agent': 'NewsSentimentBot/1.0 (News Sentiment Analysis Tool)'
                    }

                    response = requests.get(url, params=params, headers=headers, timeout=10)

                    if response.status_code == 200:
                        data = response.json()

                        for post_data in data.get('data', {}).get('children', []):
                            post = post_data.get('data', {})

                            # Parse created time
                            created_utc = post.get('created_utc', 0)
                            created_time = datetime.fromtimestamp(created_utc)

                            # Check if within time range
                            if created_time < time_threshold:
                                continue

                            # Extract post data
                            title = post.get('title', '')
                            selftext = post.get('selftext', '')
                            text = f"{title}\n{selftext}" if selftext else title

                            # Skip removed or deleted posts
                            if '[removed]' in text.lower() or '[deleted]' in text.lower():
                                continue

                            posts.append(SocialPost(
                                text=text,
                                author=post.get('author', 'unknown'),
                                platform='Reddit',
                                created_at=created_time.isoformat(),
                                url=f"https://reddit.com{post.get('permalink', '')}",
                                engagement={
                                    'score': post.get('score', 0),
                                    'num_comments': post.get('num_comments', 0),
                                    'upvote_ratio': post.get('upvote_ratio', 0)
                                }
                            ))

        except requests.exceptions.RequestException as e:
            print(f"Warning: Failed to fetch from Reddit for {company.name}: {e}")
        except Exception as e:
            print(f"Warning: Error processing Reddit results for {company.name}: {e}")

        return posts

    def _fetch_from_twitter(self, company: "Company", lookback_hours: int) -> List[SocialPost]:
        """Fetch posts from Twitter/X (placeholder - requires API access)"""
        # Twitter API v2 requires authentication
        # This is a placeholder for future implementation
        print(f"Info: Twitter integration not yet implemented for {company.name}")
        return []
