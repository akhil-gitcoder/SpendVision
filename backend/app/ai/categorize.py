"""AI-based categorization fallback, used only when the rule-based layer
(app/services/categorization.py) doesn't recognize the merchant."""
import json
import logging

from app.ai.provider import LLMProvider, AIProviderError
from app.ai.prompts import (
    CATEGORIZE_SYSTEM_PROMPT,
    build_categorize_user_prompt,
)
from app.utils.constants import ALL_CATEGORY_NAMES, EXPENSE_CATEGORY_NAMES, INCOME_CATEGORY_NAMES

logger = logging.getLogger(__name__)

DEFAULT_EXPENSE_FALLBACK = "Other"
DEFAULT_INCOME_FALLBACK = "Other Income"


def _fallback(transaction_type: str) -> dict:
    category = DEFAULT_INCOME_FALLBACK if transaction_type == "income" else DEFAULT_EXPENSE_FALLBACK
    return {"category": category, "confidence": 0.3, "source": "fallback"}


def ai_categorize(
    provider: LLMProvider | None,
    description: str,
    merchant: str | None,
    amount: float | None,
    transaction_type: str,
) -> dict:
    """Returns {"category": str, "confidence": float, "source": "ai"|"fallback"}.

    Never raises: any provider/parsing failure degrades to a safe fallback
    category so a bad AI response can never break a CSV import.
    """
    if provider is None:
        return _fallback(transaction_type)

    try:
        raw = provider.generate(
            CATEGORIZE_SYSTEM_PROMPT,
            build_categorize_user_prompt(description, merchant, amount),
            max_tokens=100,
        )
        parsed = json.loads(raw)
    except (AIProviderError, json.JSONDecodeError, ValueError) as exc:
        logger.warning("AI categorization failed, using fallback: %s", exc)
        return _fallback(transaction_type)

    category = parsed.get("category")
    confidence = parsed.get("confidence")

    # --- output validation: never trust the LLM blindly ---
    if category not in ALL_CATEGORY_NAMES:
        logger.warning("AI returned unknown category %r, using fallback", category)
        return _fallback(transaction_type)

    allowed_for_type = INCOME_CATEGORY_NAMES if transaction_type == "income" else EXPENSE_CATEGORY_NAMES
    if category not in allowed_for_type:
        # Category exists but doesn't match the transaction's income/expense type.
        return _fallback(transaction_type)

    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
        confidence = 0.5

    return {"category": category, "confidence": float(confidence), "source": "ai"}
