import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import React from 'react';
import { AuthProvider, useAuth } from './AuthContext';
import * as authApi from '../api/auth';

vi.mock('../api/auth', () => ({
  me: vi.fn(),
  login: vi.fn(),
  logout: vi.fn(),
  refresh: vi.fn(),
  register: vi.fn(),
  forgotPassword: vi.fn(),
  resetPassword: vi.fn(),
}));

function TestConsumer() {
  const { user, loading } = useAuth();
  if (loading) return <div>Loading...</div>;
  return <div>{user ? `Logged in as ${user.email}` : 'Not logged in'}</div>;
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('shows loading initially', () => {
    vi.mocked(authApi.me).mockReturnValue(new Promise(() => {})); // never resolves

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    expect(screen.getByText('Loading...')).toBeDefined();
  });

  it('sets user when me() resolves', async () => {
    vi.mocked(authApi.me).mockResolvedValue({ email: 'user@example.com', id: 1 } as any);

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Logged in as user@example.com')).toBeDefined();
    });
  });

  it('sets user to null when me() rejects', async () => {
    vi.mocked(authApi.me).mockRejectedValue(new Error('Unauthorized'));

    render(
      <AuthProvider>
        <TestConsumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Not logged in')).toBeDefined();
    });
  });

  it('useAuth throws if used outside AuthProvider', () => {
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => render(<TestConsumer />)).toThrow();

    spy.mockRestore();
  });

  it('exposes login function that calls authApi.login and updates user', async () => {
    vi.mocked(authApi.me)
      .mockRejectedValueOnce(new Error('not authed')) // initial check
      .mockResolvedValueOnce({ email: 'newuser@example.com', id: 2 } as any); // after login
    vi.mocked(authApi.login).mockResolvedValue({ access_token: 'tok' } as any);

    function LoginConsumer() {
      const { login, user, loading } = useAuth();
      if (loading) return <div>Loading...</div>;
      return (
        <div>
          <div>{user ? `User: ${user.email}` : 'No user'}</div>
          <button onClick={() => login({ email: 'newuser@example.com', password: 'pass' })}>
            Login
          </button>
        </div>
      );
    }

    const { getByText } = render(
      <AuthProvider>
        <LoginConsumer />
      </AuthProvider>
    );

    await waitFor(() => expect(getByText('No user')).toBeDefined());

    await act(async () => {
      getByText('Login').click();
    });

    await waitFor(() => {
      expect(authApi.login).toHaveBeenCalledWith({ email: 'newuser@example.com', password: 'pass' });
    });
  });

  it('exposes logout function that calls authApi.logout and clears user', async () => {
    vi.mocked(authApi.me).mockResolvedValue({ email: 'user@example.com', id: 1 } as any);
    vi.mocked(authApi.logout).mockResolvedValue({} as any);

    function LogoutConsumer() {
      const { logout, user, loading } = useAuth();
      if (loading) return <div>Loading...</div>;
      return (
        <div>
          <div>{user ? `User: ${user.email}` : 'No user'}</div>
          <button onClick={() => logout()}>Logout</button>
        </div>
      );
    }

    const { getByText } = render(
      <AuthProvider>
        <LogoutConsumer />
      </AuthProvider>
    );

    await waitFor(() => expect(getByText('User: user@example.com')).toBeDefined());

    await act(async () => {
      getByText('Logout').click();
    });

    await waitFor(() => {
      expect(authApi.logout).toHaveBeenCalled();
    });
  });
});
