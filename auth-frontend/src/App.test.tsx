import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from './App';

// ---------------------------------------------------------------------------
// Module mocks – replace heavy leaf components & auth guards with thin stubs
// ---------------------------------------------------------------------------

jest.mock('./features/auth/RequireAuth', () => ({
  __esModule: true,
  default: ({ children }: { children?: React.ReactNode }) => {
    // Simulate an authenticated user so the protected outlet renders
    const { Outlet } = require('react-router-dom');
    return <Outlet />;
  },
}));

jest.mock('./features/auth/RequireGuest', () => ({
  __esModule: true,
  default: () => {
    const { Outlet } = require('react-router-dom');
    return <Outlet />;
  },
}));

jest.mock('./features/auth/pages/LoginPage', () => ({
  __esModule: true,
  default: () => <div data-testid="login-page">LoginPage</div>,
}));

jest.mock('./features/auth/pages/RegisterPage', () => ({
  __esModule: true,
  default: () => <div data-testid="register-page">RegisterPage</div>,
}));

jest.mock('./features/auth/pages/ForgotPasswordPage', () => ({
  __esModule: true,
  default: () => <div data-testid="forgot-password-page">ForgotPasswordPage</div>,
}));

jest.mock('./features/auth/pages/ResetPasswordPage', () => ({
  __esModule: true,
  default: () => <div data-testid="reset-password-page">ResetPasswordPage</div>,
}));

jest.mock('./pages/ProfilePage', () => ({
  __esModule: true,
  default: () => <div data-testid="profile-page">ProfilePage</div>,
}));

jest.mock('./features/auth/LogoutRoute', () => ({
  __esModule: true,
  default: () => <div data-testid="logout-route">LogoutRoute</div>,
}));

// ---------------------------------------------------------------------------
// Helper
// ---------------------------------------------------------------------------

const renderAt = (path: string) =>
  render(
    <MemoryRouter initialEntries={[path]}>
      <App />
    </MemoryRouter>
  );

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('App routing', () => {
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('renders LoginPage at /login', () => {
    renderAt('/login');
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });

  test('renders RegisterPage at /register', () => {
    renderAt('/register');
    expect(screen.getByTestId('register-page')).toBeInTheDocument();
  });

  test('renders ForgotPasswordPage at /forgot-password', () => {
    renderAt('/forgot-password');
    expect(screen.getByTestId('forgot-password-page')).toBeInTheDocument();
  });

  test('renders ResetPasswordPage at /reset-password', () => {
    renderAt('/reset-password');
    expect(screen.getByTestId('reset-password-page')).toBeInTheDocument();
  });

  test('renders ProfilePage at /profile (authenticated)', () => {
    renderAt('/profile');
    expect(screen.getByTestId('profile-page')).toBeInTheDocument();
  });

  test('renders LogoutRoute at /logout', () => {
    renderAt('/logout');
    expect(screen.getByTestId('logout-route')).toBeInTheDocument();
  });

  test('redirects unknown paths to /login', () => {
    renderAt('/some-unknown-path');
    // After redirect the LoginPage should be rendered
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });

  test('redirects root path / to /login', () => {
    renderAt('/');
    expect(screen.getByTestId('login-page')).toBeInTheDocument();
  });
});
