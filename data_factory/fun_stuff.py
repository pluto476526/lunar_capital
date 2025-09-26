# ORACLE_QUOTES = [
#     "The trend is your friend. Until it betrays you and takes all your money.",
#     "I'd give you trading advice, but then we'd both be wrong.",
#     "The only thing rising faster than this stock is my blood pressure.",
#     "You want a prediction? It will go up. Or down. Or sideways. You're welcome.",
#     "This isn't a loss. It's a 'strategic liquidity reallocation.' Sleep well.",
#     "Buy the rumor, sell the news. Or was it buy the news, sell the rumor? I forget.",
#     "If I knew what would happen tomorrow, I wouldn't be talking to you.",
#     "The market can stay irrational longer than you can stay solvent. Especially you.",
# ]

# # 2. Trader Horoscopes
# HOROSCOPE_TEMPLATES = [
#     "The moons are aligning with a {}. Your risk of FOMO is critical. Stay strong.",
#     "Mercury is in retrograde over the {}. Expect confusing commentary and whipsaws. Trust nothing.",
#     "Your chart shows a classic '{}' pattern. Consider a stop-loss... for your emotions.",
#     "Saturn is opposing your portfolio today. Time to {}.",
#     "Venus enters the house of {}. Perfect day for {} trades.",
# ]

# HOROSCOPE_ASSETS = ["shitcoin", "blue chip", "meme stock", "penny stock", "ETF"]
# HOROSCOPE_ACTIONS = ["hodl", "panic sell", "YOLO", "average down", "take profits"]
# HOROSCOPE_STRATEGIES = ["long", "short", "scalp", "swing", "inverse"]

# # 3. This Day in Trading History
# HISTORICAL_EVENTS = {
#     "04-01": "On this day in 1637, a single tulip bulb could buy a house. Never forget that markets can be... irrational.",
#     "05-06": "On this day in 2010, the Flash Crash happened. A reminder that sometimes, the market just needs a five-minute timeout.",
#     "12-16": "On this day in 1999, an analyst said Amazon was 'overvalued.' The lesson: nobody knows anything.",
#     "10-19": "On this day in 1987, Black Monday occurred. Stocks only go down... sometimes.",
#     "09-15": "On this day in 2008, Lehman Brothers collapsed. Too big to fail? Think again.",
# }

# # 4. Strategy Name Generator Components
# STRATEGY_ADJECTIVES = ["Lunar", "Quantum", "Inverse", "Alpha", "Beta", "Gamma", "Delta", "Omega", "Hyper"]
# STRATEGY_NOUNS = ["Fibonacci", "Turtle", "Wombat", "Gorilla", "Eagle", "Shark", "Dragon", "Phoenix"]
# STRATEGY_CONCEPTS = ["Retracement", "Oscillator", "Momentum", "Hedging", "Algorithm", "Protocol", "Indicator", "Play"]

# # 5. Coping Mechanism Responses
# COPING_RESPONSES = [
#     "Breathe. It's only pretend money.",
#     "This is fine. Everything is fine.",
#     "Have you considered taking up gardening instead?",
#     "At least you're not trading with real money... right?",
#     "Remember: it's not a loss until you sell!",
#     "Maybe just walk away from the computer for a while.",
#     "Have you tried turning it off and on again?",
# ]

# # 6. Dev's Unhinged Trading Journal
# JOURNAL_ENTRIES = [
#     "2:47 AM: Convinced the VIX is controlled by a single algo running in a basement in Cleveland. No proof. Just a feeling.",
#     "Entry 742: Added a 'YOLO' button to the UI. For... testing purposes.",
#     "Note to self: If I see one more 'To the Moon' comment, I'm shorting every meme stock in existence.",
#     "The Fed is definitely watching my portfolio and making decisions based on it. I can feel it.",
#     "Just realized all my trading ideas come from my cat walking across the keyboard. She might be a genius.",
#     "Added more confirmation bias to the algorithm. Now it only shows me what I want to see.",
#     "My trading strategy is based on the alignment of Jupiter's moons. Backtest shows 100% accuracy (sample size: 1).",
# ]


import logging
import random
from datetime import date
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from groq import Groq

logger = logging.getLogger(__name__)


class FunFeatures:
    """A class for generating humorous, witty trading-related content."""

    # Content pools for fallback when LLM is unavailable
    ORACLE_QUOTES = [
        "The trend is your friend. Until it betrays you and takes all your money.",
        "I'd give you trading advice, but then we'd both be wrong.",
        "The only thing rising faster than this stock is my blood pressure.",
        "You want a prediction? It will go up. Or down. Or sideways. You're welcome.",
        "This isn't a loss. It's a 'strategic liquidity reallocation.' Sleep well.",
        "Buy the rumor, sell the news. Or was it buy the news, sell the rumor? I forget.",
        "If I knew what would happen tomorrow, I wouldn't be talking to you.",
        "The market can stay irrational longer than you can stay solvent. Especially you.",
    ]

    HOROSCOPE_ASSETS = ["shitcoin", "blue chip", "meme stock", "penny stock", "ETF"]
    HOROSCOPE_ACTIONS = ["hodl", "panic sell", "YOLO", "average down", "take profits"]
    HOROSCOPE_STRATEGIES = ["long", "short", "scalp", "swing", "inverse"]

    STRATEGY_ADJECTIVES = [
        "Lunar",
        "Quantum",
        "Inverse",
        "Alpha",
        "Beta",
        "Gamma",
        "Delta",
        "Omega",
        "Hyper",
    ]
    STRATEGY_NOUNS = [
        "Fibonacci",
        "Turtle",
        "Wombat",
        "Gorilla",
        "Eagle",
        "Shark",
        "Dragon",
        "Phoenix",
    ]
    STRATEGY_CONCEPTS = [
        "Retracement",
        "Oscillator",
        "Momentum",
        "Hedging",
        "Algorithm",
        "Protocol",
        "Indicator",
    ]

    COPING_RESPONSES = [
        "Breathe. It's only pretend money.",
        "This is fine. Everything is fine...OR NOT!",
        "Have you considered taking up gardening instead?",
        "At least you're not trading with real money... right?",
        "Breathe. It's only pretend money.",
        "Maybe just walk away from the computer for a while.",
        "Have you tried turning it off and on again?",
    ]

    JOURNAL_ENTRIES = [
        "2:47 AM: Convinced the VIX is controlled by a single algo running in a basement in Cleveland. No proof. Just a feeling.",
        "2:49 AM: Added a 'YOLO' button to the UI. For... testing purposes.",
        "2:50 AM: Note to self: If I see one more 'To the Moon' comment, I'm shorting every meme stock in existence.",
        "2:54 AM: The Fed is definitely watching my portfolio and making decisions based on it. I can feel it.",
        "2:55 AM: Just realized all my trading ideas come from my cat walking across the keyboard. She might be a genius.",
        "2:57 AM: Added more confirmation bias to the algorithm. Now it only shows me what I want to see.",
        "2:59 AM: My trading strategy is based on the alignment of Jupiter's moons. Backtest shows 100% accuracy (sample size: 1).",
    ]

    def __init__(self):
        self.groq_api_key = getattr(settings, "GROQ_API_KEY")
        self.groq_available = self.groq_api_key is not None
        self.llm_enabled = getattr(settings, "FUN_STUFF_LLM_ENABLED", True)
        self.llm_fallback_probability = getattr(
            settings, "FUN_STUFF_FALLBACK_PROBABILITY", 0.3
        )

    def _call_llm(self, prompt: str, max_tokens: int = 100) -> Optional[str]:
        """
        Call the LLM with a prompt and return the response.

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum number of tokens to generate

        Returns:
            The LLM response or None if the call fails
        """
        if not self.groq_available or not self.llm_enabled:
            return None

        cache_key = f"fun_features_{hash(prompt)}"
        cached_response = cache.get(cache_key)
        if cached_response:
            return cached_response

        try:
            client = Groq(api_key=self.groq_api_key)
            response = client.chat.completions.create(
                model=getattr(settings, "GROQ_MODEL", "llama-3.3-70b-versatile"),
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a sarcastic, witty financial advisor with a dark sense of humor. "
                            "Your responses should be funny, slightly cynical, and entertaining. "
                            "Include trading/market themes and dark comedy elements."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            result = response.choices[0].message.content.strip()
            cache.set(cache_key, result, timeout=86400)  # Cache for 24 hours
            return result
        except Exception as e:
            logger.error(f"LLM call failed: {str(e)}")
            return None

    def _get_fallback_content(self, content_pool: List[str]) -> str:
        """Get random content from a fallback pool."""
        return random.choice(content_pool)

    def _get_dynamic_content(self, llm_prompt: str, fallback_pool: List[str]) -> str:
        """
        Get content either from LLM or fallback pool based on availability and probability.

        Args:
            llm_prompt: The prompt to send to the LLM
            fallback_pool: List of fallback content if LLM is unavailable

        Returns:
            Generated content
        """
        # Use LLM with probability 1 - fallback_probability, or if fallback is disabled
        use_llm = (random.random() > self.llm_fallback_probability) and self.llm_enabled

        if use_llm and self.openai_available:
            llm_content = self._call_llm(llm_prompt)
            if llm_content:
                return llm_content

        return self._get_fallback_content(fallback_pool)

    def get_oracle_quote(self) -> str:
        """Get a witty trading-related quote."""
        prompt = (
            "Generate a sarcastic, witty quote about trading or financial markets. "
            "Make it funny, slightly cynical, and darkly humorous. "
            "Example: 'The trend is your friend. Until it betrays you and takes all your money.'"
        )
        return self._get_dynamic_content(prompt, self.ORACLE_QUOTES)

    def get_trader_horoscope(self, asset_class: str = "general") -> str:
        """Get a humorous trading horoscope."""
        prompt = (
            f"Create a funny, absurd horoscope for {asset_class} traders. "
            "Make it market-themed with a dark comedic twist. "
            "Example: 'Mercury is in retrograde over the shitcoin market. Expect confusing commentary and whipsaws. Trust nothing.'"
        )

        # Fallback horoscope generation
        templates = [
            f"The moons are aligning with a {{}}. Your risk of FOMO is critical. Stay strong.",
            f"Mercury is in retrograde over the {{}}. Expect confusing commentary and whipsaws. Trust nothing.",
            f"Your chart shows a classic '{{}}' pattern. Consider a stop-loss... for your emotions.",
            f"Saturn is opposing your portfolio today. Time to {{}}.",
            f"Venus enters the house of {{}}. Perfect day for {{}} trades.",
        ]

        template = random.choice(templates)
        count = template.count("{}")

        if count == 1:
            replacement = random.choice(self.HOROSCOPE_ASSETS + self.HOROSCOPE_ACTIONS)
            fallback = template.format(replacement)
        elif count == 2:
            replacement1 = random.choice(self.HOROSCOPE_ASSETS)
            replacement2 = random.choice(self.HOROSCOPE_STRATEGIES)
            fallback = template.format(replacement1, replacement2)
        else:
            fallback = template

        return self._get_dynamic_content(prompt, [fallback])

    def get_historical_events(self, count: int = 3) -> List[str]:
        """
        Get historical trading events from LLM only.

        Args:
            count: Number of events to return

        Returns:
            List of historical events
        """
        if not self.openai_available or not self.llm_enabled:
            return ["Historical events feature requires LLM integration."]

        prompt = (
            f"Share {count} interesting, funny, or ironic events from financial history. "
            "For each event, include the date and a humorous, darkly comedic lesson. "
            "Format each event on a separate line with a consistent style. "
            "Example: 'On this day in 1637, a single tulip bulb could buy a house. Never forget that markets can be... irrational.'"
        )

        cache_key = f"historical_events_{date.today().strftime('%Y-%m-%d')}_{count}"
        cached_events = cache.get(cache_key)

        if cached_events:
            return cached_events

        llm_response = self._call_llm(prompt, max_tokens=200)

        if not llm_response:
            return [
                "Failed to generate historical events. The market historians are on strike."
            ]

        # Process the LLM response
        events = [event.strip() for event in llm_response.split("\n") if event.strip()]
        events = events[:count]  # Ensure we return only the requested number

        # Cache for the rest of the day
        cache.set(cache_key, events, timeout=86400)

        return events

    def generate_strategy_name(self) -> str:
        """Generate a ridiculous trading strategy name."""
        prompt = (
            "Create a ridiculous, over-the-top name for a trading strategy by mashing together "
            "jargon, animals, and celestial bodies. Make it sound impressively meaningless. "
            "Example: 'The Quantum Wombat Retracement Protocol'"
        )

        # Fallback strategy name generation
        fallback = f"The {random.choice(self.STRATEGY_ADJECTIVES)} {random.choice(self.STRATEGY_NOUNS)} {random.choice(self.STRATEGY_CONCEPTS)}"

        return self._get_dynamic_content(prompt, [fallback])

    def get_coping_response(self) -> str:
        """Get a humorous response for coping with trading losses."""
        prompt = (
            "Create a funny, darkly motivational quote for traders who are having a bad day in the markets. "
            "Example: 'Have you considered taking up gardening instead?'"
        )
        return self._get_dynamic_content(prompt, self.COPING_RESPONSES)

    def get_journal_entry(self) -> str:
        """Get a funny, unhinged trading journal entry."""
        prompt = (
            "Write a funny, slightly unhinged entry from a developer's trading journal. "
            "Include conspiracy theories about markets or absurd observations. "
            "Example: '2:47 AM: Convinced the VIX is controlled by a single algo running in a basement in Cleveland. No proof. Just a feeling.'"
        )
        return self._get_dynamic_content(prompt, self.JOURNAL_ENTRIES)


# Factory function for easy dependency injection
def get_fun_features() -> FunFeatures:
    """Get an instance of FunFeatures for dependency injection."""
    return FunFeatures()
