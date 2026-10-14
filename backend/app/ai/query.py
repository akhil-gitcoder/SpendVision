"""
Natural-language finance assistant - intent parsing and answer phrasing.

    User question
        -> LLM interprets intent (this module, parse_intent)
        -> backend retrieves/calculates actual data (app/services/query_engine.py)
        -> result passed to LLM for explanation (this module, phrase_answer)
        -> final answer

The LLM never touches the database and never generates SQL. It only maps
a question to one of a fixed set of intents, and later turns already-computed
numbers into a sentence. `parse_intent` degrades to a keyword-based parser
when no AI provider is configured, so the assistant still works without an
API key (see app/services/query_engine.py for the keyword fallback).
"""
import json
import logging
import re

from app.ai.provider import LLMProvider, AIProviderError
from app.ai.text import clean_ai_text
from app.ai.prompts import (
    QUERY_INTENT_SYSTEM_PROMPT,
    build_query_intent_user_prompt,
    QUERY_ANSWER_SYSTEM_PROMPT,
    build_query_answer_user_prompt,
)
from app.utils.constants import ALL_CATEGORY_NAMES
from app.utils.dates import is_valid_month_string

logger = logging.getLogger(__name__)

ALLOWED_INTENTS = {
    "category_spending",
    "total_spending",
    "total_income",
    "savings",
    "biggest_expense",
    "top_expenses",
    "category_change",
    "compare_months",
    "general_summary",
    "category_breakdown",
    "sorted_expenses",
    "off_topic",
}


def _validate_intent(parsed: dict) -> dict | None:
    if not isinstance(parsed, dict):
        return None
    intent = parsed.get("intent")
    if intent not in ALLOWED_INTENTS:
        return None

    category = parsed.get("category")
    if category is not None and category not in ALL_CATEGORY_NAMES:
        category = None

    month = parsed.get("month")
    if month is not None and not is_valid_month_string(str(month)):
        month = None

    compare_month = parsed.get("compare_month")
    if compare_month is not None and not is_valid_month_string(str(compare_month)):
        compare_month = None

    top_n = parsed.get("top_n")
    if not isinstance(top_n, int) or not (1 <= top_n <= 20):
        top_n = None

    sort_order = parsed.get("sort_order")
    if sort_order not in ("asc", "desc"):
        sort_order = None

    return {
        "intent": intent,
        "category": category,
        "month": month,
        "compare_month": compare_month,
        "top_n": top_n,
        "sort_order": sort_order,
    }


def parse_intent_with_ai(
    provider: LLMProvider,
    question: str,
    today: str | None = None,
    available_months: list[str] | None = None,
    recent_turns: list[dict] | None = None,
) -> dict | None:
    """Returns a validated intent dict, or None if the AI response was
    unusable (caller should fall back to the keyword parser)."""
    try:
        raw = provider.generate(
            QUERY_INTENT_SYSTEM_PROMPT,
            build_query_intent_user_prompt(question, today, available_months, recent_turns),
            max_tokens=200,
        )
        raw = raw.strip()
        if raw.startswith("```"):
            # Some models wrap JSON in a markdown fence despite instructions.
            raw = raw.strip("`").removeprefix("json").strip()
        parsed = json.loads(raw)
    except (AIProviderError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("AI intent parsing failed, using keyword fallback: %s", exc)
        return None

    return _validate_intent(parsed)


def phrase_answer(provider: LLMProvider | None, question: str, data: dict, template_answer: str) -> tuple[str, bool]:
    """Returns (answer, ai_available). Falls back to the deterministic
    template answer if no provider is configured or the call fails."""
    if provider is None:
        return template_answer, False

    try:
        answer = provider.generate(
            QUERY_ANSWER_SYSTEM_PROMPT,
            build_query_answer_user_prompt(question, data),
            max_tokens=300,
        )
        answer = _clean_answer(answer)
        if not answer:
            return template_answer, False
        return answer, True
    except AIProviderError as exc:
        logger.warning("AI answer phrasing failed, using template answer: %s", exc)
        return template_answer, False



def _clean_answer(text: str) -> str:
    return clean_ai_text(text)
