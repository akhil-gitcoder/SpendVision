// Types mirror the backend's Pydantic response schemas
// (see backend/app/schemas/*.py) so the frontend and API stay in sync.

export interface Category {
  id: string;
  name: string;
  type: "income" | "expense";
}

export interface Transaction {
  id: string;
  transaction_date: string;
  description: string;
  merchant: string | null;
  amount: number;
  transaction_type: "income" | "expense";
  category: Category | null;
  category_confidence: number | null;
  category_source: string | null;
  source: string;
  created_at: string;
}

export interface TransactionListResponse {
  total: number;
  page: number;
  page_size: number;
  items: Transaction[];
}

export interface UploadRowError {
  row_number: number;
  reason: string;
}

export interface UploadResponse {
  filename: string;
  total_rows: number;
  imported_count: number;
  duplicate_count: number;
  failed_count: number;
  errors: UploadRowError[];
}

export interface SummaryResponse {
  total_income: number;
  total_expenses: number;
  total_savings: number;
  savings_rate: number;
  period_start: string | null;
  period_end: string | null;
  transaction_count: number;
}

export interface MonthlyPoint {
  period: string;
  income: number;
  expenses: number;
}

export interface MonthlyTrendResponse {
  granularity: string;
  points: MonthlyPoint[];
}

export interface CategoryBreakdownItem {
  category: string;
  amount: number;
  percent: number;
}

export interface CategoryBreakdownResponse {
  total_expenses: number;
  items: CategoryBreakdownItem[];
}

export interface CategoryChangeItem {
  category: string;
  current_amount: number;
  previous_amount: number;
  change_percent: number | null;
}

export interface MonthComparisonResponse {
  current_month: string;
  previous_month: string;
  current_total: number;
  previous_total: number;
  change_percent: number | null;
  category_changes: CategoryChangeItem[];
}

export interface TopExpenseItem {
  id: string;
  transaction_date: string;
  description: string;
  merchant: string | null;
  category: string | null;
  amount: number;
}

export interface TopExpensesResponse {
  items: TopExpenseItem[];
}

export interface AnomalyItem {
  transaction_id: string;
  transaction_date: string;
  description: string;
  merchant: string | null;
  category: string | null;
  amount: number;
  typical_range_low: number;
  typical_range_high: number;
  reason: string;
}

export interface AnomalyResponse {
  anomalies: AnomalyItem[];
}

export interface InsightItem {
  title: string;
  detail: string;
  severity: "info" | "positive" | "warning";
}

export interface InsightsResponse {
  generated_at: string;
  stats: Record<string, unknown>;
  insights: InsightItem[];
  ai_available: boolean;
}

export interface QueryResponse {
  id?: string;
  question: string;
  intent: string;
  data: Record<string, unknown>;
  answer: string;
  ai_available: boolean;
  created_at?: string | null;
}

export interface QueryHistoryResponse {
  items: QueryResponse[];
}
