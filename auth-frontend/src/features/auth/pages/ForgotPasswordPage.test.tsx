import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ForgotPasswordPage from './ForgotPasswordPage';
import * as authApi from '../../../api/auth';

jest.mock('../../../api/auth', () => ({
  forgotPassword: jest.fn(),
}));

const mockedForgotPassword = authApi.forgotPassword as jest.MockedFunction<typeof authApi.forgotPassword>;

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders the page title', () => {
      render(<ForgotPasswordPage />);
      expect(screen.getByRole('heading', { name: /forgot password/i })).toBeInTheDocument();
    });

    it('renders the subtitle', () => {
      render(<ForgotPasswordPage />);
      expect(screen.getByText(/enter your email address/i)).toBeInTheDocument();
    });

    it('renders email input', () => {
      render(<ForgotPasswordPage />);
      expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    });

    it('renders submit button with correct initial text', () => {
      render(<ForgotPasswordPage />);
      expect(screen.getByRole('button', { name: /send reset link/i })).toBeInTheDocument();
    });

    it('renders the app branding', () => {
      render(<ForgotPasswordPage />);
      expect(screen.getByText('AuthStarter')).toBeInTheDocument();
    });

    it('renders back to sign in link', () => {
      render(<ForgotPasswordPage />);
      const link = screen.getByRole('link', { name: /back to sign in/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute('href', '/login');
    });

    it('does not show success or error messages initially', () => {
      render(<ForgotPasswordPage />);
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });

    it('email input has placeholder', () => {
      render(<ForgotPasswordPage />);
      expect(screen.getByPlaceholderText('you@example.com')).toBeInTheDocument();
    });

    it('submit button is not disabled initially', () => {
      render(<ForgotPasswordPage />);
      expect(screen.getByRole('button', { name: /send reset link/i })).not.toBeDisabled();
    });
  });

  describe('validation', () => {
    it('shows error when submitting with empty email', async () => {
      render(<ForgotPasswordPage />);
      fireEvent.submit(screen.getByRole('button', { name: /send reset link/i }).closest('form')!);
      await waitFor(() => {
        expect(screen.getByText('Email is required.')).toBeInTheDocument();
      });
    });

    it('shows error when submitting with invalid email format', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'notanemail');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByText('Enter a valid email address.')).toBeInTheDocument();
      });
    });

    it('shows error for email with no domain', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByText('Enter a valid email address.')).toBeInTheDocument();
      });
    });

    it('shows error for whitespace-only email', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, '   ');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByText('Email is required.')).toBeInTheDocument();
      });
    });

    it('clears email error when user starts typing', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByText('Email is required.')).toBeInTheDocument();
      });
      await userEvent.type(input, 'a');
      expect(screen.queryByText('Email is required.')).not.toBeInTheDocument();
    });

    it('does not call forgotPassword API when validation fails', async () => {
      render(<ForgotPasswordPage />);
      fireEvent.submit(screen.getByLabelText(/email address/i).closest('form')!);
      await waitFor(() => {
        expect(screen.getByText('Email is required.')).toBeInTheDocument();
      });
      expect(mockedForgotPassword).not.toHaveBeenCalled();
    });

    it('sets aria-invalid on input when there is an email error', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(input).toHaveAttribute('aria-invalid', 'true');
      });
    });

    it('sets aria-describedby on input when there is an email error', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(input).toHaveAttribute('aria-describedby', 'email-error');
      });
    });

    it('aria-invalid is false when there is no email error', () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      expect(input).toHaveAttribute('aria-invalid', 'false');
    });
  });

  describe('successful submission', () => {
    beforeEach(() => {
      mockedForgotPassword.mockResolvedValue({ message: 'ok' });
    });

    it('calls forgotPassword with the entered email', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(mockedForgotPassword).toHaveBeenCalledWith({ email: 'user@example.com' });
      });
    });

    it('shows success message after successful submission', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(
          screen.getByText(
            'If an account with that email exists, a password reset link has been sent.'
          )
        ).toBeInTheDocument();
      });
    });

    it('success message has role=status', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument();
      });
    });

    it('clears email field after successful submission', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(input).toHaveValue('');
      });
    });

    it('does not show error message on success', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument();
      });
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('failed submission', () => {
    beforeEach(() => {
      mockedForgotPassword.mockRejectedValue(new Error('Network error'));
    });

    it('shows error message when API call fails', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(
          screen.getByText('Something went wrong. Please try again later.')
        ).toBeInTheDocument();
      });
    });

    it('error message has role=alert', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
    });

    it('does not show success message on failure', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
      expect(screen.queryByRole('status')).not.toBeInTheDocument();
    });

    it('email field is not cleared on failure', async () => {
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });
      expect(input).toHaveValue('user@example.com');
    });
  });

  describe('submitting state', () => {
    it('disables submit button while submitting', async () => {
      let resolvePromise: (value: { message: string }) => void;
      mockedForgotPassword.mockImplementation(
        () => new Promise((resolve) => { resolvePromise = resolve; })
      );

      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);

      await waitFor(() => {
        expect(screen.getByRole('button')).toBeDisabled();
      });

      act(() => { resolvePromise({ message: 'ok' }); });
      await waitFor(() => {
        expect(screen.getByRole('button')).not.toBeDisabled();
      });
    });

    it('shows Sending... text while submitting', async () => {
      let resolvePromise: (value: { message: string }) => void;
      mockedForgotPassword.mockImplementation(
        () => new Promise((resolve) => { resolvePromise = resolve; })
      );

      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);

      await waitFor(() => {
        expect(screen.getByText('Sending...')).toBeInTheDocument();
      });

      act(() => { resolvePromise({ message: 'ok' }); });
      await waitFor(() => {
        expect(screen.queryByText('Sending...')).not.toBeInTheDocument();
      });
    });

    it('disables email input while submitting', async () => {
      let resolvePromise: (value: { message: string }) => void;
      mockedForgotPassword.mockImplementation(
        () => new Promise((resolve) => { resolvePromise = resolve; })
      );

      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);

      await waitFor(() => {
        expect(input).toBeDisabled();
      });

      act(() => { resolvePromise({ message: 'ok' }); });
      await waitFor(() => {
        expect(input).not.toBeDisabled();
      });
    });

    it('button has aria-busy true while submitting', async () => {
      let resolvePromise: (value: { message: string }) => void;
      mockedForgotPassword.mockImplementation(
        () => new Promise((resolve) => { resolvePromise = resolve; })
      );

      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);
      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);

      await waitFor(() => {
        expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'true');
      });

      act(() => { resolvePromise({ message: 'ok' }); });
      await waitFor(() => {
        expect(screen.getByRole('button')).toHaveAttribute('aria-busy', 'false');
      });
    });

    it('clears previous success message on new submission', async () => {
      mockedForgotPassword.mockResolvedValue({ message: 'ok' });
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);

      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument();
      });

      // type email again (was cleared) and resubmit
      await userEvent.type(input, 'user@example.com');
      mockedForgotPassword.mockRejectedValue(new Error('fail'));
      fireEvent.submit(input.closest('form')!);

      await waitFor(() => {
        expect(screen.queryByRole('status')).not.toBeInTheDocument();
      });
    });

    it('clears previous error message on new submission', async () => {
      mockedForgotPassword.mockRejectedValue(new Error('fail'));
      render(<ForgotPasswordPage />);
      const input = screen.getByLabelText(/email address/i);

      await userEvent.type(input, 'user@example.com');
      fireEvent.submit(input.closest('form')!);
      await waitFor(() => {
        expect(screen.getByRole('alert')).toBeInTheDocument();
      });

      mockedForgotPassword.mockResolvedValue({ message: 'ok' });
      fireEvent.submit(input.closest('form')!);

      await waitFor(() => {
        expect(screen.queryByRole('alert')).not.toBeInTheDocument();
      });
    });
  });
});
