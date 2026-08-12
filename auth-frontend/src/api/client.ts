import { ApiError } from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

async function silentRefresh(): Promise<void> {
  const response = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new ApiError(401, 'UNAUTHORIZED', 'Session expired. Please log in again.');
  }

  const data = await response.json();
  const accessToken = data?.data?.access_token ?? data?.access_token;
  if (accessToken) {
    setAccessToken(accessToken);
  }
}

let _accessToken: string | null = null;

export function setAccessToken(token: string | null): void {
  _accessToken = token;
}

export function getAccessToken(): string | null {
  return _accessToken;
}

function buildHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra);
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (_accessToken) {
    headers.set('Authorization', `Bearer ${_accessToken}`);
  }
  return headers;
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  let code = 'UNKNOWN_ERROR';
  let message = 'An unexpected error occurred.';

  try {
    const body = await response.json();
    const err = body?.error ?? body;
    code = err?.code ?? code;
    message = err?.message ?? message;
  } catch {
    // ignore parse errors
  }

  return new ApiError(response.status, code, message);
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE_URL}${path}`;

  const headers = buildHeaders(options.headers);

  let response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers,
  });

  if (response.status === 401) {
    // Avoid concurrent refresh storms
    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = silentRefresh().finally(() => {
        isRefreshing = false;
        refreshPromise = null;
      });
    }

    try {
      await refreshPromise;
    } catch {
      throw await parseErrorResponse(response);
    }

    // Retry original request with new token
    const retryHeaders = buildHeaders(options.headers);
    response = await fetch(url, {
      ...options,
      credentials: 'include',
      headers: retryHeaders,
    });
  }

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export const client = {
  get<T>(path: string, options?: RequestInit): Promise<T> {
    return request<T>(path, { ...options, method: 'GET' });
  },
  post<T>(path: string, body?: unknown, options?: RequestInit): Promise<T> {
    return request<T>(path, {
      ...options,
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },
  put<T>(path: string, body?: unknown, options?: RequestInit): Promise<T> {
    return request<T>(path, {
      ...options,
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },
  patch<T>(path: string, body?: unknown, options?: RequestInit): Promise<T> {
    return request<T>(path, {
      ...options,
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  },
  delete<T>(path: string, options?: RequestInit): Promise<T> {
    return request<T>(path, { ...options, method: 'DELETE' });
  },
};
