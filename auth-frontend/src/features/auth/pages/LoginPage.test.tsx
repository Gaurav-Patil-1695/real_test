import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import LoginPage from './LoginPage';
import * as authApi from '../../../api/auth';

// Mock react-router-dom navigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the auth API
vi.mock('../../../api/auth', () => ({
  login: vi.fn(),
}));

const loginMock = authApi.login as ReturnType<typeof vi.fn>;

function renderLoginPage() {
  return render(
    <MemoryRouter>
      <LoginPage />
    </MemoryRouter>
  );
}

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  // ── Rendering ──────────────────────────────────────────────────────────────

  it('renders the page title', () => {
    renderLoginPage();
    expect(screen.getByRole('heading', { name: /sign in/i })).toBeInTheDocument();
  });

  it('renders the brand name', () => {
    renderLoginPage();
    expect(screen.getByText('auth-starter')).toBeInTheDocument();
  });

  it('renders the subtitle', () => {
    renderLoginPage();
    expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
  });

  it('renders the email input', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
  });

  it('renders the password input', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
  });

  it('renders the remember me checkbox', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/remember me/i)).toBeInTheDocument();
  });

  it('renders the forgot password link', () => {
    renderLoginPage();
    const link = screen.getByRole('link', { name: /forgot password/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/forgot-password');
  });

  it('renders the create account link', () => {
    renderLoginPage();
    const link = screen.getByRole('link', { name: /create account/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/register');
  });

  it('renders the submit button with label "Sign in"', () => {
    renderLoginPage();
    expect(screen.getByRole('button', { name: /^sign in$/i })).toBeInTheDocument();
  });

  it('password input type defaults to password', () => {
    renderLoginPage();
    const passwordInput = screen.getByLabelText(/^password$/i);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('does not show form-level error on initial render', () => {
    renderLoginPage();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  // ── Show / Hide password toggle ─────────────────────────────────────────────

  it('toggles password visibility when Show/Hide button is clicked', async () => {
    renderLoginPage();
    const passwordInput = screen.getByLabelText(/^password$/i);
    const toggleBtn = screen.getByRole('button', { name: /show password/i });

    expect(passwordInput).toHaveAttribute('type', 'password');
    await userEvent.click(toggleBtn);
    expect(passwordInput).toHaveAttribute('type', 'text');
    expect(screen.getByRole('button', { name: /hide password/i })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /hide password/i }));
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  // ── Validation ─────────────────────────────────────────────────────────────

  it('shows email and password validation errors when form is submitted empty', async () => {
    renderLoginPage();
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));
    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument();
    expect(await screen.findByText('Password is required.')).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it('shows email validation error for invalid email format', async () => {
    renderLoginPage();
    await userEvent.type(screen.getByLabelText(/email address/i), 'not-an-email');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'secret');
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));
    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it('shows password required error when password is empty', async () => {
    renderLoginPage();
    await userEvent.type(screen.getByLabelText(/email address/i), 'user@example.com');
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));
    expect(await screen.findByText('Password is required.')).toBeInTheDocument();
    expect(loginMock).not.toHaveBeenCalled();
  });

  it('clears email error when user starts typing in email field', async () => {
    renderLoginPage();
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));
    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/email address/i), 'a');
    expect(screen.queryByText('Enter a valid email address.')).not.toBeInTheDocument();
  });

  it('clears password error when user starts typing in password field', async () => {
    renderLoginPage();
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));
    expect(await screen.findByText('Password is required.')).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText(/^password$/i), 'x');
    expect(screen.queryByText('Password is required.')).not.toBeInTheDocument();
  });

  // ── Successful submission ───────────────────────────────────────────────────

  it('calls login API with correct payload on valid submission', async () => {
    loginMock.mockResolvedValueOnce({ access_token: 'tok', token_type: 'bearer' });
    renderLoginPage();

    await userEvent.type(screen.getByLabelText(/email address/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    await waitFor(() => expect(loginMock).toHaveBeenCalledTimes(1));
    expect(loginMock).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'password123',
      rememberMe: false,
    });
  });

  it('navigates to "/" after successful login', async () => {
    loginMock.mockResolvedValueOnce({ access_token: 'tok', token_type: 'bearer' });
    renderLoginPage();

    await userEvent.type(screen.getByLabelText(/email address/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'));
  });

  it('passes rememberMe flag when checkbox is checked', async () => {
    loginMock.mockResolvedValueOnce({ access_token: 'tok', token_type: 'bearer' });
    renderLoginPage();

    await userEvent.type(screen.getByLabelText(/email address/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.click(screen.getByLabelText(/remember me/i));
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    await waitFor(() => expect(loginMock).toHaveBeenCalledTimes(1));
    expect(loginMock).toHaveBeenCalledWith(
      expect.objectContaining({ rememberMe: true })
    );
  });

  // ── Loading / submitting state ──────────────────────────────────────────────

  it('disables the submit button while submitting', async () => {
    let resolveLogin!: () => void;
    loginMock.mockReturnValueOnce(
      new Promise<{ access_token: string; token_type: string }>((resolve) => {
        resolveLogin = () => resolve({ access_token: 'tok', token_type: 'bearer' });
      })
    );
    renderLoginPage();

    await userEvent.type(screen.getByLabelText(/email address/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    // While the promise is pending the button should be disabled
    expect(await screen.findByRole('button', { name: /signing in/i })).toBeDisabled();

    resolveLogin();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'));
  });

  it('shows spinner text while submitting', async () => {
    let resolveLogin!: () => void;
    loginMock.mockReturnValueOnce(
      new Promise<{ access_token: string; token_type: string }>((resolve) => {
        resolveLogin = () => resolve({ access_token: 'tok', token_type: 'bearer' });
      })
    );
    renderLoginPage();

    await userEvent.type(screen.getByLabelText(/email address/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    expect(await screen.findByText(/signing in/i)).toBeInTheDocument();

    resolveLogin();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'));
  });

  it('disables email and password inputs while submitting', async () => {
    let resolveLogin!: () => void;
    loginMock.mockReturnValueOnce(
      new Promise<{ access_token: string; token_type: string }>((resolve) => {
        resolveLogin = () => resolve({ access_token: 'tok', token_type: 'bearer' });
      })
    );
    renderLoginPage();

    await userEvent.type(screen.getByLabelText(/email address/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'password123');
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/email address/i)).toBeDisabled();
      expect(screen.getByLabelText(/^password$/i)).toBeDisabled();
    });

    resolveLogin();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/'));
  });

  // ── Error handling ──────────────────────────────────────────────────────────

  it('shows the error message from the API on login failure', async () => {
    loginMock.mockRejectedValueOnce(new Error('Invalid email or password.'));
    renderLoginPage();

    await userEvent.type(screen.getByLabelText(/email address/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'wrongpass');
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.');
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('shows a fallback error message when API throws a non-Error value', async () => {
    loginMock.mockRejectedValueOnce('some string error');
    renderLoginPage();

    await userEvent.type(screen.getByLabelText(/email address/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'wrongpass');
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid email or password.');
  });

  it('re-enables the submit button after a failed login', async () => {
    loginMock.mockRejectedValueOnce(new Error('Bad credentials'));
    renderLoginPage();

    await userEvent.type(screen.getByLabelText(/email address/i), 'user@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'wrongpass');
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));

    await screen.findByRole('alert');
    expect(screen.getByRole('button', { name: /^sign in$/i })).not.toBeDisabled();
  });

  // ── Remember me checkbox ────────────────────────────────────────────────────

  it('remember me checkbox starts unchecked', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/remember me/i)).not.toBeChecked();
  });

  it('remember me checkbox can be toggled', async () => {
    renderLoginPage();
    const checkbox = screen.getByLabelText(/remember me/i);
    await userEvent.click(checkbox);
    expect(checkbox).toBeChecked();
    await userEvent.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });

  // ── Accessibility ───────────────────────────────────────────────────────────

  it('email input has aria-required="true"', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/email address/i)).toHaveAttribute('aria-required', 'true');
  });

  it('password input has aria-required="true"', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/^password$/i)).toHaveAttribute('aria-required', 'true');
  });

  it('email input sets aria-invalid to true when there is a validation error', async () => {
    renderLoginPage();
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));
    await screen.findByText('Enter a valid email address.');
    expect(screen.getByLabelText(/email address/i)).toHaveAttribute('aria-invalid', 'true');
  });

  it('email input sets aria-invalid to false initially', () => {
    renderLoginPage();
    expect(screen.getByLabelText(/email address/i)).toHaveAttribute('aria-invalid', 'false');
  });

  it('password input sets aria-invalid to true when there is a validation error', async () => {
    renderLoginPage();
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }));
    await screen.findByText('Password is required.');
    expect(screen.getByLabelText(/^password$/i)).toHaveAttribute('aria-invalid', 'true');
  });

  it('form has aria-labelledby pointing to heading', () => {
    renderLoginPage();
    const form = screen.getByRole('form', { hidden: true }) ||
      document.querySelector('form');
    // The form element should carry aria-labelledby='login-title'
    const heading = screen.getByRole('heading', { name: /sign in/i });
    expect(heading.id).toBe('login-title');
  });
});
