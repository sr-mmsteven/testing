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
    # Social media specific fields
    social_posts: list = attrs.field(factory=list, init=False)
    social_sentiment: str = attrs.field(default="", init=False)
    social_sentiment_score: float = attrs.field(default=0.0, init=False)


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

    def analyze_company_news(self, company: "Company", articles: List, social_posts: List = None) -> SentimentAnalysis:
        """Analyze sentiment for all news articles and social media posts about a company"""
        social_posts = social_posts or []

        # Build prompt with all articles and social posts
        prompt = self._build_analysis_prompt(company, articles, social_posts)

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
            analysis = self._parse_analysis_response(company, analysis_text, articles, social_posts)

            return analysis

        except Exception as e:
            print(f"Error analyzing sentiment for {company.name}: {e}")
            # Return a basic analysis on error
            analysis = SentimentAnalysis(company.name, company.ticker)
            analysis.overall_sentiment = "error"
            analysis.summary = f"Failed to analyze sentiment: {str(e)}"
            return analysis

    def _build_analysis_prompt(self, company: "Company", articles: List, social_posts: List = None) -> str:
        """Build the prompt for Claude API including social media posts"""
        social_posts = social_posts or []

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

        # Build social media posts section
        social_text = []
        if social_posts:
            for i, post in enumerate(social_posts, 1):
                engagement_str = ""
                if hasattr(post, 'engagement') and post.engagement:
                    score = post.engagement.get('score', 0)
                    comments = post.engagement.get('num_comments', 0)
                    engagement_str = f"Engagement: {score} upvotes, {comments} comments\n"

                social_text.append(
                    f"Post {i}:\n"
                    f"Platform: {post.platform}\n"
                    f"Author: {post.author}\n"
                    f"Posted: {post.created_at}\n"
                    f"{engagement_str}"
                    f"Content: {post.text}\n"
                )

        # Build comprehensive prompt
        prompt_parts = [f"""You are a financial news and social media analyst. Analyze the following information about {company.name} ({company.ticker}) and provide a comprehensive sentiment analysis."""]

        if articles_text:
            prompt_parts.append(f"\n\nNews Articles:\n{chr(10).join(articles_text)}")

        if social_text:
            prompt_parts.append(f"\n\nSocial Media Posts:\n{chr(10).join(social_text)}")

        prompt_parts.append("""

Please provide your analysis in the following structured format:

OVERALL_SENTIMENT: [Choose one: POSITIVE, NEGATIVE, NEUTRAL, or MIXED]

SENTIMENT_SCORE: [Provide a score from -1.0 (very negative) to 1.0 (very positive)]

SOCIAL_SENTIMENT: [If social media data is present, choose one: POSITIVE, NEGATIVE, NEUTRAL, or MIXED]

SOCIAL_SENTIMENT_SCORE: [If social media data is present, provide a score from -1.0 to 1.0]

KEY_THEMES:
- [List 3-5 main themes or topics across all sources]

MARKET_IMPACT: [Brief assessment of potential market impact - one paragraph]

SUMMARY:
[Provide a 2-3 paragraph executive summary covering:
1. What's happening with the company (from news and social media)
2. Overall sentiment and why (note any differences between news and social sentiment)
3. Key takeaways for investors]

ARTICLE_HIGHLIGHTS:
[For each significant article or trending social post, provide a brief bullet point about its key message and sentiment]

Be objective and balanced. When social media is present, note if there's divergence between professional news sentiment and retail investor/public sentiment. Consider both immediate reactions and longer-term implications.""")

        return ''.join(prompt_parts)

    def _parse_analysis_response(self, company: "Company", response_text: str,
                                  articles: List, social_posts: List = None) -> SentimentAnalysis:
        """Parse Claude's response into structured analysis"""
        social_posts = social_posts or []
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
            elif line.startswith('SOCIAL_SENTIMENT:'):
                current_section = 'social_sentiment'
                sections[current_section] = line.split(':', 1)[1].strip()
            elif line.startswith('SOCIAL_SENTIMENT_SCORE:'):
                current_section = 'social_score'
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

        # Parse social media sentiment if present
        if 'social_sentiment' in sections:
            social_sentiment_text = sections.get('social_sentiment', 'NEUTRAL').upper()
            analysis.social_sentiment = social_sentiment_text.lower()

        # Parse social sentiment score
        if 'social_score' in sections:
            try:
                social_score_text = sections.get('social_score', '0.0')
                import re
                score_match = re.search(r'-?\d+\.?\d*', social_score_text)
                if score_match:
                    analysis.social_sentiment_score = float(score_match.group())
            except:
                analysis.social_sentiment_score = 0.0

        # Store articles and social posts for reference
        analysis.articles = articles
        analysis.social_posts = social_posts

        return analysis
