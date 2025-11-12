"""
Report generator module - generates formatted reports from sentiment analysis
"""
import os
from datetime import datetime
from typing import List, Dict, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from .config import Config
import attrs


@attrs.define
class ReportGenerator:
    config: Config
    output_dir: str = attrs.field(
        init=False,
        default=attrs.Factory(lambda self: self.config.report.output_dir, takes_self=True),
        )
    format: str = attrs.field(init=False, default=attrs.Factory(lambda self: self.config.report.format, takes_self=True))

    def __attrs_post_init__(self):
        # Create output directory if it doesn't exist
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def generate_report(self, analyses: List, timestamp: datetime | None = None) -> str:
        """Generate a report from sentiment analyses"""
        if timestamp is None:
            timestamp = datetime.now()

        if self.format == 'markdown':
            content = self._generate_markdown_report(analyses, timestamp)
            extension = 'md'
        elif self.format == 'html':
            content = self._generate_html_report(analyses, timestamp)
            extension = 'html'
        else:
            content = self._generate_text_report(analyses, timestamp)
            extension = 'txt'

        # Save report to file
        filename = f"sentiment_report_{timestamp.strftime('%Y%m%d_%H%M%S')}.{extension}"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        return filepath

    def _generate_markdown_report(self, analyses: List, timestamp: datetime) -> str:
        """Generate a markdown formatted report"""
        lines = []

        # Header
        lines.append("# 📊 Daily News Sentiment Report")
        lines.append(f"\n**Generated:** {timestamp.strftime('%B %d, %Y at %I:%M %p')}\n")
        lines.append("---\n")

        # Executive Summary
        if self.config.report.include_summary:
            lines.append("## Executive Summary\n")
            lines.append(self._generate_executive_summary(analyses))
            lines.append("\n---\n")

        # Individual company analyses
        for analysis in analyses:
            lines.append(f"## {analysis.company_name} ({analysis.ticker})\n")

            # Sentiment badge
            sentiment_emoji = self._get_sentiment_emoji(analysis.overall_sentiment)
            lines.append(f"**Overall Sentiment:** {sentiment_emoji} {analysis.overall_sentiment.upper()}")
            lines.append(f" (Score: {analysis.sentiment_score:+.2f})\n")

            # Key themes
            if analysis.key_themes:
                lines.append("### 🎯 Key Themes\n")
                for theme in analysis.key_themes:
                    lines.append(f"- {theme}")
                lines.append("")

            # Market impact
            if analysis.market_impact:
                lines.append("### 📈 Market Impact\n")
                lines.append(f"{analysis.market_impact}\n")

            # Summary
            if analysis.summary:
                lines.append("### 📝 Summary\n")
                lines.append(f"{analysis.summary}\n")

            # Article highlights
            if hasattr(analysis, 'article_analyses') and analysis.article_analyses:
                lines.append("### 📰 Article Highlights\n")
                for highlight in analysis.article_analyses:
                    if highlight.strip():
                        lines.append(f"{highlight}")
                lines.append("")

            # Recent articles
            if hasattr(analysis, 'articles') and analysis.articles:
                lines.append("### 📚 Recent Articles\n")
                for i, article in enumerate(analysis.articles[:5], 1):
                    lines.append(f"{i}. **{article.title}**")
                    lines.append(f"   - Source: {article.source}")
                    lines.append(f"   - Published: {article.published_at}")
                    lines.append(f"   - [Read more]({article.url})")
                lines.append("")

            lines.append("---\n")

        # Footer
        lines.append("\n*Report generated using Claude AI*")

        return '\n'.join(lines)

    def _generate_html_report(self, analyses: List, timestamp: datetime) -> str:
        """Generate an HTML formatted report"""
        html = []

        # HTML header
        html.append("<!DOCTYPE html>")
        html.append("<html lang='en'>")
        html.append("<head>")
        html.append("<meta charset='UTF-8'>")
        html.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html.append("<title>Daily News Sentiment Report</title>")
        html.append("<style>")
        html.append(self._get_html_styles())
        html.append("</style>")
        html.append("</head>")
        html.append("<body>")

        # Header
        html.append("<div class='header'>")
        html.append("<h1>📊 Daily News Sentiment Report</h1>")
        html.append(f"<p class='timestamp'>Generated: {timestamp.strftime('%B %d, %Y at %I:%M %p')}</p>")
        html.append("</div>")

        # Executive Summary
        if self.config.report.include_summary:
            html.append("<div class='executive-summary'>")
            html.append("<h2>Executive Summary</h2>")
            html.append(f"<p>{self._generate_executive_summary(analyses)}</p>")
            html.append("</div>")

        # Individual company analyses
        for analysis in analyses:
            sentiment_class = analysis.overall_sentiment.lower().replace(' ', '-')
            html.append(f"<div class='company-section'>")
            html.append(f"<h2>{analysis.company_name} ({analysis.ticker})</h2>")

            html.append(f"<div class='sentiment-badge {sentiment_class}'>")
            html.append(f"{self._get_sentiment_emoji(analysis.overall_sentiment)} ")
            html.append(f"{analysis.overall_sentiment.upper()} (Score: {analysis.sentiment_score:+.2f})")
            html.append("</div>")

            if analysis.key_themes:
                html.append("<h3>🎯 Key Themes</h3>")
                html.append("<ul>")
                for theme in analysis.key_themes:
                    html.append(f"<li>{theme}</li>")
                html.append("</ul>")

            if analysis.market_impact:
                html.append("<h3>📈 Market Impact</h3>")
                html.append(f"<p>{analysis.market_impact}</p>")

            if analysis.summary:
                html.append("<h3>📝 Summary</h3>")
                html.append(f"<p>{analysis.summary}</p>")

            if hasattr(analysis, 'articles') and analysis.articles:
                html.append("<h3>📚 Recent Articles</h3>")
                html.append("<ul class='article-list'>")
                for article in analysis.articles[:5]:
                    html.append(f"<li>")
                    html.append(f"<strong><a href='{article.url}' target='_blank'>{article.title}</a></strong>")
                    html.append(f"<br><small>{article.source} - {article.published_at}</small>")
                    html.append(f"</li>")
                html.append("</ul>")

            html.append("</div>")

        # Footer
        html.append("<div class='footer'>")
        html.append("<p><em>Report generated using Claude AI</em></p>")
        html.append("</div>")

        html.append("</body>")
        html.append("</html>")

        return '\n'.join(html)

    def _generate_text_report(self, analyses: List, timestamp: datetime) -> str:
        """Generate a plain text formatted report"""
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("DAILY NEWS SENTIMENT REPORT".center(80))
        lines.append(f"{timestamp.strftime('%B %d, %Y at %I:%M %p')}".center(80))
        lines.append("=" * 80)
        lines.append("")

        # Executive Summary
        if self.config.report.include_summary:
            lines.append("EXECUTIVE SUMMARY")
            lines.append("-" * 80)
            lines.append(self._generate_executive_summary(analyses))
            lines.append("")
            lines.append("=" * 80)
            lines.append("")

        # Individual company analyses
        for analysis in analyses:
            lines.append(f"{analysis.company_name} ({analysis.ticker})")
            lines.append("-" * 80)

            lines.append(f"Overall Sentiment: {analysis.overall_sentiment.upper()} "
                        f"(Score: {analysis.sentiment_score:+.2f})")
            lines.append("")

            if analysis.key_themes:
                lines.append("Key Themes:")
                for theme in analysis.key_themes:
                    lines.append(f"  * {theme}")
                lines.append("")

            if analysis.market_impact:
                lines.append("Market Impact:")
                lines.append(analysis.market_impact)
                lines.append("")

            if analysis.summary:
                lines.append("Summary:")
                lines.append(analysis.summary)
                lines.append("")

            if hasattr(analysis, 'articles') and analysis.articles:
                lines.append("Recent Articles:")
                for i, article in enumerate(analysis.articles[:5], 1):
                    lines.append(f"  {i}. {article.title}")
                    lines.append(f"     {article.source} - {article.published_at}")
                    lines.append(f"     {article.url}")
                lines.append("")

            lines.append("=" * 80)
            lines.append("")

        lines.append("Report generated using Claude AI")

        return '\n'.join(lines)

    def _generate_executive_summary(self, analyses: List) -> str:
        """Generate an executive summary from all analyses"""
        if not analyses:
            return "No sentiment data available."

        positive = sum(1 for a in analyses if 'positive' in a.overall_sentiment.lower())
        negative = sum(1 for a in analyses if 'negative' in a.overall_sentiment.lower())
        neutral = sum(1 for a in analyses if 'neutral' in a.overall_sentiment.lower())

        summary = f"Analyzed {len(analyses)} companies. "
        summary += f"Sentiment breakdown: {positive} positive, {negative} negative, {neutral} neutral. "

        # Highlight most positive and most negative
        sorted_analyses = sorted(analyses, key=lambda x: x.sentiment_score, reverse=True)

        if sorted_analyses:
            most_positive = sorted_analyses[0]
            most_negative = sorted_analyses[-1]

            if most_positive.sentiment_score > 0:
                summary += f"\n\nMost positive: {most_positive.company_name} "
                summary += f"({most_positive.sentiment_score:+.2f}). "

            if most_negative.sentiment_score < 0:
                summary += f"Most negative: {most_negative.company_name} "
                summary += f"({most_negative.sentiment_score:+.2f})."

        return summary

    def _get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji for sentiment"""
        sentiment = sentiment.lower()
        if 'positive' in sentiment:
            return "🟢"
        elif 'negative' in sentiment:
            return "🔴"
        elif 'mixed' in sentiment:
            return "🟡"
        else:
            return "⚪"

    def _get_html_styles(self) -> str:
        """Get CSS styles for HTML report"""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .timestamp {
            margin: 10px 0 0 0;
            opacity: 0.9;
        }
        .executive-summary {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .company-section {
            background: white;
            padding: 25px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .company-section h2 {
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        .sentiment-badge {
            display: inline-block;
            padding: 10px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px 0;
        }
        .sentiment-badge.positive {
            background-color: #d4edda;
            color: #155724;
        }
        .sentiment-badge.negative {
            background-color: #f8d7da;
            color: #721c24;
        }
        .sentiment-badge.neutral, .sentiment-badge.mixed {
            background-color: #fff3cd;
            color: #856404;
        }
        h3 {
            color: #555;
            margin-top: 20px;
        }
        ul {
            padding-left: 20px;
        }
        .article-list {
            list-style: none;
            padding: 0;
        }
        .article-list li {
            padding: 10px;
            margin: 10px 0;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }
        .article-list a {
            color: #667eea;
            text-decoration: none;
        }
        .article-list a:hover {
            text-decoration: underline;
        }
        .footer {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        """
