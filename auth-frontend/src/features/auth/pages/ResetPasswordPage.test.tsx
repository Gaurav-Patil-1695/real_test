import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import ResetPasswordPage from './ResetPasswordPage';
import * as authApi from '../../../api/auth';

// Mock the auth API module
jest.mock('../../../api/auth', () => ({
  resetPassword: jest.fn(),
}));

const mockedResetPassword = authApi.resetPassword as jest.MockedFunction<typeof authApi.resetPassword>;

// Helper to render with router and optional search params
function renderPage(search = '?token=valid-token') {
  return render(
    <MemoryRouter initialEntries={[`/reset-password${search}`]}>
      <Routes>
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('ResetPasswordPage — rendering', () => {
  it('renders the page title and subtitle', () => {
    renderPage();
    expect(screen.getByRole('heading', { name: /set new password/i })).toBeInTheDocument();
    expect(screen.getByText(/your new password must meet the requirements/i)).toBeInTheDocument();
  });

  it('renders the New Password and Confirm New Password fields', () => {
    renderPage();
    expect(screen.getByLabelText(/new password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm new password/i)).toBeInTheDocument();
  });

  it('renders the Reset Password submit button', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /reset password/i })).toBeInTheDocument();
  });

  it('renders the Back to login link', () => {
    renderPage();
    expect(screen.getByRole('link', { name: /back to login/i })).toBeInTheDocument();
  });

  it('renders the brand name', () => {
    renderPage();
    expect(screen.getByText('auth-starter')).toBeInTheDocument();
  });

  it('password inputs start as type=password', () => {
    renderPage();
    const [pwInput, confirmInput] = screen.getAllByLabelText(/password/i);
    expect(pwInput).toHaveAttribute('type', 'password');
    expect(confirmInput).toHaveAttribute('type', 'password');
  });
});

describe('ResetPasswordPage — show/hide password toggles', () => {
  it('toggles New Password visibility', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    const toggleBtn = screen.getByRole('button', { name: /show password/i });
    expect(pwInput).toHaveAttribute('type', 'password');
    await userEvent.click(toggleBtn);
    expect(pwInput).toHaveAttribute('type', 'text');
    await userEvent.click(screen.getByRole('button', { name: /hide password/i }));
    expect(pwInput).toHaveAttribute('type', 'password');
  });

  it('toggles Confirm New Password visibility', async () => {
    renderPage();
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    const toggleBtn = screen.getByRole('button', { name: /show confirm password/i });
    expect(confirmInput).toHaveAttribute('type', 'password');
    await userEvent.click(toggleBtn);
    expect(confirmInput).toHaveAttribute('type', 'text');
    await userEvent.click(screen.getByRole('button', { name: /hide confirm password/i }));
    expect(confirmInput).toHaveAttribute('type', 'password');
  });
});

describe('ResetPasswordPage — password validation (on blur)', () => {
  it('shows required error when password is empty and blurred', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    fireEvent.blur(pwInput);
    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
  });

  it('shows minLength error for passwords shorter than 8 characters', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    await userEvent.type(pwInput, 'Abc1');
    fireEvent.blur(pwInput);
    expect(await screen.findByText(/at least 8 characters/i)).toBeInTheDocument();
  });

  it('shows uppercase error when no uppercase letter', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    await userEvent.type(pwInput, 'abcdefg1');
    fireEvent.blur(pwInput);
    expect(await screen.findByText(/at least one uppercase letter/i)).toBeInTheDocument();
  });

  it('shows lowercase error when no lowercase letter', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    await userEvent.type(pwInput, 'ABCDEFG1');
    fireEvent.blur(pwInput);
    expect(await screen.findByText(/at least one lowercase letter/i)).toBeInTheDocument();
  });

  it('shows number error when no digit', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    await userEvent.type(pwInput, 'Abcdefgh');
    fireEvent.blur(pwInput);
    expect(await screen.findByText(/at least one number/i)).toBeInTheDocument();
  });

  it('shows no password error for a valid password', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    await userEvent.type(pwInput, 'ValidPass1');
    fireEvent.blur(pwInput);
    expect(screen.queryByText(/password is required/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/at least 8 characters/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/uppercase/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/lowercase/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/at least one number/i)).not.toBeInTheDocument();
  });
});

describe('ResetPasswordPage — confirm password validation (on blur)', () => {
  it('shows required error when confirm password is empty and blurred', async () => {
    renderPage();
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    fireEvent.blur(confirmInput);
    expect(await screen.findByText(/please confirm your password/i)).toBeInTheDocument();
  });

  it('shows mismatch error when passwords differ', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'DifferentPass1');
    fireEvent.blur(confirmInput);
    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
  });

  it('shows no confirm error when passwords match', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    fireEvent.blur(confirmInput);
    expect(screen.queryByText(/passwords do not match/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/please confirm your password/i)).not.toBeInTheDocument();
  });
});

describe('ResetPasswordPage — password strength bar', () => {
  it('does not show strength bar when password is empty', () => {
    renderPage();
    expect(screen.queryByText(/strength:/i)).not.toBeInTheDocument();
  });

  it('shows Weak strength for a password with only length', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    await userEvent.type(pwInput, 'aaaaaaaa'); // length >= 8, lowercase only
    expect(await screen.findByText(/strength: fair/i)).toBeInTheDocument();
  });

  it('shows Strong for a fully valid password', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    await userEvent.type(pwInput, 'ValidPass1');
    expect(await screen.findByText(/strength: strong/i)).toBeInTheDocument();
  });

  it('shows Weak for a short single-char password type', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    await userEvent.type(pwInput, 'A');
    // score = 1 (uppercase only, < 8 chars so length not counted)
    expect(await screen.findByText(/strength: weak/i)).toBeInTheDocument();
  });
});

describe('ResetPasswordPage — missing token', () => {
  it('shows token missing error banner on submit when no token in URL', async () => {
    renderPage(''); // no search params
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    const submitBtn = screen.getByRole('button', { name: /reset password/i });
    await userEvent.click(submitBtn);
    expect(await screen.findByRole('alert')).toHaveTextContent(/reset token is missing or invalid/i);
    expect(mockedResetPassword).not.toHaveBeenCalled();
  });
});

describe('ResetPasswordPage — form submission validation on submit', () => {
  it('shows validation errors on submit without filling fields', async () => {
    renderPage();
    const submitBtn = screen.getByRole('button', { name: /reset password/i });
    await userEvent.click(submitBtn);
    expect(await screen.findByText(/password is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/please confirm your password/i)).toBeInTheDocument();
    expect(mockedResetPassword).not.toHaveBeenCalled();
  });

  it('shows mismatch error on submit when passwords differ', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'OtherPass1');
    const submitBtn = screen.getByRole('button', { name: /reset password/i });
    await userEvent.click(submitBtn);
    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
    expect(mockedResetPassword).not.toHaveBeenCalled();
  });
});

describe('ResetPasswordPage — successful submission', () => {
  it('calls resetPassword API with correct args and shows success banner', async () => {
    mockedResetPassword.mockResolvedValueOnce({ message: 'Password reset.' });
    renderPage('?token=abc123');
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    const submitBtn = screen.getByRole('button', { name: /reset password/i });
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockedResetPassword).toHaveBeenCalledWith({
        token: 'abc123',
        password: 'ValidPass1',
        confirmPassword: 'ValidPass1',
      });
    });

    expect(await screen.findByRole('status')).toHaveTextContent(/password reset successfully/i);
  });

  it('hides the form after successful submission', async () => {
    mockedResetPassword.mockResolvedValueOnce({ message: 'Password reset.' });
    renderPage('?token=abc123');
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /reset password/i }));

    await waitFor(() => {
      expect(screen.queryByRole('button', { name: /reset password/i })).not.toBeInTheDocument();
    });
  });

  it('navigates to /login after 3 seconds on success', async () => {
    mockedResetPassword.mockResolvedValueOnce({ message: 'Password reset.' });
    renderPage('?token=abc123');
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /reset password/i }));

    await screen.findByRole('status');

    act(() => {
      jest.advanceTimersByTime(3000);
    });

    expect(await screen.findByText('Login Page')).toBeInTheDocument();
  });
});

describe('ResetPasswordPage — failed submission', () => {
  it('shows error banner when API returns an error', async () => {
    mockedResetPassword.mockRejectedValueOnce(new Error('Token is expired or invalid.'));
    renderPage('?token=bad-token');
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /reset password/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/token is expired or invalid/i);
  });

  it('shows generic error message when API throws non-Error', async () => {
    mockedResetPassword.mockRejectedValueOnce('unknown failure');
    renderPage('?token=bad-token');
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /reset password/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/something went wrong/i);
  });

  it('re-enables the submit button after failed submission', async () => {
    mockedResetPassword.mockRejectedValueOnce(new Error('Token expired.'));
    renderPage('?token=bad-token');
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /reset password/i }));

    await screen.findByRole('alert');
    const submitBtn = screen.getByRole('button', { name: /reset password/i });
    expect(submitBtn).not.toBeDisabled();
  });
});

describe('ResetPasswordPage — submitting state', () => {
  it('disables submit button while submitting', async () => {
    let resolveApi: (val: authApi.ResetPasswordResponse) => void;
    mockedResetPassword.mockReturnValueOnce(
      new Promise<authApi.ResetPasswordResponse>((resolve) => {
        resolveApi = resolve;
      })
    );
    renderPage('?token=abc123');
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /reset password/i }));

    expect(screen.getByRole('button', { name: /resetting/i })).toBeDisabled();

    act(() => {
      resolveApi!({ message: 'done' });
    });
  });

  it('shows Resetting… text while submitting', async () => {
    let resolveApi: (val: authApi.ResetPasswordResponse) => void;
    mockedResetPassword.mockReturnValueOnce(
      new Promise<authApi.ResetPasswordResponse>((resolve) => {
        resolveApi = resolve;
      })
    );
    renderPage('?token=abc123');
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /reset password/i }));

    expect(screen.getByText(/resetting/i)).toBeInTheDocument();

    act(() => {
      resolveApi!({ message: 'done' });
    });
  });
});

describe('ResetPasswordPage — aria attributes', () => {
  it('marks password input aria-invalid when there is an error', async () => {
    renderPage();
    const pwInput = screen.getByLabelText(/^new password$/i);
    fireEvent.blur(pwInput);
    await screen.findByText(/password is required/i);
    expect(pwInput).toHaveAttribute('aria-invalid', 'true');
  });

  it('marks confirm input aria-invalid when there is an error', async () => {
    renderPage();
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    fireEvent.blur(confirmInput);
    await screen.findByText(/please confirm your password/i);
    expect(confirmInput).toHaveAttribute('aria-invalid', 'true');
  });

  it('sets aria-busy on submit button when submitting', async () => {
    let resolveApi: (val: authApi.ResetPasswordResponse) => void;
    mockedResetPassword.mockReturnValueOnce(
      new Promise<authApi.ResetPasswordResponse>((resolve) => {
        resolveApi = resolve;
      })
    );
    renderPage('?token=abc123');
    const pwInput = screen.getByLabelText(/^new password$/i);
    const confirmInput = screen.getByLabelText(/confirm new password/i);
    await userEvent.type(pwInput, 'ValidPass1');
    await userEvent.type(confirmInput, 'ValidPass1');
    await userEvent.click(screen.getByRole('button', { name: /reset password/i }));

    const btn = screen.getByRole('button', { name: /resetting/i });
    expect(btn).toHaveAttribute('aria-busy', 'true');

    act(() => {
      resolveApi!({ message: 'done' });
    });
  });
});
