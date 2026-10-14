# SpendVision - AI Personal Finance Dashboard

A medium-scale, resume-ready web app for uploading personal transactions, visualizing spending,
and getting AI-generated financial insights. Built as a focused MVP - not a production fintech
platform.

## 1. Project Overview

SpendVision lets a user upload a CSV of their financial transactions and get a full picture of
their spending: a categorized transaction ledger, a dashboard of trends and breakdowns, month-
over-month comparisons, AI-generated observations about spending behavior, a natural-language
finance assistant, and lightweight unusual-spending detection.

The AI is not a bolted-on chatbot — every AI feature operates on the user's own computed
financial data:

- **Categorization** uses a rule-based merchant lookup first, and only falls back to an LLM for
  merchants it doesn't recognize.
- **Insights** are phrased by an LLM, but every number they reference was calculated by the
  backend beforehand — the AI explains, it doesn't calculate.
- **The "Ask AI" assistant** never writes or executes SQL. It classifies the question into a
  fixed set of intents, the backend computes the answer with predefined analytics functions,
  and (optionally) an LLM turns that result into a sentence.
- **Anomaly detection** is a plain statistical check (no LLM at all) — see section 10.

If no AI API key is configured, every AI feature still works: it falls back to deterministic,
template-based logic so the app is fully usable out of the box.

## 2. Features

- CSV upload with validation, duplicate detection, and per-row error reporting
- Hybrid (rule-based + LLM) transaction categorization
- Dashboard: income/expense/savings summary cards, spending trend chart (daily/weekly/monthly),
  category breakdown donut chart, month-over-month comparison, recent transactions, top expenses
- Searchable, filterable transaction list (date, category, type)
- AI-generated spending insights, grounded in backend-calculated statistics
- Natural-language finance assistant ("Ask AI") with a safe, non-SQL intent-based architecture
- Statistical unusual-spending (anomaly) detection

## 3. Tech Stack

**Frontend:** Next.js (App Router) + TypeScript + React + Tailwind CSS + Recharts for charts.

**Backend:** Python + FastAPI (REST API) + Pydantic (request/response validation) + SQLAlchemy
(ORM).

**Database:** PostgreSQL, with a small, purpose-built relational schema (users, categories,
transactions).

**AI:** An LLM (Groq's free tier by default; Gemini and Anthropic Claude also supported) accessed through a small provider-abstraction layer
so the vendor can be swapped later. Prompts request structured JSON output, and every response is
validated before it's trusted or stored.

**Data processing:** pandas for analytics (trends, breakdowns, comparisons, anomaly detection)
and CSV parsing, plus the Python standard library.

**Authentication:** intentionally minimal — see section 11.

## 4. Architecture

```text
                    ┌──────────────────────┐
                    │       Next.js        │
                    │     TypeScript       │
                    │      Tailwind        │
                    └──────────┬───────────┘
                               │
                            REST API
                               │
                    ┌──────────▼───────────┐
                    │       FastAPI        │
                    │        Python        │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                 │
              ▼                ▼                 ▼
        PostgreSQL         AI Service        Analytics
              │                │                 │
       Transactions        LLM API           pandas /
       Categories          Insights          algorithms
       Users               Questions
```

The backend is a single FastAPI application (no microservices). Inside it, concerns are
separated by directory: `api` (routes), `models` (SQLAlchemy), `schemas` (Pydantic), `services`
(business logic / orchestration), `ai` (LLM provider + prompts + validation), `analytics`
(pandas-based deterministic calculations), and `utils`.

## 5. Project Structure

```text
ai-finance-dashboard/
│
├── frontend/                    Next.js app
│   ├── app/                     Pages (dashboard, transactions, upload, insights, ask)
│   ├── components/              Reusable UI: layout, dashboard charts, tables, insight cards
│   ├── lib/                     API client, formatting helpers, chart color system
│   ├── hooks/                   useAsync data-fetching hook
│   ├── types/                   TypeScript types mirroring backend schemas
│   └── ...
│
├── backend/
│   ├── app/
│   │   ├── api/                 FastAPI routers (health, transactions, analytics, ai, anomalies)
│   │   ├── models/               SQLAlchemy models (User, Category, Transaction)
│   │   ├── schemas/              Pydantic request/response schemas
│   │   ├── services/             CSV import, categorization, insight/query orchestration
│   │   ├── ai/                   LLM provider abstraction, prompt templates, output validation
│   │   ├── analytics/             pandas-based summary/trend/comparison/anomaly calculations
│   │   ├── utils/                 constants, date helpers, seeding, dependencies
│   │   ├── database.py
│   │   ├── config.py
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
│
├── sample-data/
│   ├── sample_transactions.csv   ~150 realistic demo transactions across 5 months
│   └── generate_sample_data.py   (optional) script that generated the CSV above
│
├── README.md
├── .gitignore
└── docker-compose.yml            PostgreSQL only
```

## 6. Database Design

**`users`** — `id` (UUID PK), `email` (unique), `auth_identifier`, `created_at`.

**`categories`** — `id` (UUID PK), `name` (unique), `type` (`income` | `expense`), `created_at`.
Seeded automatically on startup with: Food, Groceries, Transport, Shopping, Entertainment,
Utilities, Healthcare, Education, Rent (expense), Salary, Investment, Other Income (income), and
Other (expense, catch-all).

**`transactions`** — `id` (UUID PK), `user_id` (FK → users), `transaction_date`, `description`,
`merchant`, `amount` (numeric), `transaction_type` (`income` | `expense`), `category_id`
(FK → categories, nullable), `category_confidence`, `category_source` (`rule` | `ai` |
`fallback`), `source` (`csv_upload` | `manual`), `created_at`. Indexed on `(user_id,
transaction_date)` for fast range queries and on `(user_id, transaction_date, description,
amount)` to support duplicate-import detection.

## 7. CSV Format

```csv
date,description,amount,type
2026-08-01,Swiggy,450,expense
2026-08-02,Uber,280,expense
2026-08-03,Salary,65000,income
2026-08-04,Amazon,1299,expense
```

Required columns: `date`, `description`, `amount`, `type` (`income` or `expense`; `credit`/
`debit` are also accepted and normalized). An optional `merchant` column is supported; if
omitted, `description` is used as the merchant name.

The importer validates the whole file first (correct columns, non-empty, ≤5&nbsp;MB, valid CSV),
then validates each row independently — a bad date, non-numeric amount, or invalid type fails
only that row, with a human-readable reason returned to the UI. Rows matching an existing
`(date, description, amount)` triple for the user (or a duplicate within the same file) are
skipped and counted separately, so re-uploading the same file is safe.

A ready-to-use sample file with ~150 transactions across 5 months (including a few deliberately
oversized transactions to demonstrate anomaly detection) lives at
`sample-data/sample_transactions.csv`.

## 8. AI Architecture

### Transaction categorization (hybrid)

```text
Transaction
     │
     ▼
Known merchant/rule? ──YES──► Category (confidence 1.0, source "rule")
     │
     NO
     │
     ▼
   LLM ──► validate against allowed category list/type ──► Category (source "ai")
                                                          └─ invalid/unavailable → "Other" (source "fallback")
```

`backend/app/utils/constants.py` holds a merchant → category dictionary (Swiggy → Food, Uber →
Transport, Netflix → Entertainment, DMart → Groceries, etc.). Only transactions with no rule
match are sent to the LLM, so a typical CSV import makes very few AI calls. The LLM is asked for
strict JSON (`{"category": ..., "confidence": ...}`); the response is rejected and replaced with
a safe fallback if the category isn't in the allowed list or doesn't match the transaction's
income/expense type.

### AI spending insights

The backend (`app/services/insights_data.py`) first computes a small, bounded statistics object —
current vs. previous month totals, category breakdown, notable category changes, top expenses,
savings rate. Only that object (not the raw transaction table) is sent to the LLM, which is
instructed to reference only the given numbers and to phrase suggestions as observations, never
financial advice. If no AI key is configured, or the AI response fails validation, the same
statistics feed a deterministic template that produces equivalent (if less nuanced) insights —
see `app/ai/insights.py::_template_insights`.

### Natural-language finance assistant

```text
User question
      │
      ▼
LLM interprets intent (fixed set: category_spending, total_spending, savings, top_expenses, …)
      │
      ▼
Backend retrieves/calculates actual data (predefined pandas/analytics functions — never AI-written SQL)
      │
      ▼
Result passed to the LLM to phrase a final sentence (optional — falls back to a template)
      │
      ▼
Final answer
```

The LLM never has database access and never generates SQL. `app/services/query_engine.py` maps
the parsed (and validated) intent to one of a fixed set of analytics function calls. If no AI
provider is configured, a small keyword-based parser (`keyword_parse_intent`) handles the same
set of intents well enough to answer the example questions below without any LLM call.

### Deterministic vs. AI-generated, explicitly

Every numeric figure in the app (totals, percentages, category sums) is computed in
`app/analytics/` or `app/services/` with pandas/SQL — never guessed by an LLM. The AI layer's job
is strictly to interpret and phrase those numbers, and every AI response is schema-validated
before use; invalid output always degrades to a deterministic fallback rather than surfacing bad
data or crashing the request.

## 9. Unusual Spending Detection

Implemented in `app/analytics/anomalies.py` — a plain z-score-style check, **not** an LLM. For
each expense category with at least 3 transactions, it computes the mean and standard deviation
of that category's amounts; a transaction is flagged if it's more than 2 standard deviations
above the category mean **and** above an absolute ₹1,000 floor (to avoid flagging noise in
categories with naturally tiny, low-variance spending). Each flagged transaction reports its
typical range and a plain-language reason.

## 10. Authentication

Authentication is intentionally minimal for this MVP: the app runs single-tenant against one
seeded "demo" user (`app/utils/deps.py::get_current_user`), so there's no login flow to stand up
to try the project. The `users` table and every `transactions.user_id` foreign key are already in
place, so real authentication (hashed passwords + session/JWT, or an OAuth provider) can be added
later by replacing `get_current_user` with a real session lookup — no schema changes required.

## 11. Setup Instructions

### Prerequisites

- Node.js 18+
- Python 3.11+
- PostgreSQL 14+ (or Docker, to run the provided `docker-compose.yml`)

### 1. Clone

```bash
git clone <your-fork-url> ai-finance-dashboard
cd ai-finance-dashboard
```

### 2. Start PostgreSQL

Either via Docker:

```bash
docker compose up -d
```

...or point `DATABASE_URL` (below) at your own local/managed PostgreSQL instance. No manual
schema setup is required — the backend creates tables automatically on first startup.

### 3. Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`:

```env
DATABASE_URL=postgresql://finance_user:finance_password@localhost:5432/finance_dashboard
AI_PROVIDER=groq
AI_API_KEY=your_api_key_here     # leave blank to run with deterministic AI fallbacks
AI_MODEL=openai/gpt-oss-20b
CORS_ORIGINS=http://localhost:3000
```

Get a free Groq key (no credit card) at [console.groq.com/keys](https://console.groq.com/keys). Gemini (`AI_PROVIDER=gemini`) and Anthropic (`AI_PROVIDER=anthropic`) also work - see `backend/.env.example` for model names. Leave `AI_API_KEY` blank to run on deterministic fallbacks with no AI at all.

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

The API is now at `http://localhost:8000` (interactive docs at `/docs`).

### 4. Frontend setup

```bash
cd frontend
npm install
cp .env.example .env.local
```

`frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Run the app:

```bash
npm run dev
```

Visit `http://localhost:3000`.

### 5. Load sample data

Go to the **Upload** page in the app and upload `sample-data/sample_transactions.csv`, or:

```bash
curl -F "file=@sample-data/sample_transactions.csv" http://localhost:8000/transactions/upload
```

## 12. API Documentation

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| POST | `/transactions/upload` | Upload and import a CSV file |
| GET | `/transactions` | List transactions (filters: date range, category, type, search, pagination) |
| GET | `/transactions/{id}` | Get a single transaction |
| GET | `/analytics/summary` | Income / expenses / savings / savings rate |
| GET | `/analytics/monthly` | Spending trend (`?granularity=daily\|weekly\|monthly`) |
| GET | `/analytics/categories` | Category breakdown (`?month=YYYY-MM`) |
| GET | `/analytics/comparison` | Current vs. previous month, overall and by category |
| GET | `/analytics/top-expenses` | Largest transactions for a period |
| POST | `/ai/categorize` | Categorize a single transaction description (rule + AI fallback) |
| GET | `/ai/insights` | AI-generated spending insights for a month |
| POST | `/ai/query` | Ask a natural-language question about your finances |
| GET | `/anomalies` | Unusual-spending detection results |

Full interactive documentation (request/response schemas) is available at `/docs` once the
backend is running.

## 13. How to Test the Application

1. Start Postgres, the backend, and the frontend as above.
2. On the **Upload** page, upload `sample-data/sample_transactions.csv` — you should see an
   import summary (imported/duplicate/failed counts).
3. The **Dashboard** should populate with summary cards, a spending trend chart, a category
   donut chart, a month comparison, and recent/top transactions.
4. On **Transactions**, try the search box and the category/type filters.
5. On **Insights**, confirm you see a handful of insight cards and (thanks to the sample data's
   deliberately oversized transactions) at least one flagged unusual transaction.
6. On **Ask AI**, try one of the suggested questions (e.g. "What was my biggest expense this
   month?") and confirm you get a grounded answer.
7. Re-upload the same CSV to confirm duplicate rows are skipped rather than double-imported.

There is no login step — the app opens straight to the dashboard for the single demo user.

## 14. Known Limitations

- Single-tenant only; no real authentication or multi-user support (by design — see section 10).
- Anomaly detection is a simple per-category z-score check; it doesn't account for seasonality,
  recurring-but-large expenses (e.g. annual insurance), or cross-category patterns.
- The keyword-based intent fallback (used when no AI key is configured) understands the example
  question phrasings well but is less flexible than the LLM-backed parser.
- CSV import is synchronous; very large files (near the 5&nbsp;MB cap) will block the request
  until processing finishes.
- No data export, editing, or manual transaction entry — CSV upload is the only ingestion path.

## 15. Recommended Next Improvements

- Real authentication (hashed passwords + JWT sessions), building on the existing `users` table.
- Recurring-transaction detection (e.g. flagging subscriptions automatically).
- Editable/deletable transactions and manual entry.
- Bank/UPI integrations, investment tracking, budgeting — explicitly out of scope for this MVP.
- Export (CSV/PDF) of analytics and insights.
- A second LLM provider (e.g. OpenAI) implementing the same `LLMProvider` interface, selectable
  via `AI_PROVIDER`.
