"""
Orchestrates the natural-language finance assistant end to end:

    question -> intent (keyword parser; AI only if unclear) -> deterministic data lookup
             -> answer (AI phrasing or template fallback) -> saved to chat history

All actual numbers come from the analytics module (pandas over the user's
own transactions) via a fixed set of predefined functions - never from
AI-generated SQL. This is what keeps the assistant both safe (no injection
surface) and trustworthy (the LLM cannot hallucinate a number that isn't in
`data`).

Month handling: the LLM has no idea what "today" is, so a bare "august" used
to be resolved to e.g. 2024 and return all zeros. Month names in the question
are now resolved deterministically (app.utils.dates.extract_months_from_text)
against the months the user actually has data for, and that result always
wins over the LLM's guess.
"""
import re
from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.ai.provider import LLMProvider
from app.ai.query import parse_intent_with_ai, phrase_answer
from app.analytics.comparison import compute_month_comparison
from app.analytics.summary import compute_summary
from app.analytics.top_expenses import compute_top_expenses
from app.analytics.trends import compute_category_breakdown
from app.models import ChatMessage, Transaction
from app.utils.constants import ALL_CATEGORY_NAMES
from app.utils.dates import (
    current_month,
    extract_months_from_text,
    format_month_label,
    month_bounds,
    previous_month,
)

RECENT_TURNS_FOR_CONTEXT = 3


# --- Context helpers -------------------------------------------------------

def get_available_months(db: Session, user_id) -> list[str]:
    """Sorted list of YYYY-MM months in which the user has any transaction."""
    month_expr = func.to_char(Transaction.transaction_date, "YYYY-MM")
    rows = (
        db.query(month_expr)
        .filter(Transaction.user_id == user_id)
        .distinct()
        .all()
    )
    return sorted(r[0] for r in rows if r[0])


def default_month(available_months: list[str]) -> str:
    """Month to use when the question doesn't name one: the current month if
    it has data, otherwise the latest month that does."""
    now = current_month()
    if now in available_months or not available_months:
        return now
    return available_months[-1]


def get_recent_turns(db: Session, user_id, limit: int = RECENT_TURNS_FOR_CONTEXT) -> list[dict]:
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {"question": r.question, "intent_params": r.intent_params or {"intent": r.intent}}
        for r in reversed(rows)
    ]


# --- Keyword-based intent fallback (used when no AI provider is configured
# or the AI response fails validation) -----------------------------------

OFF_TOPIC_ANSWER = (
    "I can only help with questions about your finances - try asking about your spending, "
    "income, savings or a specific transaction."
)

# Used only by the no-AI keyword fallback to tell a vague-but-financial
# question ("how am I doing?") from small talk ("do you love me").
_FINANCE_SIGNAL_RE = re.compile(
    r"\b(money|cash|spend\w*|spent|expense\w*|income|earn\w*|salary|sav(e|ed|es|ing|ings)|budget|"
    r"transaction\w*|financ\w*|categor\w*|cost\w*|paid|pay\w*|bill\w*|buy|bought|purchase\w*|"
    r"shop\w*|order\w*|summary|overview|doing|afford\w*|amount|total|how much|month\w*|week\w*|year\w*|"
    r"rupee\w*|inr|balance)\b|₹",
    re.IGNORECASE,
)

# "Which category increased the most?" is a change question, but "which
# category did I spend the most on?" is a breakdown question - only words
# about growth/decline make it a change question.
_CHANGE_RE = re.compile(r"\b(increas\w*|decreas\w*|grew|grow\w*|rose|rise|rising|jump\w*|chang\w*|drop\w*|fell|fall\w*|went up|went down)\b")
_SUPERLATIVE_RE = re.compile(r"\b(most|least|highest|lowest|biggest|largest|smallest|max\w*|min\w*)\b")
_WHERE_CATEGORY_RE = re.compile(r"\b(where|categor\w*|area\w*|on what|which thing)\b")
_BREAKDOWN_RE = re.compile(r"\b(breakdown|break down|by category|per category|each category|split)\b")

# "Arrange/sort/list my expenses in ascending/descending order".
_SORT_RE = re.compile(r"\b(descending|ascending|sort\w*|arrange\w*|order(ed)?|rank\w*|high(est)? to low(est)?|"
                      r"low(est)? to high(est)?|large(st)? to small(est)?|small(est)? to large(st)?|"
                      r"big(gest)? to small(est)?|small(est)? to big(gest)?)\b")
_ASCENDING_RE = re.compile(r"\b(ascending|low(est)? to high(est)?|small(est)? to (large|big)(st|gest)?|cheapest first|smallest first)\b")
_EXPENSE_LIST_RE = re.compile(r"\b(expense\w*|spend\w*|spent|transaction\w*|purchase\w*|payment\w*)\b")
SORTED_LIST_LIMIT = 20

_FOLLOW_UP_RE = re.compile(r"^\s*(what about|how about|and|what of|same for|now|ok(ay)?,? (what about|and))\b", re.IGNORECASE)


def _guess_category(question: str) -> str | None:
    q = question.lower()
    for name in ALL_CATEGORY_NAMES:
        if name.lower() in q:
            return name
    return None


def _relative_month(question: str) -> str | None:
    q = question.lower()
    if "last month" in q or "previous month" in q:
        return previous_month(current_month())
    if "this month" in q or "current month" in q:
        return current_month()
    return None


def _guess_top_n(question: str) -> int | None:
    match = re.search(r"\btop\s+(\d{1,2})\b", question.lower())
    if match:
        n = int(match.group(1))
        return n if 1 <= n <= 20 else None
    return None


def keyword_parse_intent(
    question: str,
    available_months: list[str] | None = None,
    recent_turns: list[dict] | None = None,
) -> dict:
    q = question.lower()
    category = _guess_category(question)
    months = extract_months_from_text(question, available_months)
    month = months[0] if months else _relative_month(question)
    compare_month = None
    top_n = _guess_top_n(question)

    if "compare" in q or " vs " in q or "versus" in q:
        intent = "compare_months"
        if len(months) >= 2:
            month, compare_month = months[0], months[1]
        elif len(months) == 1:
            month = months[0]
        else:
            # "Compare with last month" describes the comparison target, not
            # the primary period - leave the anchor to the default month so
            # the comparison is latest vs. the month before it.
            month = None
    elif _SORT_RE.search(q) and _EXPENSE_LIST_RE.search(q) and "categor" not in q:
        intent = "sorted_expenses"
    elif _CHANGE_RE.search(q) and ("categor" in q or category is not None):
        intent = "category_change"
    elif _BREAKDOWN_RE.search(q) or (_SUPERLATIVE_RE.search(q) and _WHERE_CATEGORY_RE.search(q)):
        intent = "category_breakdown"
    elif top_n or "top" in q:
        intent = "top_expenses"
    elif "biggest" in q or "largest" in q:
        intent = "biggest_expense"
    elif "save" in q or "savings" in q or "saved" in q:
        intent = "savings"
    elif "income" in q or "earn" in q or "salary" in q:
        intent = "total_income"
    elif category is not None:
        intent = "category_spending"
    elif "spend" in q or "spent" in q or "expense" in q or "expenditure" in q:
        intent = "total_spending"
    else:
        is_follow_up = bool(recent_turns and _FOLLOW_UP_RE.search(question))
        if not is_follow_up and not months and not _FINANCE_SIGNAL_RE.search(question):
            intent = "off_topic"
        else:
            intent = "general_summary"

    sort_order = ("asc" if _ASCENDING_RE.search(q) else "desc") if intent == "sorted_expenses" else None
    parsed = {"intent": intent, "category": category, "month": month, "compare_month": compare_month,
              "top_n": top_n, "sort_order": sort_order}

    # Follow-ups like "what about august?" or "and food?" inherit the previous
    # question's intent and only change what the user changed.
    if intent in ("general_summary", "category_spending") and recent_turns and _FOLLOW_UP_RE.search(question):
        prev = dict(recent_turns[-1].get("intent_params") or {})
        if prev.get("intent") and prev["intent"] != "off_topic":
            if intent == "category_spending" and prev["intent"] not in ("category_spending", "category_change"):
                prev["intent"] = "category_spending"
            parsed = {
                "intent": prev["intent"],
                "category": category or prev.get("category"),
                "month": month or prev.get("month"),
                "compare_month": compare_month if month else prev.get("compare_month"),
                "top_n": top_n or prev.get("top_n"),
                "sort_order": prev.get("sort_order"),
            }

    return parsed


def _apply_explicit_months(intent_data: dict, question: str, available_months: list[str]) -> dict:
    """Month names typed by the user override whatever year the LLM guessed."""
    months = extract_months_from_text(question, available_months)
    if not months:
        return intent_data
    fixed = dict(intent_data)
    fixed["month"] = months[0]
    if fixed["intent"] == "compare_months":
        fixed["compare_month"] = months[1] if len(months) > 1 else None
    return fixed


# --- Deterministic data retrieval, one predefined function per intent ----

def execute_intent(db: Session, user_id, intent_data: dict, available_months: list[str] | None = None) -> dict:
    available_months = available_months or []
    intent = intent_data["intent"]
    month = intent_data.get("month") or default_month(available_months)
    base = {
        "month": month,
        "month_label": format_month_label(month),
        "has_data_for_month": month in available_months,
        "months_with_data": [format_month_label(m) for m in available_months],
    }

    if intent == "category_spending":
        category = intent_data.get("category")
        breakdown = compute_category_breakdown(db, user_id, month)
        amount = next((i["amount"] for i in breakdown["items"] if i["category"] == category), 0.0)
        return {**base, "category": category, "amount": amount}

    if intent == "total_spending":
        start, end = month_bounds(month)
        summary = compute_summary(db, user_id, start, end)
        return {**base, "total_expenses": summary["total_expenses"]}

    if intent == "total_income":
        start, end = month_bounds(month)
        summary = compute_summary(db, user_id, start, end)
        return {**base, "total_income": summary["total_income"]}

    if intent == "savings":
        start, end = month_bounds(month)
        summary = compute_summary(db, user_id, start, end)
        return {
            **base,
            "total_income": summary["total_income"],
            "total_expenses": summary["total_expenses"],
            "total_savings": summary["total_savings"],
            "savings_rate": summary["savings_rate"],
        }

    if intent == "biggest_expense":
        top = compute_top_expenses(db, user_id, month, limit=1)
        return {**base, "transaction": top["items"][0] if top["items"] else None}

    if intent == "top_expenses":
        n = intent_data.get("top_n") or 5
        top = compute_top_expenses(db, user_id, month, limit=n)
        return {**base, "count": n, "items": top["items"]}

    if intent == "category_change":
        comparison = compute_month_comparison(db, user_id, month)
        category = intent_data.get("category")
        changes = comparison["category_changes"]
        prev = comparison["previous_month"]
        prev_info = {"previous_month": prev, "previous_month_label": format_month_label(prev) if prev else None}
        if category:
            match = next((c for c in changes if c["category"] == category), None)
            return {**base, **prev_info, "change": match}
        with_change = [c for c in changes if c["change_percent"] is not None]
        biggest = max(with_change, key=lambda c: abs(c["change_percent"])) if with_change else None
        return {**base, **prev_info, "change": biggest}

    if intent == "compare_months":
        month_a = month
        month_b = intent_data.get("compare_month") or previous_month(month_a)
        start_a, end_a = month_bounds(month_a)
        start_b, end_b = month_bounds(month_b)
        summary_a = compute_summary(db, user_id, start_a, end_a)
        summary_b = compute_summary(db, user_id, start_b, end_b)
        return {
            **base,
            "month_a": month_a,
            "month_a_label": format_month_label(month_a),
            "month_b": month_b,
            "month_b_label": format_month_label(month_b),
            "expenses_a": summary_a["total_expenses"],
            "expenses_b": summary_b["total_expenses"],
            "income_a": summary_a["total_income"],
            "income_b": summary_b["total_income"],
        }

    if intent == "sorted_expenses":
        order = intent_data.get("sort_order") or "desc"
        category = intent_data.get("category")
        items = compute_top_expenses(db, user_id, month, limit=10_000)["items"]  # all, highest first
        if category:
            items = [i for i in items if i["category"] == category]
        if order == "asc":
            items = list(reversed(items))
        return {
            **base,
            "sort_order": order,
            "category": category,
            "count": len(items),
            "total": round(sum(i["amount"] for i in items), 2),
            "items": items[:SORTED_LIST_LIMIT],
        }

    if intent == "category_breakdown":
        breakdown = compute_category_breakdown(db, user_id, month)
        items = breakdown["items"]  # ranked highest -> lowest spend
        return {
            **base,
            "total_expenses": breakdown["total_expenses"],
            "categories": items,
            "highest": items[0] if items else None,
            "lowest": items[-1] if items else None,
        }

    # general_summary fallback
    start, end = month_bounds(month)
    summary = compute_summary(db, user_id, start, end)
    breakdown = compute_category_breakdown(db, user_id, month)
    return {**base, "summary": summary, "top_categories": breakdown["items"][:3]}


# --- Template answers (used when no AI provider is available) ------------

def _no_data_answer(data: dict) -> str:
    available = data.get("months_with_data") or []
    if not available:
        return "You don't have any transactions yet. Upload a statement to get started."
    return (
        f"There are no transactions for {data['month_label']}. "
        f"You have data for: {', '.join(available)}."
    )


def _short_date(iso: str) -> str:
    try:
        return date.fromisoformat(iso).strftime("%d %b")
    except ValueError:
        return iso


def _template_answer(intent_data: dict, data: dict) -> str:
    intent = intent_data["intent"]
    label = data.get("month_label", data.get("month"))

    if intent == "compare_months":
        diff = data["expenses_a"] - data["expenses_b"]
        direction = "more" if diff > 0 else "less"
        return (
            f"You spent ₹{data['expenses_a']:,.0f} in {data['month_a_label']} versus "
            f"₹{data['expenses_b']:,.0f} in {data['month_b_label']} - that's ₹{abs(diff):,.0f} {direction}."
        )

    if not data.get("has_data_for_month", True):
        return _no_data_answer(data)

    if intent == "category_spending":
        if not data.get("category"):
            return f"I couldn't tell which category you meant. Try e.g. \"How much did I spend on Food in {label}?\""
        return f"You spent ₹{data['amount']:,.0f} on {data['category']} in {label}."

    if intent == "total_spending":
        return f"Your total expenses in {label} were ₹{data['total_expenses']:,.0f}."

    if intent == "total_income":
        return f"Your total income in {label} was ₹{data['total_income']:,.0f}."

    if intent == "savings":
        return (
            f"In {label}, you earned ₹{data['total_income']:,.0f} and spent "
            f"₹{data['total_expenses']:,.0f}, saving ₹{data['total_savings']:,.0f} "
            f"({data['savings_rate']:.1f}% savings rate)."
        )

    if intent == "biggest_expense":
        t = data.get("transaction")
        if not t:
            return f"No expenses found for {label}."
        return f"Your biggest expense in {label} was {t['description']} at ₹{t['amount']:,.0f}."

    if intent == "top_expenses":
        items = data.get("items", [])
        if not items:
            return f"No expenses found for {label}."
        lines = [f"{i+1}. {it['description']} - ₹{it['amount']:,.0f}" for i, it in enumerate(items)]
        return f"Your top {len(items)} expenses in {label}:\n" + "\n".join(lines)

    if intent == "category_change":
        change = data.get("change")
        if not change or change["change_percent"] is None:
            return f"There isn't enough data to compare category changes for {label}."
        direction = "increased" if change["change_percent"] > 0 else "decreased"
        return (
            f"{change['category']} {direction} {abs(change['change_percent']):.1f}% in {label} "
            f"vs {data.get('previous_month_label')} "
            f"(₹{change['previous_amount']:,.0f} → ₹{change['current_amount']:,.0f})."
        )

    if intent == "sorted_expenses":
        items = data.get("items", [])
        what = f"{data['category']} expenses" if data.get("category") else "expenses"
        if not items:
            return f"No {what} found for {label}."
        direction = "lowest to highest" if data.get("sort_order") == "asc" else "highest to lowest"
        lines = [
            f"{n}. {it['merchant'] or it['description']} ({it['category']}, {_short_date(it['transaction_date'])}) - ₹{it['amount']:,.0f}"
            for n, it in enumerate(items, start=1)
        ]
        text = f"Your {what} in {label}, {direction}:\n" + "\n".join(lines)
        if data["count"] > len(items):
            text += f"\n...and {data['count'] - len(items)} more."
        return text + f"\nTotal: ₹{data['total']:,.0f} across {data['count']} {'expense' if data['count'] == 1 else 'expenses'}."

    if intent == "category_breakdown":
        hi, lo = data.get("highest"), data.get("lowest")
        if not hi:
            return f"No expenses found for {label}."
        if hi["category"] == lo["category"]:
            return f"In {label}, all your spending was on {hi['category']} (₹{hi['amount']:,.0f})."
        return (
            f"In {label}, you spent the most on {hi['category']} (₹{hi['amount']:,.0f}, {hi['percent']:.1f}% of expenses) "
            f"and the least on {lo['category']} (₹{lo['amount']:,.0f})."
        )

    summary = data.get("summary", {})
    return (
        f"In {label}, you earned ₹{summary.get('total_income', 0):,.0f} and spent "
        f"₹{summary.get('total_expenses', 0):,.0f}, saving ₹{summary.get('total_savings', 0):,.0f} "
        f"across {summary.get('transaction_count', 0)} transactions."
    )


# --- Entry points ----------------------------------------------------------

def run_query(db: Session, user_id, provider: LLMProvider | None, question: str) -> dict:
    available_months = get_available_months(db, user_id)
    recent_turns = get_recent_turns(db, user_id)

    # The fast local keyword parser goes first. Only when it can't tell what
    # the user means (general_summary) do we spend an extra LLM round-trip on
    # intent parsing - so common questions cost one LLM call (the final
    # phrasing) instead of two, roughly halving response time.
    intent_data = keyword_parse_intent(question, available_months, recent_turns)
    # The keyword "off_topic" guess is only a heuristic - with an AI provider
    # available, let the LLM make that call too.
    if provider is not None and intent_data["intent"] in ("general_summary", "off_topic"):
        ai_intent = parse_intent_with_ai(
            provider,
            question,
            today=date.today().isoformat(),
            available_months=available_months,
            recent_turns=recent_turns,
        )
        if ai_intent is not None:
            intent_data = _apply_explicit_months(ai_intent, question, available_months)

    if intent_data["intent"] == "off_topic":
        # Small talk / non-finance questions get one fixed sentence: no data
        # lookup and no LLM phrasing call, so it's instant and can't drift.
        data = {"month": default_month(available_months)}
        answer, ai_available = OFF_TOPIC_ANSWER, provider is not None
        return _save_and_serialize(db, user_id, question, answer, intent_data, data, ai_available)

    data = execute_intent(db, user_id, intent_data, available_months)
    template = _template_answer(intent_data, data)

    # When there is simply no data for the period, the deterministic message
    # is clearer than anything the LLM would phrase from a pile of zeros.
    if intent_data["intent"] != "compare_months" and not data.get("has_data_for_month", True):
        answer, ai_available = template, provider is not None
    elif intent_data["intent"] == "sorted_expenses":
        # A ranked list must come back exactly as computed - LLM phrasing
        # could re-order, merge or drop rows - so it skips the AI call.
        answer, ai_available = template, provider is not None
    else:
        answer, ai_available = phrase_answer(provider, question, data, template)

    return _save_and_serialize(db, user_id, question, answer, intent_data, data, ai_available)


def _save_and_serialize(db: Session, user_id, question: str, answer: str, intent_data: dict, data: dict,
                        ai_available: bool) -> dict:
    resolved = {**intent_data, "month": data["month"]}
    message = ChatMessage(
        user_id=user_id,
        question=question,
        answer=answer,
        intent=intent_data["intent"],
        intent_params=resolved,
        data=data,
        ai_available=ai_available,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return serialize_message(message)


def serialize_message(message: ChatMessage) -> dict:
    return {
        "id": str(message.id),
        "question": message.question,
        "intent": message.intent,
        "data": message.data or {},
        "answer": message.answer,
        "ai_available": message.ai_available,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def list_history(db: Session, user_id, limit: int = 100) -> list[dict]:
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
        .all()
    )
    return [serialize_message(r) for r in reversed(rows)]


def clear_history(db: Session, user_id) -> int:
    deleted = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete()
    db.commit()
    return deleted
