"""Post-processing for LLM text shown directly in the UI.

Prompts ask for plain text in Indian Rupees, but models don't always comply
(markdown bold, "$" amounts, "₹340.0"). Every amount in this app is in INR,
so it's safe to normalise these deterministically before display."""
import re

_DOLLAR_AMOUNT_RE = re.compile(r"(?:US)?\$\s?(?=\d)")
_INR_WORD_RE = re.compile(r"\b(?:INR|Rs\.?)\s?(?=\d)")
_ZERO_DECIMALS_RE = re.compile(r"(₹\s?[\d,]+)\.0+\b")
_LONG_PERCENT_RE = re.compile(r"(\d[\d,]*\.\d{2,})\s?%")


def _round_percent(match: re.Match) -> str:
    value = float(match.group(1).replace(",", ""))
    return f"{value:,.1f}%"


def clean_ai_text(text: str) -> str:
    text = text.replace("**", "").replace("__", "").replace("`", "")
    text = _DOLLAR_AMOUNT_RE.sub("₹", text)          # $7,811.00 -> ₹7,811.00
    text = _INR_WORD_RE.sub("₹", text)               # INR 500 / Rs. 500 -> ₹500
    text = _ZERO_DECIMALS_RE.sub(r"\1", text)        # ₹7,811.00 -> ₹7,811
    text = _LONG_PERCENT_RE.sub(_round_percent, text)  # 27.07% -> 27.1%
    return text.strip()
