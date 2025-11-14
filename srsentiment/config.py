"""Configuration management using attrs and cattrs."""

from pathlib import Path
from typing import List, Literal

import os
import attrs
import cattrs
import yaml


@attrs.define
class Company:
    """Company configuration."""

    name: str
    ticker: str
    keywords: List[str] = attrs.field(factory=list)


@attrs.define
class NewsAPIConfig:
    """NewsAPI configuration."""

    enabled: bool = True
    lookback_hours: int = 24
    language: str = "en"
    sort_by: str = "publishedAt"
    api_key: str = attrs.field(factory=lambda: os.getenv('NEWSAPIKEY', ''))


@attrs.define
class RSSFeedsConfig:
    """RSS feeds configuration."""

    enabled: bool = True
    feeds: List[str] = attrs.field(factory=list)


@attrs.define
class RedditConfig:
    """Reddit configuration."""

    enabled: bool = True
    subreddits: List[str] = attrs.field(factory=lambda: ["stocks", "investing", "wallstreetbets"])
    # OAuth credentials for Reddit API (required)
    client_id: str = attrs.field(factory=lambda: os.getenv('REDDIT_CLIENT_ID', ''))
    client_secret: str = attrs.field(factory=lambda: os.getenv('REDDIT_CLIENT_SECRET', ''))
    user_agent: str = attrs.field(factory=lambda: os.getenv('REDDIT_USER_AGENT', 'python:srsentiment:v1.0.0 (by /u/your_username)'))


@attrs.define
class SocialMediaSourcesConfig:
    """Social media sources configuration."""

    reddit: RedditConfig = attrs.field(factory=RedditConfig)


@attrs.define
class NewsSourcesConfig:
    """News sources configuration."""

    newsapi: NewsAPIConfig = attrs.field(factory=NewsAPIConfig)
    rss_feeds: RSSFeedsConfig = attrs.field(factory=RSSFeedsConfig)


@attrs.define
class ReportConfig:
    """Report generation configuration."""

    format: Literal["markdown", "html", "text"] = "markdown"
    include_summary: bool = True
    max_articles_per_company: int = 10
    output_dir: str = "reports"


@attrs.define
class ClaudeConfig:
    """Claude API configuration."""

    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 4096
    temperature: float = 0.3


@attrs.define
class Config:
    """Main configuration object."""

    companies: List[Company] = attrs.field(factory=list)
    news_sources: NewsSourcesConfig = attrs.field(factory=NewsSourcesConfig)
    social_media_sources: SocialMediaSourcesConfig = attrs.field(factory=SocialMediaSourcesConfig)
    report: ReportConfig = attrs.field(factory=ReportConfig)
    claude: ClaudeConfig = attrs.field(factory=ClaudeConfig)


# Create a converter instance for serialization/deserialization
converter = cattrs.Converter()


def load_config(file_path: str | Path) -> Config:
    """Load configuration from a YAML file.

    Args:
        file_path: Path to the YAML configuration file.

    Returns:
        Config object populated from the YAML file.
    """
    file_path = Path(file_path)
    with open(file_path, "r") as f:
        data = yaml.safe_load(f)

    return converter.structure(data, Config)


def save_config(config: Config, file_path: str | Path) -> None:
    """Save configuration to a YAML file.

    Args:
        config: Config object to serialize.
        file_path: Path to save the YAML configuration file.
    """
    file_path = Path(file_path)
    data = converter.unstructure(config)

    with open(file_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
