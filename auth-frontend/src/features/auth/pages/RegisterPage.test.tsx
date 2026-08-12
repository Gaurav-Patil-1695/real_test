import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import RegisterPage from './RegisterPage';
import * as authApi from '../../../api/auth';

jest.mock('../../../api/auth');

const mockedRegister = authApi.register as jest.MockedFunction<typeof authApi.register>;

describe('RegisterPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  // ── Rendering ──────────────────────────────────────────────────────────────

  it('renders all form fields and the submit button', () => {
    render(<RegisterPage />);
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    // password field (label text "Password")
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/i agree to the terms/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('renders the branding title and sign-in link', () => {
    render(<RegisterPage />);
    expect(screen.getByText('auth-starter')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /sign in/i })).toHaveAttribute('href', '/login');
  });

  it('does not show any error messages on initial render', () => {
    render(<RegisterPage />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  // ── Validation – empty submit ───────────────────────────────────────────────

  it('shows all validation errors when submitted empty', async () => {
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    expect(await screen.findByText('Full name is required.')).toBeInTheDocument();
    expect(screen.getByText('Enter a valid email address.')).toBeInTheDocument();
    expect(screen.getByText('Password must be at least 8 characters.')).toBeInTheDocument();
    expect(screen.getByText('Passwords do not match.')).toBeInTheDocument();
    expect(screen.getByText('You must accept the Terms to continue.')).toBeInTheDocument();
  });

  it('does not call register API when validation fails', async () => {
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    await screen.findByText('Full name is required.');
    expect(mockedRegister).not.toHaveBeenCalled();
  });

  // ── Validation – individual fields ─────────────────────────────────────────

  it('shows error for invalid email format', async () => {
    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/full name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email address/i), 'not-an-email');
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    expect(await screen.findByText('Enter a valid email address.')).toBeInTheDocument();
  });

  it('shows error when password is shorter than 8 chars', async () => {
    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abc1');
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    expect(await screen.findByText('Password must be at least 8 characters.')).toBeInTheDocument();
  });

  it('shows error when password lacks complexity (no uppercase)', async () => {
    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/^password$/i), 'alllower1');
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    expect(await screen.findByText('Password must be at least 8 characters.')).toBeInTheDocument();
  });

  it('shows error when passwords do not match', async () => {
    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1!');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'DifferentPass1!');
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    expect(await screen.findByText('Passwords do not match.')).toBeInTheDocument();
  });

  it('shows error when terms are not accepted', async () => {
    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/full name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email address/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1!');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'Abcdef1!');
    // do NOT check terms
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    expect(await screen.findByText('You must accept the Terms to continue.')).toBeInTheDocument();
  });

  // ── Field-level error clearing ──────────────────────────────────────────────

  it('clears field error when the user starts typing in that field', async () => {
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    expect(await screen.findByText('Full name is required.')).toBeInTheDocument();
    await userEvent.type(screen.getByLabelText(/full name/i), 'A');
    expect(screen.queryByText('Full name is required.')).not.toBeInTheDocument();
  });

  // ── Password visibility toggle ─────────────────────────────────────────────

  it('toggles password visibility', async () => {
    render(<RegisterPage />);
    const passwordInput = screen.getByLabelText(/^password$/i);
    expect(passwordInput).toHaveAttribute('type', 'password');
    fireEvent.click(screen.getByRole('button', { name: /show password/i }));
    expect(passwordInput).toHaveAttribute('type', 'text');
    fireEvent.click(screen.getByRole('button', { name: /hide password/i }));
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('toggles confirm password visibility', async () => {
    render(<RegisterPage />);
    const confirmInput = screen.getByLabelText(/confirm password/i);
    expect(confirmInput).toHaveAttribute('type', 'password');
    fireEvent.click(screen.getByRole('button', { name: /show confirm password/i }));
    expect(confirmInput).toHaveAttribute('type', 'text');
    fireEvent.click(screen.getByRole('button', { name: /hide confirm password/i }));
    expect(confirmInput).toHaveAttribute('type', 'password');
  });

  // ── Password strength indicator ────────────────────────────────────────────

  it('does not render strength indicator when password is empty', () => {
    render(<RegisterPage />);
    expect(screen.queryByText(/weak|fair|good|strong/i)).not.toBeInTheDocument();
  });

  it('shows Weak strength for a short/simple password', async () => {
    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/^password$/i), 'a');
    expect(screen.getByText('Weak')).toBeInTheDocument();
  });

  it('shows Strong strength for a fully complex password', async () => {
    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1g');
    expect(screen.getByText('Strong')).toBeInTheDocument();
  });

  it('shows Fair strength for a password with 2 criteria', async () => {
    render(<RegisterPage />);
    // length>=8 + lowercase = 2 criteria
    await userEvent.type(screen.getByLabelText(/^password$/i), 'abcdefgh');
    expect(screen.getByText('Fair')).toBeInTheDocument();
  });

  // ── Successful submission ──────────────────────────────────────────────────

  it('calls register API with correct payload on valid submission', async () => {
    mockedRegister.mockResolvedValue({
      id: '1',
      full_name: 'Alice',
      email: 'alice@example.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });

    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/full name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email address/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1!');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'Abcdef1!');
    await userEvent.click(screen.getByLabelText(/i agree to the terms/i));
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(mockedRegister).toHaveBeenCalledWith({
        fullName: 'Alice',
        email: 'alice@example.com',
        password: 'Abcdef1!',
        confirmPassword: 'Abcdef1!',
      });
    });
  });

  it('shows success message after successful registration', async () => {
    mockedRegister.mockResolvedValue({
      id: '1',
      full_name: 'Alice',
      email: 'alice@example.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });

    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/full name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email address/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1!');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'Abcdef1!');
    await userEvent.click(screen.getByLabelText(/i agree to the terms/i));
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('Account created! You can now log in.')).toBeInTheDocument();
  });

  // ── Server error handling ──────────────────────────────────────────────────

  it('shows email field error when server error message contains "email"', async () => {
    mockedRegister.mockRejectedValue(new Error('That email address is already taken.'));

    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/full name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email address/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1!');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'Abcdef1!');
    await userEvent.click(screen.getByLabelText(/i agree to the terms/i));
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('That email is already registered.')).toBeInTheDocument();
  });

  it('shows generic server error when error message is unrelated to email', async () => {
    mockedRegister.mockRejectedValue(new Error('Internal server error'));

    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/full name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email address/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1!');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'Abcdef1!');
    await userEvent.click(screen.getByLabelText(/i agree to the terms/i));
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('Internal server error')).toBeInTheDocument();
  });

  it('shows fallback error message when a non-Error is thrown', async () => {
    mockedRegister.mockRejectedValue('something bad');

    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/full name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email address/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1!');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'Abcdef1!');
    await userEvent.click(screen.getByLabelText(/i agree to the terms/i));
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    expect(await screen.findByText('Registration failed. Please try again.')).toBeInTheDocument();
  });

  // ── Submitting state ───────────────────────────────────────────────────────

  it('disables the submit button and shows spinner while submitting', async () => {
    let resolve: (v: authApi.RegisterResponse) => void;
    mockedRegister.mockReturnValue(
      new Promise<authApi.RegisterResponse>((res) => {
        resolve = res;
      }),
    );

    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/full name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email address/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1!');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'Abcdef1!');
    await userEvent.click(screen.getByLabelText(/i agree to the terms/i));
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /creating account/i })).toBeDisabled();
    });

    // resolve to avoid act() warning
    resolve!({
      id: '1',
      full_name: 'Alice',
      email: 'alice@example.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });
    await screen.findByText('Account created! You can now log in.');
  });

  it('inputs are disabled while submitting', async () => {
    let resolve: (v: authApi.RegisterResponse) => void;
    mockedRegister.mockReturnValue(
      new Promise<authApi.RegisterResponse>((res) => {
        resolve = res;
      }),
    );

    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/full name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email address/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1!');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'Abcdef1!');
    await userEvent.click(screen.getByLabelText(/i agree to the terms/i));
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      expect(screen.getByLabelText(/full name/i)).toBeDisabled();
    });

    resolve!({
      id: '1',
      full_name: 'Alice',
      email: 'alice@example.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });
    await screen.findByText('Account created! You can now log in.');
  });

  // ── aria attributes ────────────────────────────────────────────────────────

  it('sets aria-invalid on inputs that have errors', async () => {
    render(<RegisterPage />);
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    await screen.findByText('Full name is required.');
    expect(screen.getByLabelText(/full name/i)).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByLabelText(/email address/i)).toHaveAttribute('aria-invalid', 'true');
  });

  it('sets aria-busy on submit button while submitting', async () => {
    let resolve: (v: authApi.RegisterResponse) => void;
    mockedRegister.mockReturnValue(
      new Promise<authApi.RegisterResponse>((res) => {
        resolve = res;
      }),
    );

    render(<RegisterPage />);
    await userEvent.type(screen.getByLabelText(/full name/i), 'Alice');
    await userEvent.type(screen.getByLabelText(/email address/i), 'alice@example.com');
    await userEvent.type(screen.getByLabelText(/^password$/i), 'Abcdef1!');
    await userEvent.type(screen.getByLabelText(/confirm password/i), 'Abcdef1!');
    await userEvent.click(screen.getByLabelText(/i agree to the terms/i));
    fireEvent.click(screen.getByRole('button', { name: /create account/i }));

    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /creating account/i });
      expect(btn).toHaveAttribute('aria-busy', 'true');
    });

    resolve!({
      id: '1',
      full_name: 'Alice',
      email: 'alice@example.com',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    });
    await screen.findByText('Account created! You can now log in.');
  });
});
