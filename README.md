# News Sentiment Report Generator

A Python tool that fetches daily news for specified companies and uses **Claude AI** (Anthropic) to generate comprehensive sentiment analysis reports.

## Features

- **Multi-Source News Fetching**: Aggregates news from NewsAPI and RSS feeds
- **AI-Powered Sentiment Analysis**: Uses Claude AI to analyze sentiment and market impact
- **Comprehensive Reports**: Generates detailed reports in Markdown, HTML, or plain text
- **Configurable**: Easy YAML configuration for companies and settings
- **Automated**: Can be scheduled to run daily via cron or Task Scheduler

## Quick Start

### 1. Prerequisites

- Python 3.8 or higher
- Anthropic API key (required)
- NewsAPI key (optional but recommended)

### 2. Installation

```bash
# Clone or download this repository
git clone <your-repo-url>
cd testing

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
```

### 3. Configuration

Edit `.env` and add your API keys:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
NEWSAPI_KEY=your_newsapi_key_here
```

**Getting API Keys:**
- **Anthropic API Key**: Sign up at https://console.anthropic.com/
- **NewsAPI Key**: Get a free key at https://newsapi.org/ (100 requests/day on free tier)

### 4. Customize Companies

Edit `config.yaml` to add or modify the companies you want to track:

```yaml
companies:
  - name: "Apple"
    ticker: "AAPL"
    keywords:
      - "Apple Inc"
      - "AAPL"
      - "iPhone"
      - "Tim Cook"
```

### 5. Run the Script

```bash
python main.py
```

Your report will be generated in the `reports/` directory!

## Usage

### Basic Usage

```bash
# Generate report for all companies in config
python main.py

# Generate report for specific companies
python main.py --companies Apple --companies Tesla

# Generate HTML report instead of Markdown
python main.py --format html

# Look back 48 hours instead of default 24
python main.py --hours 48
```

### Command Line Options

```
-c, --config PATH       Path to configuration file (default: config.yaml)
-o, --output PATH       Output file path (overrides config)
--format FORMAT         Report format: markdown, html, or text
--companies TEXT        Specific companies to analyze (can be used multiple times)
--hours N               Hours to look back for news (overrides config)
--no-banner             Suppress banner output
--help                  Show help message and exit
```

### Examples

```bash
# Quick report for Tesla in text format
python main.py --companies Tesla --format text

# Last 12 hours of news for Apple and Microsoft
python main.py --companies Apple --companies Microsoft --hours 12

# Generate HTML report to specific location
python main.py --format html --output ~/Desktop/report.html
```

## Report Output

The tool generates comprehensive reports including:

- **Executive Summary**: Overall sentiment across all companies
- **Per-Company Analysis**:
  - Overall sentiment score (-1.0 to +1.0)
  - Key themes and topics
  - Market impact assessment
  - Executive summary
  - Recent article highlights with links

### Report Formats

1. **Markdown** (default): Clean, readable format with emojis
2. **HTML**: Beautiful, styled report you can open in a browser
3. **Text**: Plain text for email or terminal display

## Configuration

### config.yaml Structure

```yaml
companies:
  - name: "Company Name"
    ticker: "TICK"
    keywords:
      - "keyword 1"
      - "keyword 2"

news_sources:
  newsapi:
    enabled: true
    lookback_hours: 24
    language: "en"
    sort_by: "publishedAt"

  rss_feeds:
    enabled: true
    feeds:
      - "https://feed-url-1.com"
      - "https://feed-url-2.com"

report:
  format: "markdown"
  include_summary: true
  max_articles_per_company: 10
  output_dir: "reports"

claude:
  model: "claude-sonnet-4-5-20250929"
  max_tokens: 4096
  temperature: 0.3
```

## Scheduling

### Linux/Mac (cron)

Run every weekday at 7 AM:

```bash
# Edit crontab
crontab -e

# Add this line (adjust paths)
0 7 * * 1-5 cd /path/to/testing && /usr/bin/python3 main.py
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 7 AM)
4. Action: Start a program
   - Program: `python.exe`
   - Arguments: `main.py`
   - Start in: `C:\path\to\testing`

## Project Structure

```
testing/
├── main.py                 # Main entry point
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from .env.example)
├── .env.example            # Example environment file
├── README.md               # This file
├── src/
│   ├── __init__.py
│   ├── news_fetcher.py     # News fetching logic
│   ├── sentiment_analyzer.py  # Claude AI sentiment analysis
│   └── report_generator.py    # Report generation
└── reports/                # Generated reports (created automatically)
```

## How It Works

1. **News Fetching**: The script queries NewsAPI and RSS feeds for recent articles mentioning your target companies
2. **Sentiment Analysis**: Each company's news is sent to Claude AI with a detailed prompt asking for sentiment analysis
3. **Report Generation**: Claude's analysis is formatted into a beautiful report with overall sentiment, key themes, and market impact
4. **Output**: The report is saved to the `reports/` directory in your chosen format

## Troubleshooting

### "ANTHROPIC_API_KEY environment variable is not set"

Make sure you've:
1. Created a `.env` file from `.env.example`
2. Added your Anthropic API key to the `.env` file
3. The `.env` file is in the same directory as `main.py`

### "NEWSAPI_KEY is not set" warning

This is just a warning. The script will still work using RSS feeds, but news coverage may be limited. Get a free NewsAPI key at https://newsapi.org/

### No articles found

Try:
- Increasing the lookback hours: `--hours 48`
- Adding more keywords to your company configuration
- Checking if the company name/keywords are correct

### Rate limits

- NewsAPI free tier: 100 requests per day
- Anthropic API: Check your usage at https://console.anthropic.com/

## Cost Estimates

**NewsAPI**: Free tier (100 requests/day) is usually sufficient for daily reports on 5-10 companies.

**Anthropic API**:
- Each company analysis uses ~1,000-3,000 tokens
- For 5 companies: ~5,000-15,000 tokens per report
- Claude Sonnet 4.5: ~$3-10 per million tokens (check current pricing)
- **Daily cost estimate**: $0.015 - $0.15 per report

## Advanced Features

### Email Integration

You can extend the script to email reports:

```python
# Add email sending after report generation
import smtplib
from email.mime.text import MIMEText

# Send email with report...
```

### Database Storage

Store historical sentiment data for trend analysis:

```python
# Add after analysis
import sqlite3
# Store analysis.sentiment_score with timestamp...
```

### Custom Prompts

Modify `src/sentiment_analyzer.py` to customize the Claude AI prompt for your specific needs.

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## License

MIT License - feel free to use this for personal or commercial projects.

## Support

For issues with:
- **This script**: Create an issue in this repository
- **Anthropic API**: https://support.anthropic.com/
- **NewsAPI**: https://newsapi.org/support

## Changelog

### Version 1.0.0
- Initial release
- Multi-source news fetching
- Claude AI sentiment analysis
- Multiple report formats
- Command-line interface

---

Made with Claude AI 🤖
