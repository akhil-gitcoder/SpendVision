import { ApiError } from "@/lib/api";

export interface UploadedDocument {
  id: string;
  month: string;
  filename: string;
  size_bytes: number;
  total_rows: number;
  imported_count: number;
  duplicate_count: number;
  failed_count: number;
  uploaded_at: string;
}

export interface SavedUpload extends UploadedDocument {
  errors: { row_number: number; reason: string }[];
}

export interface UploadPreview {
  document: SavedUpload;
  columns: string[];
  rows: string[][];
  has_more: boolean;
}

const BASE = "/api/transactions/uploads";

function fail(status: number, body: unknown): ApiError {
  if (status === 401) window.dispatchEvent(new Event("spendvision:session-expired"));
  const detail = body && typeof body === "object" && "detail" in body ? body.detail : null;
  return new ApiError(typeof detail === "string" ? detail : "Could not process this request. Please try again.", status);
}

async function get<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { credentials: "same-origin", cache: "no-store" });
  } catch {
    throw new ApiError("Could not reach the server.", 0);
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) throw fail(response.status, body);
  if (body === null) throw new ApiError("The server returned an invalid response.", response.status);
  return body as T;
}

export const uploadDocuments = {
  list: (year: number) => get<UploadedDocument[]>(`${BASE}?year=${year}`),
  preview: (id: string) => get<UploadPreview>(`${BASE}/${encodeURIComponent(id)}/preview`),
  downloadUrl: (id: string) => `${BASE}/${encodeURIComponent(id)}/download`,
    remove: async (
    id: string
  ): Promise<{ deleted_transactions: number }> => {
    let response: Response;

    try {
      response = await fetch(
        `${BASE}/${encodeURIComponent(id)}`,
        {
          method: "DELETE",
          credentials: "same-origin",
          cache: "no-store",
        }
      );
    } catch {
      throw new ApiError(
        "Could not reach the server. Refresh the file list before retrying.",
        0
      );
    }

    const body = await response.json().catch(() => null);

    if (!response.ok) {
      throw fail(response.status, body);
    }

    if (typeof body?.deleted_transactions !== "number") {
      throw new ApiError(
        "Unexpected response. Refresh the file list to check the result.",
        response.status
      );
    }

    return body;
  },
  save: (file: File, month: string, onProgress: (value: number) => void) =>
    new Promise<SavedUpload>((resolve, reject) => {
      const body = new FormData();
      body.append("file", file);
      body.append("month", month);
      const xhr = new XMLHttpRequest();
      xhr.open("POST", BASE);
      xhr.timeout = 120000;
      xhr.upload.onprogress = (event) => {
        if (event.lengthComputable) onProgress(Math.round(event.loaded / event.total * 100));
      };
      xhr.onload = () => {
        let result: unknown;
        try { result = JSON.parse(xhr.responseText); } catch { result = null; }
        if (xhr.status >= 200 && xhr.status < 300 && result) resolve(result as SavedUpload);
        else reject(fail(xhr.status, result));
      };
      xhr.onerror = () => reject(new ApiError("Could not reach the server.", 0));
      xhr.ontimeout = () => reject(new ApiError("The request timed out. Refresh the saved-file list before retrying.", 0));
      xhr.send(body);
    }),
};