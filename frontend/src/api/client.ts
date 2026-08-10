import type {
  ApiConfig,
  ColumnMapping,
  ComparisonResult,
  InspectionResult,
  ReportFormat,
  ValidationResult,
  ValidationSummary,
} from "../types/api";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const API_ROOT = `${API_BASE_URL}/api/v1`;
const TOKEN_STORAGE_KEY = "eav_api_token";

export function getStoredApiToken(): string {
  try {
    return window.localStorage.getItem(TOKEN_STORAGE_KEY) ?? "";
  } catch {
    // Storage can be unavailable (private browsing, blocked cookies).
    return "";
  }
}

export function setStoredApiToken(token: string): void {
  try {
    if (token) {
      window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
    } else {
      window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
  } catch {
    // Without storage the token simply does not survive a reload.
  }
}

function authHeaders(): Record<string, string> {
  // The backend ignores the header on open deployments, so it is safe to
  // send whenever a token is stored.
  const token = getStoredApiToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export class ApiError extends Error {
  readonly status: number;
  readonly details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function parseError(response: Response): Promise<ApiError> {
  let details: unknown;

  try {
    details = await response.json();
  } catch {
    details = undefined;
  }

  const detail =
    typeof details === "object" &&
    details !== null &&
    "detail" in details &&
    typeof details.detail === "string"
      ? details.detail
      : undefined;

  return new ApiError(
    detail || `The request failed with status ${response.status}.`,
    response.status,
    details,
  );
}

async function requestJson<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...init,
    // The session cookie scopes stored runs to this browser session.
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...authHeaders(),
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw await parseError(response);
  }

  return (await response.json()) as T;
}

export const api = {
  getConfig(signal?: AbortSignal): Promise<ApiConfig> {
    return requestJson<ApiConfig>("/config", { signal });
  },

  listValidations(signal?: AbortSignal): Promise<ValidationSummary[]> {
    return requestJson<ValidationSummary[]>("/validations", { signal });
  },

  getValidation(id: string, signal?: AbortSignal): Promise<ValidationResult> {
    return requestJson<ValidationResult>(
      `/validations/${encodeURIComponent(id)}`,
      { signal },
    );
  },

  createValidation(
    file: File,
    mapping?: ColumnMapping,
    signal?: AbortSignal,
  ): Promise<ValidationResult> {
    const body = new FormData();
    body.append("file", file);
    if (mapping && Object.keys(mapping).length > 0) {
      body.append("mapping", JSON.stringify(mapping));
    }

    return requestJson<ValidationResult>("/validations", {
      method: "POST",
      body,
      signal,
    });
  },

  createInspection(
    file: File,
    signal?: AbortSignal,
  ): Promise<InspectionResult> {
    const body = new FormData();
    body.append("file", file);

    return requestJson<InspectionResult>("/inspections", {
      method: "POST",
      body,
      signal,
    });
  },

  createComparison(
    beforeFile: File,
    afterFile: File,
    signal?: AbortSignal,
  ): Promise<ComparisonResult> {
    const body = new FormData();
    body.append("before_file", beforeFile);
    body.append("after_file", afterFile);

    return requestJson<ComparisonResult>("/comparisons", {
      method: "POST",
      body,
      signal,
    });
  },

  reportUrl(validationId: string, format: ReportFormat): string {
    return `${API_ROOT}/validations/${encodeURIComponent(validationId)}/report.${format}`;
  },

  async downloadReport(
    validationId: string,
    format: ReportFormat,
  ): Promise<Blob> {
    const response = await fetch(this.reportUrl(validationId, format), {
      credentials: "include",
      headers: {
        Accept:
          format === "pdf"
            ? "application/pdf"
            : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ...authHeaders(),
      },
    });

    if (!response.ok) {
      throw await parseError(response);
    }

    return response.blob();
  },
};

export function getErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof TypeError) {
    return "The validation service could not be reached. Check the API connection and try again.";
  }

  return "Something went wrong. Please try again.";
}
