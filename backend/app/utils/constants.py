"""Shared constants."""

# The MVP runs single-tenant: every request operates against this one demo
# user. See app/utils/deps.py::get_current_user for how this is wired up,
# and the README's "Authentication" section for how to extend this to real
# multi-user auth later without touching the rest of the app.
DEMO_USER_EMAIL = "demo@financedashboard.app"

# Fixed category set. Kept as a constant (rather than admin-editable) to
# keep the MVP's scope small - see project README "Scope".
# "Other Income" is a small addition beyond the brief's illustrative list,
# so unmatched income transactions have somewhere valid to land without
# being miscategorized as an expense category.
DEFAULT_CATEGORIES = [
    ("Food", "expense"),
    ("Groceries", "expense"),
    ("Transport", "expense"),
    ("Shopping", "expense"),
    ("Entertainment", "expense"),
    ("Utilities", "expense"),
    ("Healthcare", "expense"),
    ("Education", "expense"),
    ("Rent", "expense"),
    ("Salary", "income"),
    ("Investment", "income"),
    ("Other", "expense"),
    ("Other Income", "income"),
]

EXPENSE_CATEGORY_NAMES = [n for n, t in DEFAULT_CATEGORIES if t == "expense"]
INCOME_CATEGORY_NAMES = [n for n, t in DEFAULT_CATEGORIES if t == "income"]
ALL_CATEGORY_NAMES = [n for n, _ in DEFAULT_CATEGORIES]

# Rule-based merchant -> category lookup. Matching is case-insensitive
# substring matching against the transaction description/merchant. This
# handles the common cases cheaply so we don't burn LLM calls on every
# transaction (see app/services/categorization.py).
MERCHANT_RULES: dict[str, str] = {
    "swiggy": "Food",
    "zomato": "Food",
    "dominos": "Food",
    "pizza hut": "Food",
    "mcdonald": "Food",
    "kfc": "Food",
    "starbucks": "Food",
    "cafe coffee day": "Food",
    "chai point": "Food",
    "uber": "Transport",
    "ola": "Transport",
    "rapido": "Transport",
    "indian oil": "Transport",
    "petrol": "Transport",
    "irctc": "Transport",
    "metro": "Transport",
    "netflix": "Entertainment",
    "amazon prime video": "Entertainment",
    "hotstar": "Entertainment",
    "spotify": "Entertainment",
    "bookmyshow": "Entertainment",
    "pvr": "Entertainment",
    "inox": "Entertainment",
    "amazon": "Shopping",
    "flipkart": "Shopping",
    "myntra": "Shopping",
    "ajio": "Shopping",
    "nykaa": "Shopping",
    "dmart": "Groceries",
    "bigbasket": "Groceries",
    "blinkit": "Groceries",
    "zepto": "Groceries",
    "grofers": "Groceries",
    "reliance fresh": "Groceries",
    "more supermarket": "Groceries",
    "electricity": "Utilities",
    "water bill": "Utilities",
    "broadband": "Utilities",
    "airtel": "Utilities",
    "jio": "Utilities",
    "vodafone": "Utilities",
    "gas bill": "Utilities",
    "apollo pharmacy": "Healthcare",
    "pharmeasy": "Healthcare",
    "practo": "Healthcare",
    "hospital": "Healthcare",
    "clinic": "Healthcare",
    "diagnostics": "Healthcare",
    "byju": "Education",
    "udemy": "Education",
    "coursera": "Education",
    "school fee": "Education",
    "tuition": "Education",
    "rent": "Rent",
    "landlord": "Rent",
    "salary": "Salary",
    "payroll": "Salary",
    "mutual fund": "Investment",
    "sip": "Investment",
    "zerodha": "Investment",
    "groww": "Investment",
}
