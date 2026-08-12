import React, { useState } from 'react';
import { forgotPassword } from '../../../api/auth';

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [emailError, setEmailError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const validate = (): boolean => {
    if (!email.trim()) {
      setEmailError('Email is required.');
      return false;
    }
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setEmailError('Enter a valid email address.');
      return false;
    }
    setEmailError('');
    return true;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSuccessMessage('');
    setErrorMessage('');

    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await forgotPassword({ email });
      setSuccessMessage(
        'If an account with that email exists, a password reset link has been sent.'
      );
      setEmail('');
    } catch {
      setErrorMessage(
        'Something went wrong. Please try again later.'
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    if (emailError) setEmailError('');
  };

  return (
    <div className="auth-layout">
      <style>{`
        :root {
          --color-accent-disabled: #c7d2fe;
          --color-accent-primary: #4f46e5;
          --color-accent-primary-active: #3730a3;
          --color-accent-primary-hover: #4338ca;
          --color-bg-app: #f1f5f9;
          --color-border: #E2E8F0;
          --color-border-strong: #CBD5E1;
          --color-error: #DC2626;
          --color-focus-ring: #818cf8;
          --color-info: #2563EB;
          --color-link: #4f46e5;
          --color-muted-surface: #f8fafc;
          --color-success: #16A34A;
          --color-surface: #FFFFFF;
          --color-text-muted: #94A3B8;
          --color-text-primary: #0F172A;
          --color-text-secondary: #475569;
          --color-warning: #D97706;
          --elevation-1: 0 1px 2px rgba(15,23,42,0.06);
          --elevation-2: 0 4px 12px rgba(15,23,42,0.08);
          --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
          --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
          --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
          --radius-button: 8px;
          --radius-card: 16px;
          --radius-input: 8px;
          --space-2xl: 48px;
          --space-lg: 24px;
          --space-md: 16px;
          --space-sm: 8px;
          --space-xl: 32px;
          --space-xs: 4px;
        }

        .auth-layout {
          min-height: 100vh;
          background-color: var(--color-bg-app);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          font-family: var(--family-base);
          padding: var(--space-md);
        }

        .auth-branding {
          margin-bottom: var(--space-lg);
          text-align: center;
        }

        .auth-branding__logo {
          font-size: 30px;
          font-weight: 700;
          color: var(--color-accent-primary);
          line-height: 1.2;
          text-decoration: none;
        }

        .auth-card {
          background-color: var(--color-surface);
          border-radius: var(--radius-card);
          box-shadow: var(--elevation-card);
          padding: var(--space-2xl);
          width: 100%;
          max-width: 440px;
        }

        .auth-card__title {
          font-size: 30px;
          font-weight: 700;
          color: var(--color-text-primary);
          line-height: 1.2;
          margin: 0 0 var(--space-sm) 0;
          text-align: center;
        }

        .auth-card__subtitle {
          font-size: 14px;
          font-weight: 400;
          color: var(--color-text-secondary);
          line-height: 1.5;
          margin: 0 0 var(--space-xl) 0;
          text-align: center;
        }

        .auth-card__field {
          margin-bottom: var(--space-md);
          display: flex;
          flex-direction: column;
          gap: var(--space-xs);
        }

        .auth-card__label {
          font-size: 14px;
          font-weight: 500;
          color: var(--color-text-primary);
          line-height: 1.5;
        }

        .auth-card__input {
          font-family: var(--family-base);
          font-size: 16px;
          font-weight: 400;
          color: var(--color-text-primary);
          background-color: var(--color-surface);
          border: 1px solid var(--color-border-strong);
          border-radius: var(--radius-input);
          padding: var(--space-sm) var(--space-md);
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s;
          width: 100%;
          box-sizing: border-box;
        }

        .auth-card__input:focus {
          border-color: var(--color-accent-primary);
          box-shadow: var(--elevation-focus);
        }

        .auth-card__input--error {
          border-color: var(--color-error);
        }

        .auth-card__input--error:focus {
          border-color: var(--color-error);
          box-shadow: 0 0 0 3px rgba(220,38,38,0.2);
        }

        .field--error {
          font-size: 12px;
          font-weight: 400;
          color: var(--color-error);
          line-height: 1.5;
          margin: 0;
        }

        .auth-card__submit {
          font-family: var(--family-base);
          font-size: 16px;
          font-weight: 600;
          color: var(--color-surface);
          background-color: var(--color-accent-primary);
          border: none;
          border-radius: var(--radius-button);
          padding: var(--space-sm) var(--space-md);
          width: 100%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
          margin-top: var(--space-lg);
          min-height: 44px;
          transition: background-color 0.15s;
        }

        .auth-card__submit:hover:not(:disabled) {
          background-color: var(--color-accent-primary-hover);
        }

        .auth-card__submit:active:not(:disabled) {
          background-color: var(--color-accent-primary-active);
        }

        .auth-card__submit:disabled {
          background-color: var(--color-accent-disabled);
          cursor: not-allowed;
        }

        .auth-card__spinner {
          width: 18px;
          height: 18px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: #fff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
          display: inline-block;
          flex-shrink: 0;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .auth-card__banner {
          border-radius: var(--radius-input);
          padding: var(--space-sm) var(--space-md);
          font-size: 14px;
          font-weight: 400;
          line-height: 1.5;
          margin-bottom: var(--space-md);
        }

        .auth-card__banner--success {
          background-color: #dcfce7;
          color: var(--color-success);
          border: 1px solid #bbf7d0;
        }

        .auth-card__banner--error {
          background-color: #fee2e2;
          color: var(--color-error);
          border: 1px solid #fecaca;
        }

        .auth-card__footer {
          margin-top: var(--space-lg);
          text-align: center;
          font-size: 14px;
          font-weight: 400;
          color: var(--color-text-secondary);
          line-height: 1.5;
        }

        .link {
          color: var(--color-link);
          font-weight: 500;
          text-decoration: none;
        }

        .link:hover {
          text-decoration: underline;
        }
      `}</style>

      <div className="auth-branding" aria-label="App branding">
        <span className="auth-branding__logo">AuthStarter</span>
      </div>

      <div className="auth-card" role="main">
        <h1 className="auth-card__title">Forgot password?</h1>
        <p className="auth-card__subtitle">
          Enter your email address and we&apos;ll send you a link to reset your password.
        </p>

        <div aria-live="polite" aria-atomic="true">
          {successMessage && (
            <div className="auth-card__banner auth-card__banner--success" role="status">
              {successMessage}
            </div>
          )}
          {errorMessage && (
            <div className="auth-card__banner auth-card__banner--error" role="alert">
              {errorMessage}
            </div>
          )}
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className="auth-card__field">
            <label className="auth-card__label" htmlFor="email">
              Email address
            </label>
            <input
              id="email"
              type="email"
              className={`auth-card__input${emailError ? ' auth-card__input--error' : ''}`}
              value={email}
              onChange={handleEmailChange}
              autoComplete="email"
              aria-describedby={emailError ? 'email-error' : undefined}
              aria-invalid={emailError ? 'true' : 'false'}
              disabled={isSubmitting}
              placeholder="you@example.com"
            />
            {emailError && (
              <p id="email-error" className="field--error" role="alert">
                {emailError}
              </p>
            )}
          </div>

          <button
            type="submit"
            className="auth-card__submit"
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting && <span className="auth-card__spinner" aria-hidden="true" />}
            {isSubmitting ? 'Sending...' : 'Send reset link'}
          </button>
        </form>

        <div className="auth-card__footer">
          <a href="/login" className="link">
            Back to sign in
          </a>
        </div>
      </div>
    </div>
  );
};

export default ForgotPasswordPage;
