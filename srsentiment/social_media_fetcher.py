"""
Social media fetcher module - fetches posts from social media platforms
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import attrs
import time
import praw

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
    _reddit: Optional[praw.Reddit] = None

    def __attrs_post_init__(self):
        """Initialize Reddit API client with OAuth"""
        reddit_config = self.config.social_media_sources.reddit
        if reddit_config.enabled and reddit_config.client_id and reddit_config.client_secret:
            try:
                self._reddit = praw.Reddit(
                    client_id=reddit_config.client_id,
                    client_secret=reddit_config.client_secret,
                    user_agent=reddit_config.user_agent
                )
                # Test the connection
                self._reddit.read_only = True
                print(f"✅ Successfully connected to Reddit API (read-only mode)")
            except Exception as e:
                print(f"⚠️  Failed to initialize Reddit API: {e}")
                print(f"   Reddit posts will be skipped.")
                self._reddit = None

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
        """Fetch posts from Reddit using PRAW (OAuth API)"""
        posts = []

        # Check if Reddit client is initialized
        if not self._reddit:
            print(f"⚠️  Reddit API not configured. Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET.")
            return posts

        try:
            # Build search query from company keywords
            keywords = company.keywords if company.keywords else [company.name]

            # Get subreddits to search
            subreddits = self.config.social_media_sources.reddit.subreddits

            # Calculate timestamp threshold
            time_threshold = datetime.now() - timedelta(hours=lookback_hours)
            time_threshold_unix = time_threshold.timestamp()

            for subreddit_name in subreddits:
                for keyword in keywords:
                    try:
                        # Get subreddit instance
                        subreddit = self._reddit.subreddit(subreddit_name)

                        # Search for posts in the subreddit
                        # Use time_filter for better performance
                        time_filter = 'day' if lookback_hours <= 24 else ('week' if lookback_hours <= 168 else 'month')

                        print(f"  Searching r/{subreddit_name} for '{keyword}'...")

                        # Search posts
                        search_results = subreddit.search(
                            keyword,
                            sort='new',
                            time_filter=time_filter,
                            limit=25
                        )

                        post_count = 0
                        for submission in search_results:
                            # Check if post is within time range
                            if submission.created_utc < time_threshold_unix:
                                continue

                            # Skip removed/deleted posts
                            if submission.removed_by_category or submission.selftext == '[removed]':
                                continue

                            posts.append(SocialMediaPost(
                                title=submission.title,
                                content=submission.selftext[:500] if submission.selftext else '',
                                url=f"https://www.reddit.com{submission.permalink}",
                                published_at=datetime.fromtimestamp(submission.created_utc).isoformat(),
                                source=f"r/{subreddit_name}",
                                platform='reddit',
                                score=submission.score
                            ))
                            post_count += 1

                        if post_count > 0:
                            print(f"    ✅ Found {post_count} posts")
                        else:
                            print(f"    No posts found")

                        # Small delay to be respectful to Reddit's API
                        time.sleep(1)

                    except Exception as e:
                        print(f"  ⚠️  Failed to fetch from r/{subreddit_name} for '{keyword}': {e}")
                        continue

        except Exception as e:
            print(f"⚠️  Failed to fetch Reddit posts for {company.name}: {e}")

        return posts
