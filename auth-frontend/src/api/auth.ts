const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  user: UserResponse;
}

export interface RegisterRequest {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptedTerms: boolean;
}

export interface RegisterResponse {
  accessToken: string;
  tokenType: string;
  user: UserResponse;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ForgotPasswordResponse {
  message: string;
}

export interface ResetPasswordRequest {
  token: string;
  password: string;
  confirmPassword: string;
}

export interface ResetPasswordResponse {
  message: string;
}

export interface UserResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface MeResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface LogoutResponse {
  message: string;
}

export interface RefreshResponse {
  accessToken: string;
  tokenType: string;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Record<string, string[]>;
  };
}

async function request<T>(path: string, options: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let errorBody: ApiError;
    try {
      errorBody = await response.json();
    } catch {
      throw new Error(`Request failed with status ${response.status}`);
    }
    const err = new Error(errorBody.error?.message || 'Request failed');
    (err as Error & { apiError: ApiError }).apiError = errorBody;
    throw err;
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return response.json() as Promise<T>;
}

export async function login(data: LoginRequest): Promise<LoginResponse> {
  return request<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  return request<RegisterResponse>('/auth/register', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function forgotPassword(data: ForgotPasswordRequest): Promise<ForgotPasswordResponse> {
  return request<ForgotPasswordResponse>('/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function resetPassword(data: ResetPasswordRequest): Promise<ResetPasswordResponse> {
  return request<ResetPasswordResponse>('/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function me(accessToken: string): Promise<MeResponse> {
  return request<MeResponse>('/auth/me', {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function logout(accessToken: string): Promise<LogoutResponse> {
  return request<LogoutResponse>('/auth/logout', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
}

export async function refresh(): Promise<RefreshResponse> {
  return request<RefreshResponse>('/auth/refresh', {
    method: 'POST',
  });
}
