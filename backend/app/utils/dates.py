"""Small shared date helpers for month-string ("YYYY-MM") based analytics."""
import calendar
import re
from datetime import date

MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def is_valid_month_string(value: str) -> bool:
    return bool(MONTH_RE.match(value))


def current_month() -> str:
    return date.today().strftime("%Y-%m")


def previous_month(month: str) -> str:
    year, mon = (int(p) for p in month.split("-"))
    if mon == 1:
        return f"{year - 1}-12"
    return f"{year}-{mon - 1:02d}"


def month_bounds(month: str) -> tuple[date, date]:
    year, mon = (int(p) for p in month.split("-"))
    start = date(year, mon, 1)
    end = date(year, mon, calendar.monthrange(year, mon)[1])
    return start, end


# --- Month-name resolution for natural-language questions -----------------
#
# LLMs don't know "today", so a bare "august" tends to get resolved to
# whatever year the model was trained around (e.g. 2024). We resolve month
# names deterministically instead, preferring months the user actually has
# data for.

_MONTH_NAMES = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sept": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}
_NAME_ALT = "|".join(sorted(_MONTH_NAMES, key=len, reverse=True))
_NAME_THEN_YEAR = re.compile(rf"\b({_NAME_ALT})\b\.?(?:[\s,'-]*((?:19|20)\d{{2}}))?", re.IGNORECASE)
_YEAR_THEN_NAME = re.compile(rf"\b((?:19|20)\d{{2}})[\s,-]+({_NAME_ALT})\b", re.IGNORECASE)
_ISO_MONTH = re.compile(r"\b((?:19|20)\d{2})-(0[1-9]|1[0-2])\b")
# "may" is also a common verb, so only treat it as a month with a year or a
# preposition in front of it ("in may", "for may").
_MAY_AS_MONTH = re.compile(r"\b(?:in|for|of|during|since|until|from|to|and|vs|versus|about)\s+may\b|\bmay\s*,?\s*(?:19|20)\d{2}\b", re.IGNORECASE)


def _pick_year(month_num: int, available_months: list[str], today: date) -> int:
    """Best year for a month name given without a year: the most recent
    month with data, else the most recent occurrence that isn't in the future."""
    suffix = f"-{month_num:02d}"
    with_data = sorted(m for m in available_months if m.endswith(suffix))
    if with_data:
        return int(with_data[-1][:4])
    return today.year if month_num <= today.month else today.year - 1


def extract_months_from_text(
    text: str,
    available_months: list[str] | None = None,
    today: date | None = None,
) -> list[str]:
    """Returns every month mentioned in `text` as YYYY-MM, in order of appearance."""
    available_months = available_months or []
    today = today or date.today()
    found: list[tuple[int, str]] = []
    taken: list[tuple[int, int]] = []

    def overlaps(span: tuple[int, int]) -> bool:
        return any(span[0] < e and s < span[1] for s, e in taken)

    for m in _ISO_MONTH.finditer(text):
        taken.append(m.span())
        found.append((m.start(), f"{m.group(1)}-{m.group(2)}"))

    for m in _YEAR_THEN_NAME.finditer(text):
        if overlaps(m.span()):
            continue
        taken.append(m.span())
        found.append((m.start(), f"{m.group(1)}-{_MONTH_NAMES[m.group(2).lower()]:02d}"))

    for m in _NAME_THEN_YEAR.finditer(text):
        if overlaps(m.span()):
            continue
        name = m.group(1).lower()
        if name == "may" and not _MAY_AS_MONTH.search(text):
            continue
        month_num = _MONTH_NAMES[name]
        year = int(m.group(2)) if m.group(2) else _pick_year(month_num, available_months, today)
        taken.append(m.span())
        found.append((m.start(), f"{year}-{month_num:02d}"))

    found.sort()
    result: list[str] = []
    for _, month in found:
        if month not in result:
            result.append(month)
    return result


def format_month_label(month: str) -> str:
    """"2026-08" -> "August 2026"."""
    year, mon = (int(p) for p in month.split("-"))
    return f"{calendar.month_name[mon]} {year}"
