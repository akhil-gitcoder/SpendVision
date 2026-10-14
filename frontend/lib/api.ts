import type {
  AnomalyResponse,
  CategoryBreakdownResponse,
  InsightsResponse,
  MonthComparisonResponse,
  MonthlyTrendResponse,
  QueryResponse,
  QueryHistoryResponse,
  SummaryResponse,
  TopExpensesResponse,
  TransactionListResponse,
  UploadResponse,
} from "@/types";

const API_BASE_URL = "/api";

export interface AuthUser {
  id: string;
  email: string;
  created_at: string;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

function sessionExpired(path: string, status: number) {
  if (
    status === 401 &&
    !path.startsWith("/auth/") &&
    typeof window !== "undefined"
  ) {
    window.dispatchEvent(
      new Event("spendvision:session-expired")
    );
  }
}

async function request<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        ...(options?.body &&
        !(options.body instanceof FormData)
          ? { "Content-Type": "application/json" }
          : {}),
        ...options?.headers,
      },
    });
  } catch {
    throw new ApiError(
      "Could not reach the backend server. Make sure the API is running.",
      0
    );
  }

  if (!response.ok) {
    sessionExpired(path, response.status);

    let detail = `Request failed (${response.status})`;

    try {
      const body = await response.json();

      if (body?.detail) {
        detail =
          typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body.detail);
      }
    } catch {
      // Keep the default message if the response is not JSON.
    }

    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export interface TransactionFilters {
  start_date?: string;
  end_date?: string;
  category?: string;
  transaction_type?: "income" | "expense";
  search?: string;
  page?: number;
  page_size?: number;
}

function buildQuery(
  params: Record<string, string | number | undefined>
): string {
  const search = new URLSearchParams();

  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }

  const query = search.toString();
  return query ? `?${query}` : "";
}

export const api = {
  me: () => request<AuthUser>("/auth/me"),

  signup: (email: string, password: string) =>
    request<AuthUser>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  login: (email: string, password: string) =>
    request<AuthUser>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  logout: () =>
    request<void>("/auth/logout", {
      method: "POST",
    }),

  health: () =>
    request<{ status: string }>("/health"),

  uploadTransactions: async (
    file: File
  ): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    return request<UploadResponse>(
      "/transactions/upload",
      {
        method: "POST",
        body: formData,
      }
    );
  },

  uploadTransactionsWithProgress: (
    file: File,
    onProgress: (percent: number) => void
  ): Promise<UploadResponse> => {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append("file", file);

      const xhr = new XMLHttpRequest();

      xhr.open(
        "POST",
        `${API_BASE_URL}/transactions/upload`
      );

      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) {
          onProgress(
            Math.round(
              (event.loaded / event.total) * 100
            )
          );
        }
      };

      xhr.onload = () => {
        let body:
          | (Partial<UploadResponse> & {
              detail?: unknown;
            })
          | null = null;

        try {
          body = JSON.parse(xhr.responseText);
        } catch {
          // Handle an invalid response below.
        }

        if (
          xhr.status >= 200 &&
          xhr.status < 300 &&
          body
        ) {
          resolve(body as UploadResponse);
        } else {
          sessionExpired(
            "/transactions/upload",
            xhr.status
          );

          reject(
            new ApiError(
              typeof body?.detail === "string"
                ? body.detail
                : "Upload failed. Please check the file and try again.",
              xhr.status
            )
          );
        }
      };

      xhr.onerror = () => {
        reject(
          new ApiError(
            "Could not reach the backend server.",
            0
          )
        );
      };

      xhr.send(formData);
    });
  },

  listTransactions: (
    filters: TransactionFilters = {}
  ) =>
    request<TransactionListResponse>(
      `/transactions${buildQuery({ ...filters })}`
    ),

  getSummary: (
    params: {
      start_date?: string;
      end_date?: string;
    } = {}
  ) =>
    request<SummaryResponse>(
      `/analytics/summary${buildQuery(params)}`
    ),

  getMonthlyTrend: (
    granularity:
      | "daily"
      | "weekly"
      | "monthly" = "monthly"
  ) =>
    request<MonthlyTrendResponse>(
      `/analytics/monthly${buildQuery({
        granularity,
      })}`
    ),

  getCategoryBreakdown: (month?: string) =>
    request<CategoryBreakdownResponse>(
      `/analytics/categories${buildQuery({ month })}`
    ),

  getMonthComparison: (month?: string) =>
    request<MonthComparisonResponse>(
      `/analytics/comparison${buildQuery({ month })}`
    ),

  getTopExpenses: (
    month?: string,
    limit = 5
  ) =>
    request<TopExpensesResponse>(
      `/analytics/top-expenses${buildQuery({
        month,
        limit,
      })}`
    ),

  getInsights: (month?: string) =>
    request<InsightsResponse>(
      `/ai/insights${buildQuery({ month })}`
    ),

  getAnomalies: () =>
    request<AnomalyResponse>("/anomalies"),

  askQuery: (question: string) =>
    request<QueryResponse>("/ai/query", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  getQueryHistory: (limit = 100) =>
    request<QueryHistoryResponse>(`/ai/query/history${buildQuery({ limit })}`),

  clearQueryHistory: () =>
    request<{ deleted: number }>("/ai/query/history", { method: "DELETE" }),
};