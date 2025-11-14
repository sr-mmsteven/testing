#!/usr/bin/env python3
"""
News Sentiment Report Generator

A tool that fetches daily news for specified companies and uses Claude AI
to generate sentiment analysis reports.
"""
import sys
import os
import click
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from .news_fetcher import NewsFetcher
from .social_media_fetcher import SocialMediaFetcher
from .sentiment_analyzer import SentimentAnalyzer
from .report_generator import ReportGenerator
from .config import load_config, Config


def load_config_with_error_handling(config_path: str = 'config.yaml') -> Config:
    """Load configuration from YAML file with error handling"""
    try:
        return load_config(config_path)
    except FileNotFoundError:
        click.echo(click.style(f"Error: Configuration file '{config_path}' not found.", fg='red'))
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Error: Failed to parse configuration file: {e}", fg='red'))
        sys.exit(1)


def validate_environment():
    """Validate required environment variables"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        click.echo(click.style("Error: ANTHROPIC_API_KEY environment variable is not set.", fg='red'))
        click.echo("Please set it in your .env file or environment.")
        click.echo("\nGet your API key from: https://console.anthropic.com/")
        sys.exit(1)

    newsapi_key = os.getenv('NEWSAPI_KEY')
    if not newsapi_key:
        click.echo(click.style("Warning: NEWSAPI_KEY is not set. News fetching may be limited.", fg='yellow'))
        click.echo("Get a free key from: https://newsapi.org/\n")


def print_banner():
    """Print application banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║       📊  News Sentiment Report Generator  📊                ║
║                                                               ║
║           Powered by Claude AI (Anthropic)                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """
    click.echo(banner)


@click.command()
@click.option(
    '-c', '--config',
    default='config.yaml',
    type=click.Path(exists=True),
    help='Path to configuration file (default: config.yaml)'
)
@click.option(
    '-o', '--output',
    type=click.Path(),
    help='Output file path (overrides config)'
)
@click.option(
    '--format',
    type=click.Choice(['markdown', 'html', 'text'], case_sensitive=False),
    help='Report format (overrides config)'
)
@click.option(
    '--companies',
    multiple=True,
    help='Specific companies to analyze (can be used multiple times: --companies Apple --companies Tesla)'
)
@click.option(
    '--hours',
    type=int,
    help='Hours to look back for news (overrides config)'
)
@click.option(
    '--no-banner',
    is_flag=True,
    help='Suppress banner output'
)
@click.option(
    '--sources',
    type=click.Choice(['all', 'news', 'social'], case_sensitive=False),
    default='all',
    help='Data sources to analyze: all (default), news only, or social media only'
)
def main(config, output, format, companies, hours, no_banner, sources):
    """Generate sentiment reports from news and/or social media using Claude AI.

    This tool fetches recent news articles and social media posts for configured
    companies and uses Claude AI to perform comprehensive sentiment analysis,
    generating detailed reports in your chosen format.

    Examples:

        # Generate report for all companies using all sources
        news-sentiment

        # Analyze only social media sentiment (skip news)
        news-sentiment --sources social

        # Analyze only news articles (skip social media)
        news-sentiment --sources news

        # Analyze specific companies
        news-sentiment --companies Apple --companies Tesla

        # Generate HTML report from social media only
        news-sentiment --sources social --format html

        # Look back 48 hours
        news-sentiment --hours 48
    """
    # Print banner
    if not no_banner:
        print_banner()

    # Load environment variables
    load_dotenv()

    # Validate environment
    validate_environment()

    # Load configuration
    click.echo(f"📋 Loading configuration from '{config}'...")
    config_data = load_config_with_error_handling(config)

    # Override config with command line arguments
    if format:
        config_data.report.format = format

    if hours:
        config_data.news_sources.newsapi.lookback_hours = hours

    # Filter companies if specified
    companies_list = config_data.companies
    if companies:
        companies_list = [c for c in companies_list if c.name in companies]
        if not companies_list:
            click.echo(click.style(f"Error: No matching companies found for: {companies}", fg='red'))
            sys.exit(1)

    click.echo(f"📈 Analyzing {len(companies_list)} companies: {', '.join(c.name for c in companies_list)}\n")

    # Initialize components
    try:
        news_fetcher = NewsFetcher(config_data) if sources in ['all', 'news'] else None
        social_media_fetcher = SocialMediaFetcher(config_data) if sources in ['all', 'social'] else None
        sentiment_analyzer = SentimentAnalyzer(config_data)
        report_generator = ReportGenerator(config_data)
    except Exception as e:
        click.echo(click.style(f"Error: Failed to initialize components: {e}", fg='red'))
        sys.exit(1)

    # Process each company
    analyses = []
    lookback_hours = config_data.news_sources.newsapi.lookback_hours

    with click.progressbar(
        companies_list,
        label='Processing companies',
        item_show_func=lambda c: c.name if c else ''
    ) as companies_bar:
        for i, company in enumerate(companies_bar, 1):
            click.echo(f"\n[{i}/{len(companies_list)}] Processing {company.name} ({company.ticker})...")

            all_content = []

            # Fetch news articles if enabled
            if news_fetcher and sources in ['all', 'news']:
                click.echo(f"  📰 Fetching news articles...")
                try:
                    articles = news_fetcher.fetch_company_news(company, lookback_hours)
                    click.echo(click.style(f"  ✓ Found {len(articles)} news articles", fg='green'))
                    all_content.extend(articles)
                except Exception as e:
                    click.echo(click.style(f"  ✗ Error fetching news: {e}", fg='red'))

            # Fetch social media posts if enabled
            if social_media_fetcher and sources in ['all', 'social']:
                click.echo(f"  📱 Fetching social media posts...")
                try:
                    posts = social_media_fetcher.fetch_company_posts(company, lookback_hours)
                    click.echo(click.style(f"  ✓ Found {len(posts)} social media posts", fg='green'))
                    all_content.extend(posts)
                except Exception as e:
                    click.echo(click.style(f"  ✗ Error fetching social media: {e}", fg='red'))

            if not all_content:
                click.echo(click.style(f"  ⚠ No content found for {company.name}", fg='yellow'))
                continue

            # Analyze sentiment
            click.echo(f"  🤖 Analyzing sentiment with Claude...")
            try:
                analysis = sentiment_analyzer.analyze_company_content(company, all_content, sources)
                sentiment_color = 'green' if 'positive' in analysis.overall_sentiment.lower() else (
                    'red' if 'negative' in analysis.overall_sentiment.lower() else 'yellow'
                )
                click.echo(click.style(
                    f"  ✓ Sentiment: {analysis.overall_sentiment.upper()} (Score: {analysis.sentiment_score:+.2f})",
                    fg=sentiment_color
                ))
                analyses.append(analysis)
            except Exception as e:
                click.echo(click.style(f"  ✗ Error analyzing sentiment: {e}", fg='red'))
                continue

    click.echo()

    if not analyses:
        click.echo(click.style("Error: No analyses completed successfully.", fg='red'))
        sys.exit(1)

    # Generate report
    click.echo("📝 Generating report...")
    try:
        timestamp = datetime.now()
        report_path = report_generator.generate_report(analyses, timestamp)
        click.echo(click.style("✓ Report generated successfully!\n", fg='green'))
        click.echo(f"📄 Report saved to: {click.style(report_path, fg='cyan', bold=True)}")

        # If custom output path specified, copy the report there
        if output:
            import shutil
            shutil.copy(report_path, output)
            click.echo(f"📄 Report also saved to: {click.style(output, fg='cyan', bold=True)}")

    except Exception as e:
        click.echo(click.style(f"Error: Failed to generate report: {e}", fg='red'))
        sys.exit(1)

    click.echo(click.style("\n✨ All done! Have a great day!", fg='green', bold=True))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        click.echo(click.style("\n\n⚠️  Interrupted by user. Exiting...", fg='yellow'))
        sys.exit(0)
    except Exception as e:
        click.echo(click.style(f"\n❌ Unexpected error: {e}", fg='red'))
        import traceback
        traceback.print_exc()
        sys.exit(1)
