"""
Hybrid transaction categorization.

    Transaction -> known merchant/rule? --YES--> category
                                        --NO---> LLM -> category

The rule layer is a simple case-insensitive substring match against a
merchant->category dictionary (app/utils/constants.MERCHANT_RULES). Only
transactions that don't match any rule are sent to the LLM, so the vast
majority of a CSV import never touches the AI provider at all.
"""
from app.ai.categorize import ai_categorize
from app.ai.provider import LLMProvider
from app.utils.constants import MERCHANT_RULES


def match_rule(description: str, merchant: str | None) -> str | None:
    haystack = f"{description or ''} {merchant or ''}".lower()
    for keyword, category in MERCHANT_RULES.items():
        if keyword in haystack:
            return category
    return None


def categorize_transaction(
    provider: LLMProvider | None,
    description: str,
    merchant: str | None,
    amount: float | None,
    transaction_type: str,
) -> dict:
    """Returns {"category": str, "confidence": float, "source": "rule"|"ai"|"fallback"}."""
    rule_category = match_rule(description, merchant)
    if rule_category is not None:
        return {"category": rule_category, "confidence": 1.0, "source": "rule"}

    return ai_categorize(provider, description, merchant, amount, transaction_type)
