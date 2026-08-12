import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as authApi from './auth';

const originalFetch = global.fetch;

function mockFetch(response: Partial<Response> & { json?: () => Promise<unknown> }) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => ({}),
    ...response,
  }) as unknown as typeof fetch;
}

describe('auth API client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('login', () => {
    it('calls POST /api/v1/auth/login with credentials', async () => {
      mockFetch({ json: async () => ({ access_token: 'tok' }) });

      await authApi.login({ email: 'user@example.com', password: 'pass' });

      const [url, options] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
      expect(url).toContain('/api/v1/auth/login');
      expect(options?.method?.toUpperCase()).toBe('POST');
      const body = JSON.parse(options?.body as string);
      expect(body.email).toBe('user@example.com');
      expect(body.password).toBe('pass');
    });

    it('returns parsed JSON on success', async () => {
      mockFetch({ json: async () => ({ access_token: 'abc123' }) });

      const result = await authApi.login({ email: 'a@b.com', password: 'p' });
      expect(result).toMatchObject({ access_token: 'abc123' });
    });

    it('throws or rejects on non-ok response', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Invalid credentials' }),
      }) as unknown as typeof fetch;

      await expect(
        authApi.login({ email: 'a@b.com', password: 'wrong' })
      ).rejects.toThrow();
    });
  });

  describe('register', () => {
    it('calls POST /api/v1/auth/register', async () => {
      mockFetch({ json: async () => ({ id: 1, email: 'user@example.com' }) });

      await authApi.register({ email: 'user@example.com', password: 'pass123' });

      const [url, options] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
      expect(url).toContain('/api/v1/auth/register');
      expect(options?.method?.toUpperCase()).toBe('POST');
    });

    it('returns parsed JSON on success', async () => {
      mockFetch({ json: async () => ({ id: 42, email: 'new@example.com' }) });

      const result = await authApi.register({ email: 'new@example.com', password: 'pass' });
      expect(result).toMatchObject({ id: 42 });
    });

    it('throws on non-ok response', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Email already registered' }),
      }) as unknown as typeof fetch;

      await expect(
        authApi.register({ email: 'dup@example.com', password: 'p' })
      ).rejects.toThrow();
    });
  });

  describe('forgotPassword', () => {
    it('calls POST /api/v1/auth/forgot-password', async () => {
      mockFetch({ json: async () => ({}) });

      await authApi.forgotPassword({ email: 'user@example.com' });

      const [url, options] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
      expect(url).toContain('/api/v1/auth/forgot-password');
      expect(options?.method?.toUpperCase()).toBe('POST');
      const body = JSON.parse(options?.body as string);
      expect(body.email).toBe('user@example.com');
    });
  });

  describe('resetPassword', () => {
    it('calls POST /api/v1/auth/reset-password', async () => {
      mockFetch({ json: async () => ({}) });

      await authApi.resetPassword({ token: 'resettoken', password: 'newpass' });

      const [url, options] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
      expect(url).toContain('/api/v1/auth/reset-password');
      expect(options?.method?.toUpperCase()).toBe('POST');
      const body = JSON.parse(options?.body as string);
      expect(body.token).toBe('resettoken');
      expect(body.password).toBe('newpass');
    });

    it('throws on non-ok response', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: async () => ({ detail: 'Invalid token' }),
      }) as unknown as typeof fetch;

      await expect(
        authApi.resetPassword({ token: 'bad', password: 'p' })
      ).rejects.toThrow();
    });
  });

  describe('me', () => {
    it('calls GET /api/v1/auth/me', async () => {
      mockFetch({ json: async () => ({ email: 'user@example.com' }) });

      await authApi.me();

      const [url, options] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
      expect(url).toContain('/api/v1/auth/me');
      const method = options?.method?.toUpperCase() ?? 'GET';
      expect(method).toBe('GET');
    });

    it('returns user data on success', async () => {
      mockFetch({ json: async () => ({ email: 'me@example.com', id: 7 }) });

      const result = await authApi.me();
      expect(result).toMatchObject({ email: 'me@example.com' });
    });

    it('throws on non-ok response', async () => {
      global.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ detail: 'Unauthorized' }),
      }) as unknown as typeof fetch;

      await expect(authApi.me()).rejects.toThrow();
    });
  });

  describe('logout', () => {
    it('calls POST /api/v1/auth/logout', async () => {
      mockFetch({ json: async () => ({}) });

      await authApi.logout();

      const [url, options] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
      expect(url).toContain('/api/v1/auth/logout');
      expect(options?.method?.toUpperCase()).toBe('POST');
    });
  });

  describe('refresh', () => {
    it('calls POST /api/v1/auth/refresh', async () => {
      mockFetch({ json: async () => ({ access_token: 'newtoken' }) });

      await authApi.refresh();

      const [url, options] = (global.fetch as ReturnType<typeof vi.fn>).mock.calls[0];
      expect(url).toContain('/api/v1/auth/refresh');
      expect(options?.method?.toUpperCase()).toBe('POST');
    });
  });
});
