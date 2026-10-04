import type { ApiErrorBody } from './types';

export class ApiError extends Error {
  status: number;
  code: string;
  requestId: string;

  constructor(status: number, code: string, message: string, requestId: string) {
    super(message);
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

function toQuery(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined) search.set(key, String(value));
  }
  const query = search.toString();
  return query ? `?${query}` : '';
}

export async function apiFetch<T>(
  path: string,
  params: Record<string, string | number | undefined> = {},
  init?: RequestInit,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}${toQuery(params)}`, {
      headers: { 'Content-Type': 'application/json' },
      ...init,
    });
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', `Cannot reach API at ${BASE_URL}`, '-');
  }
  if (!response.ok) {
    let code = 'UNKNOWN_ERROR';
    let message = `Request failed with status ${response.status}`;
    let requestId = response.headers.get('X-Request-ID') ?? '-';
    try {
      const body = (await response.json()) as ApiErrorBody;
      code = body.error ?? code;
      message = body.message ?? message;
      requestId = body.request_id ?? requestId;
    } catch {
      // Non-JSON error page: keep the status-based fallback.
    }
    throw new ApiError(response.status, code, message, requestId);
  }
  return (await response.json()) as T;
}
