#!/usr/bin/env python3
"""
News Sentiment Report Generator

A tool that fetches daily news for specified companies and uses Claude AI
to generate sentiment analysis reports.
"""
import sys
import os
import yaml
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from news_fetcher import NewsFetcher
from sentiment_analyzer import SentimentAnalyzer
from report_generator import ReportGenerator


def load_config(config_path: str = 'config.yaml') -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_path}' not found.")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse configuration file: {e}")
        sys.exit(1)


def validate_environment():
    """Validate required environment variables"""
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable is not set.")
        print("Please set it in your .env file or environment.")
        print("\nGet your API key from: https://console.anthropic.com/")
        sys.exit(1)

    newsapi_key = os.getenv('NEWSAPI_KEY')
    if not newsapi_key:
        print("Warning: NEWSAPI_KEY is not set. News fetching may be limited.")
        print("Get a free key from: https://newsapi.org/\n")


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
    print(banner)


def main():
    """Main application entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Generate daily news sentiment reports using Claude AI'
    )
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    parser.add_argument(
        '-o', '--output',
        help='Output file path (overrides config)'
    )
    parser.add_argument(
        '--format',
        choices=['markdown', 'html', 'text'],
        help='Report format (overrides config)'
    )
    parser.add_argument(
        '--companies',
        nargs='+',
        help='Specific companies to analyze (space-separated names)'
    )
    parser.add_argument(
        '--hours',
        type=int,
        help='Hours to look back for news (overrides config)'
    )
    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Suppress banner output'
    )

    args = parser.parse_args()

    # Print banner
    if not args.no_banner:
        print_banner()

    # Load environment variables
    load_dotenv()

    # Validate environment
    validate_environment()

    # Load configuration
    print(f"📋 Loading configuration from '{args.config}'...")
    config = load_config(args.config)

    # Override config with command line arguments
    if args.format:
        config.setdefault('report', {})['format'] = args.format

    if args.hours:
        config.setdefault('news_sources', {}).setdefault('newsapi', {})['lookback_hours'] = args.hours

    # Filter companies if specified
    companies = config.get('companies', [])
    if args.companies:
        companies = [c for c in companies if c['name'] in args.companies]
        if not companies:
            print(f"Error: No matching companies found for: {args.companies}")
            sys.exit(1)

    print(f"📈 Analyzing {len(companies)} companies: {', '.join(c['name'] for c in companies)}\n")

    # Initialize components
    try:
        news_fetcher = NewsFetcher(config)
        sentiment_analyzer = SentimentAnalyzer(config)
        report_generator = ReportGenerator(config)
    except Exception as e:
        print(f"Error: Failed to initialize components: {e}")
        sys.exit(1)

    # Process each company
    analyses = []
    lookback_hours = config.get('news_sources', {}).get('newsapi', {}).get('lookback_hours', 24)

    for i, company in enumerate(companies, 1):
        print(f"[{i}/{len(companies)}] Processing {company['name']} ({company.get('ticker', 'N/A')})...")

        # Fetch news
        print(f"  📰 Fetching news articles...")
        try:
            articles = news_fetcher.fetch_company_news(company, lookback_hours)
            print(f"  ✓ Found {len(articles)} articles")
        except Exception as e:
            print(f"  ✗ Error fetching news: {e}")
            continue

        # Analyze sentiment
        print(f"  🤖 Analyzing sentiment with Claude...")
        try:
            analysis = sentiment_analyzer.analyze_company_news(company, articles)
            print(f"  ✓ Sentiment: {analysis.overall_sentiment.upper()} "
                  f"(Score: {analysis.sentiment_score:+.2f})")
            analyses.append(analysis)
        except Exception as e:
            print(f"  ✗ Error analyzing sentiment: {e}")
            continue

        print()

    if not analyses:
        print("Error: No analyses completed successfully.")
        sys.exit(1)

    # Generate report
    print("📝 Generating report...")
    try:
        timestamp = datetime.now()
        report_path = report_generator.generate_report(analyses, timestamp)
        print(f"✓ Report generated successfully!\n")
        print(f"📄 Report saved to: {report_path}")

        # If custom output path specified, copy the report there
        if args.output:
            import shutil
            shutil.copy(report_path, args.output)
            print(f"📄 Report also saved to: {args.output}")

    except Exception as e:
        print(f"Error: Failed to generate report: {e}")
        sys.exit(1)

    print("\n✨ All done! Have a great day!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
