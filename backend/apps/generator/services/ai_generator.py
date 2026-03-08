"""
Generator Module — AI Content Generator
Uses OpenAI or Anthropic to generate social media posts for each brand.
"""
import logging
import json
from dataclasses import dataclass, field
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class GeneratedContent:
    """Structured result returned by the AI generator."""
    post_text: str
    caption: str
    hashtags: list = field(default_factory=list)
    image_prompt: str = ""
    raw_response: str = ""

    def full_post(self) -> str:
        """Combine post text + caption + hashtags into one publishable string."""
        parts = [self.post_text]
        if self.caption:
            parts.append(f"\n{self.caption}")
        if self.hashtags:
            parts.append("\n" + " ".join(self.hashtags))
        return "\n".join(parts)


# ─── Prompt Templates per Content Type ───────────────────────────────────────

PROMPTS = {
    "education": """You are an educational content creator for {brand_name}.
Tone: {tone}. Create a highly engaging educational social media post about: {topic}.
Requirements:
- Post text: 1–3 punchy sentences with a key learning point
- Caption: 1 sentence that drives engagement (question or CTA)
- 5 relevant hashtags
- Image prompt: a clean visual description for a quote card
Respond ONLY in valid JSON with keys: post_text, caption, hashtags (list), image_prompt""",

    "programming": """You are a programming content creator for {brand_name}.
Tone: {tone}. Create an engaging programming tip or insight about: {topic}.
Requirements:
- Post text: A practical tip, trick, or insight (2–3 sentences max)
- Include a short code snippet or concept if relevant
- Caption: A question or CTA that sparks conversation
- 5 hashtags like #Python #Coding #DevTips
- Image prompt: describe a developer-themed quote card
Respond ONLY in valid JSON with keys: post_text, caption, hashtags (list), image_prompt""",

    "devotional": """You are a faith-based devotional content creator for {brand_name}.
Tone: {tone}. Create a daily devotional post about: {topic}.
Requirements:
- Post text: An uplifting scripture-inspired message (2–3 sentences)
- Caption: An encouraging call to action
- 5 relevant hashtags like #DailyDevotion #Faith #God
- Image prompt: peaceful, spiritual quote card visual
Respond ONLY in valid JSON with keys: post_text, caption, hashtags (list), image_prompt""",

    "forex": """You are a forex/trading content creator for {brand_name}.
Tone: {tone}. Create an educational forex trading tip about: {topic}.
Requirements:
- Post text: A practical trading insight or tip (2–3 sentences)
- Caption: Engaging question or motivational CTA for traders
- 5 hashtags like #Forex #Trading #FX #FinanceTips
- Image prompt: professional financial-themed quote card
Respond ONLY in valid JSON with keys: post_text, caption, hashtags (list), image_prompt
IMPORTANT: Do NOT give specific buy/sell signals or financial advice.""",

    "motivation": """You are a motivational content creator for {brand_name}.
Tone: {tone}. Create an inspiring motivational post about: {topic}.
Requirements:
- Post text: A powerful motivational message (1–3 sentences)
- Caption: Question or CTA that drives engagement
- 5 hashtags like #Motivation #Mindset #Success
- Image prompt: bold, inspiring quote card description
Respond ONLY in valid JSON with keys: post_text, caption, hashtags (list), image_prompt""",

    "news": """You are a news commentary creator for {brand_name}.
Tone: {tone}. Create an insightful social media post about this news: {topic}.
Requirements:
- Post text: Brief, clear summary with commentary (2–3 sentences)
- Caption: Thought-provoking question for discussion
- 5 relevant hashtags
- Image prompt: news-style quote card visual
Respond ONLY in valid JSON with keys: post_text, caption, hashtags (list), image_prompt""",

    "general": """You are a social media content creator for {brand_name}.
Tone: {tone}. Create an engaging post about: {topic}.
Requirements:
- Post text: 2–3 compelling sentences
- Caption: engaging CTA or question
- 5 relevant hashtags
- Image prompt: quote card visual description
Respond ONLY in valid JSON with keys: post_text, caption, hashtags (list), image_prompt""",
}

DEFAULT_TOPICS = {
    "education": "the power of consistent daily learning and growth",
    "programming": "clean code principles and writing readable Python",
    "devotional": "God's grace and finding peace in difficult times",
    "forex": "the importance of risk management in trading",
    "motivation": "building discipline as the foundation of success",
    "news": "recent developments in AI and technology",
    "general": "the value of continuous self-improvement",
}


class AIGenerator:
    """
    Generates social media content using OpenAI GPT or Anthropic Claude.
    """

    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self.model = settings.AI_MODEL

    def generate(
        self,
        brand_name: str,
        content_type: str,
        tone: str,
        topic: Optional[str] = None,
        custom_voice_prompt: str = "",
        brand_hashtags: Optional[list] = None,
    ) -> GeneratedContent:
        """
        Main generation method. Returns structured GeneratedContent.
        """
        topic = topic or DEFAULT_TOPICS.get(content_type, "life lessons and growth")
        prompt_template = PROMPTS.get(content_type, PROMPTS["general"])

        system_prompt = prompt_template.format(
            brand_name=brand_name,
            tone=tone,
            topic=topic,
        )

        if custom_voice_prompt:
            system_prompt += f"\n\nAdditional brand instructions: {custom_voice_prompt}"

        logger.info(f"Generating [{content_type}] content for '{brand_name}' | topic: {topic[:50]}")

        if self.provider == "anthropic":
            raw = self._call_anthropic(system_prompt)
        else:
            raw = self._call_openai(system_prompt)

        content = self._parse_response(raw, brand_hashtags or [])
        logger.info(f"Generated post: {content.post_text[:80]}...")
        return content

    # ── OpenAI ─────────────────────────────────────────────────────────────
    def _call_openai(self, prompt: str) -> str:
        try:
            import openai
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional social media content creator. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=600,
                temperature=0.85,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    # ── Anthropic ──────────────────────────────────────────────────────────
    def _call_anthropic(self, prompt: str) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=600,
                system="You are a professional social media content creator. Always respond with valid JSON only.",
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    # ── Parse Response ─────────────────────────────────────────────────────
    def _parse_response(self, raw: str, brand_hashtags: list) -> GeneratedContent:
        """Parse AI JSON response into a GeneratedContent dataclass."""
        # Strip markdown code blocks if present
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI response as JSON. Raw: {raw[:200]}")
            # Fallback: treat entire response as post text
            return GeneratedContent(
                post_text=raw[:280],
                caption="Follow us for more!",
                hashtags=brand_hashtags,
                raw_response=raw,
            )

        # Merge brand hashtags with AI-generated ones
        ai_hashtags = data.get("hashtags", [])
        all_hashtags = list(dict.fromkeys(ai_hashtags + brand_hashtags))  # deduplicate

        return GeneratedContent(
            post_text=data.get("post_text", ""),
            caption=data.get("caption", ""),
            hashtags=all_hashtags[:10],  # cap at 10
            image_prompt=data.get("image_prompt", ""),
            raw_response=raw,
        )
