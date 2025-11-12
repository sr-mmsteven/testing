"""
Sentiment analyzer module - uses Claude API to analyze news sentiment
"""
import os
from typing import List, Dict, TYPE_CHECKING
from anthropic import Anthropic
import attrs

if TYPE_CHECKING:
    from .config import Config, Company


@attrs.define
class SentimentAnalysis:
    company_name: str
    ticker: str
    overall_sentiment: str = attrs.field(default="", init=False)  # positive, negative, neutral, mixed
    sentiment_score: float = attrs.field(default=0.0, init=False)  # -1.0 to 1.0
    key_themes: list[str] = attrs.field(factory=list, init=False)
    article_analyses: list[str] = attrs.field(factory=list, init=False)
    summary: str = attrs.field(default="", init=False)
    market_impact: str = attrs.field(default="", init=False)
    articles: list = attrs.field(factory=list, init=False)


    def __repr__(self):
        return (f"SentimentAnalysis(company='{self.company_name}', "
                f"sentiment='{self.overall_sentiment}', score={self.sentiment_score})")


@attrs.define
class SentimentAnalyzer:
    """Analyzes news sentiment using Claude API"""
    config: Config
    api_key: str = attrs.field(init=False, factory=lambda: os.getenv('ANTHROPIC_API_KEY', ''),
                               validator=attrs.validators.min_len(10))
    client: Anthropic = attrs.field(init=False, default=attrs.Factory(
        lambda self: Anthropic(api_key=self.api_key),
        takes_self=True
    ))


    @property
    def model(self):
        return self.config.claude.model
    
    @property
    def max_tokens(self):
        return self.config.claude.max_tokens
    
    @property
    def temperature(self):
        return self.config.claude.temperature

    def analyze_company_news(self, company: "Company", articles: List) -> SentimentAnalysis:
        """Analyze sentiment for all news articles about a company"""
        # if not articles:
        #     analysis = SentimentAnalysis(company.name, company.ticker)
        #     analysis.overall_sentiment = "neutral"
        #     analysis.summary = "No recent news articles found."
        #     return analysis

        # Build prompt with all articles
        prompt = self._build_analysis_prompt(company, articles)

        # Call Claude API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            # Parse Claude's response
            analysis_text = response.content[0].text
            analysis = self._parse_analysis_response(company, analysis_text, articles)

            return analysis

        except Exception as e:
            print(f"Error analyzing sentiment for {company.name}: {e}")
            # Return a basic analysis on error
            analysis = SentimentAnalysis(company.name, company.ticker)
            analysis.overall_sentiment = "error"
            analysis.summary = f"Failed to analyze sentiment: {str(e)}"
            return analysis

    def _build_analysis_prompt(self, company: "Company", articles: List) -> str:
        """Build the prompt for Claude API"""
        articles_text = []

        for i, article in enumerate(articles, 1):
            articles_text.append(
                f"Article {i}:\n"
                f"Title: {article.title}\n"
                f"Source: {article.source}\n"
                f"Published: {article.published_at}\n"
                f"Description: {article.description}\n"
                f"URL: {article.url}\n"
            )

        prompt = f"""You are a financial news analyst. Analyze social media and any of the following news articles about {company.name} ({company.ticker}) and provide a comprehensive sentiment analysis.

News Articles:
{chr(10).join(articles_text)}

Please provide your analysis in the following structured format:

OVERALL_SENTIMENT: [Choose one: POSITIVE, NEGATIVE, NEUTRAL, or MIXED]

SENTIMENT_SCORE: [Provide a score from -1.0 (very negative) to 1.0 (very positive)]

KEY_THEMES:
- [List 3-5 main themes or topics across the articles]

MARKET_IMPACT: [Brief assessment of potential market impact - one paragraph]

SUMMARY:
[Provide a 2-3 paragraph executive summary covering:
1. What's happening with the company
2. Overall sentiment and why
3. Key takeaways for investors]

ARTICLE_HIGHLIGHTS:
[For each significant article, provide a brief bullet point about its key message and sentiment]

Be objective, balanced, and focus on facts. Consider both immediate reactions and longer-term implications."""

        return prompt

    def _parse_analysis_response(self, company: "Company", response_text: str,
                                  articles: List) -> SentimentAnalysis:
        """Parse Claude's response into structured analysis"""
        analysis = SentimentAnalysis(company.name, company.ticker)

        # Extract sections from response
        sections = {}
        current_section = None
        current_content = []

        for line in response_text.split('\n'):
            line = line.strip()

            # Check for section headers
            if line.startswith('OVERALL_SENTIMENT:'):
                current_section = 'sentiment'
                sections[current_section] = line.split(':', 1)[1].strip()
            elif line.startswith('SENTIMENT_SCORE:'):
                current_section = 'score'
                sections[current_section] = line.split(':', 1)[1].strip()
            elif line.startswith('KEY_THEMES:'):
                current_section = 'themes'
                current_content = []
            elif line.startswith('MARKET_IMPACT:'):
                if current_section == 'themes':
                    sections['themes'] = current_content
                current_section = 'impact'
                current_content = []
            elif line.startswith('SUMMARY:'):
                if current_section == 'impact':
                    sections['impact'] = '\n'.join(current_content)
                current_section = 'summary'
                current_content = []
            elif line.startswith('ARTICLE_HIGHLIGHTS:'):
                if current_section == 'summary':
                    sections['summary'] = '\n'.join(current_content)
                current_section = 'highlights'
                current_content = []
            elif line and current_section:
                current_content.append(line)

        # Save last section
        if current_section == 'summary':
            sections['summary'] = '\n'.join(current_content)
        elif current_section == 'highlights':
            sections['highlights'] = current_content
        elif current_section == 'impact':
            sections['impact'] = '\n'.join(current_content)

        # Populate analysis object
        sentiment_text = sections.get('sentiment', 'NEUTRAL').upper()
        analysis.overall_sentiment = sentiment_text.lower()

        # Parse sentiment score
        try:
            score_text = sections.get('score', '0.0')
            # Extract numeric value
            import re
            score_match = re.search(r'-?\d+\.?\d*', score_text)
            if score_match:
                analysis.sentiment_score = float(score_match.group())
        except:
            analysis.sentiment_score = 0.0

        # Extract themes
        if 'themes' in sections:
            analysis.key_themes = [
                theme.lstrip('- ').strip()
                for theme in sections['themes']
                if theme.strip() and theme.strip().startswith('-')
            ]

        analysis.summary = sections.get('summary', '').strip()
        analysis.market_impact = sections.get('impact', '').strip()

        # Store article highlights
        if 'highlights' in sections:
            analysis.article_analyses = sections['highlights']

        # Store articles for reference
        analysis.articles = articles

        return analysis
