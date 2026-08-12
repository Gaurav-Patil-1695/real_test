const API_BASE = '/auth';

export interface RegisterRequest {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
}

export interface RegisterResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  rememberMe?: boolean;
}

export interface LoginResponse {
  accessToken: string;
  tokenType: string;
  user: {
    id: string;
    fullName: string;
    email: string;
    isActive: boolean;
    createdAt: string;
  };
}

export interface MeResponse {
  id: string;
  fullName: string;
  email: string;
  isActive: boolean;
  createdAt: string;
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

export interface RefreshResponse {
  accessToken: string;
  tokenType: string;
}

export interface LogoutResponse {
  message: string;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = await response.json();
      if (body?.error?.message) {
        message = body.error.message;
      } else if (body?.detail) {
        message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // ignore JSON parse errors
    }
    throw new Error(message);
  }

  const text = await response.text();
  if (!text) {
    return undefined as unknown as T;
  }
  return JSON.parse(text) as T;
}

export async function register(payload: RegisterRequest): Promise<RegisterResponse> {
  return request<RegisterResponse>('/register', {
    method: 'POST',
    body: JSON.stringify({
      full_name: payload.fullName,
      email: payload.email,
      password: payload.password,
      confirm_password: payload.confirmPassword,
    }),
  });
}

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  return request<LoginResponse>('/login', {
    method: 'POST',
    body: JSON.stringify({
      email: payload.email,
      password: payload.password,
      remember_me: payload.rememberMe ?? false,
    }),
  });
}

export async function me(): Promise<MeResponse> {
  return request<MeResponse>('/me', {
    method: 'GET',
  });
}

export async function forgotPassword(payload: ForgotPasswordRequest): Promise<ForgotPasswordResponse> {
  return request<ForgotPasswordResponse>('/forgot-password', {
    method: 'POST',
    body: JSON.stringify({
      email: payload.email,
    }),
  });
}

export async function resetPassword(payload: ResetPasswordRequest): Promise<ResetPasswordResponse> {
  return request<ResetPasswordResponse>('/reset-password', {
    method: 'POST',
    body: JSON.stringify({
      token: payload.token,
      password: payload.password,
      confirm_password: payload.confirmPassword,
    }),
  });
}

export async function refresh(): Promise<RefreshResponse> {
  return request<RefreshResponse>('/refresh', {
    method: 'POST',
  });
}

export async function logout(): Promise<LogoutResponse> {
  return request<LogoutResponse>('/logout', {
    method: 'POST',
  });
}
