import React, { useState, useId } from 'react';
import { register } from '../../../api/auth';

interface RegisterFormState {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

interface RegisterFormErrors {
  fullName?: string;
  email?: string;
  password?: string;
  confirmPassword?: string;
  acceptTerms?: string;
}

function getPasswordStrength(password: string): number {
  let score = 0;
  if (password.length >= 8) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/\d/.test(password)) score++;
  return score;
}

function validateForm(values: RegisterFormState): RegisterFormErrors {
  const errors: RegisterFormErrors = {};

  if (!values.fullName || values.fullName.trim().length < 1) {
    errors.fullName = 'Full name is required.';
  } else if (values.fullName.length > 120) {
    errors.fullName = 'Full name is required.';
  }

  if (!values.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
    errors.email = 'Enter a valid email address.';
  }

  if (!values.password || values.password.length < 8) {
    errors.password = 'Password must be at least 8 characters.';
  } else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/.test(values.password)) {
    errors.password = 'Password must be at least 8 characters.';
  }

  if (!values.confirmPassword || values.confirmPassword !== values.password) {
    errors.confirmPassword = 'Passwords do not match.';
  }

  if (!values.acceptTerms) {
    errors.acceptTerms = 'You must accept the Terms to continue.';
  }

  return errors;
}

export default function RegisterPage(): JSX.Element {
  const [values, setValues] = useState<RegisterFormState>({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
    acceptTerms: false,
  });

  const [errors, setErrors] = useState<RegisterFormErrors>({});
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const idPrefix = useId();
  const fullNameId = `${idPrefix}-fullName`;
  const emailId = `${idPrefix}-email`;
  const passwordId = `${idPrefix}-password`;
  const confirmPasswordId = `${idPrefix}-confirmPassword`;
  const acceptTermsId = `${idPrefix}-acceptTerms`;

  const fullNameErrId = `${fullNameId}-err`;
  const emailErrId = `${emailId}-err`;
  const passwordErrId = `${passwordId}-err`;
  const confirmPasswordErrId = `${confirmPasswordId}-err`;
  const acceptTermsErrId = `${acceptTermsId}-err`;

  const passwordStrength = getPasswordStrength(values.password);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>): void {
    const { name, value, type, checked } = e.target;
    setValues((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
    setServerError(null);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>): Promise<void> {
    e.preventDefault();
    setServerError(null);
    setSuccessMessage(null);

    const validationErrors = validateForm(values);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setIsSubmitting(true);
    try {
      await register({
        fullName: values.fullName,
        email: values.email,
        password: values.password,
        confirmPassword: values.confirmPassword,
      });
      setSuccessMessage('Account created! You can now log in.');
    } catch (err: unknown) {
      if (err instanceof Error) {
        const message = err.message;
        if (message.toLowerCase().includes('email')) {
          setErrors((prev) => ({ ...prev, email: 'That email is already registered.' }));
        } else {
          setServerError(message || 'Registration failed. Please try again.');
        }
      } else {
        setServerError('Registration failed. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
  const strengthColors = [
    'var(--color-text-muted)',
    'var(--color-error)',
    'var(--color-warning)',
    'var(--color-info)',
    'var(--color-success)',
  ];

  return (
    <>
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
          --family-mono: 'JetBrains Mono', 'Courier New', monospace;
          --radius-button: 8px;
          --radius-card: 16px;
          --radius-full: 9999px;
          --radius-input: 8px;
          --radius-lg: 12px;
          --radius-sm: 4px;
          --space-2xl: 48px;
          --space-lg: 24px;
          --space-md: 16px;
          --space-sm: 8px;
          --space-xl: 32px;
          --space-xs: 4px;
        }

        *, *::before, *::after {
          box-sizing: border-box;
        }

        .register-page {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          background-color: var(--color-bg-app);
          font-family: var(--family-base);
          color: var(--color-text-primary);
          padding: var(--space-md);
        }

        .auth-branding {
          text-align: center;
          margin-bottom: var(--space-lg);
        }

        .auth-branding__title {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-text-primary);
          margin: 0 0 var(--space-xs) 0;
        }

        .auth-branding__subtitle {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          margin: 0;
        }

        .auth-card {
          background-color: var(--color-surface);
          border-radius: var(--radius-card);
          box-shadow: var(--elevation-card);
          padding: var(--space-xl);
          width: 100%;
          max-width: 440px;
        }

        .auth-card__title {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-text-primary);
          margin: 0 0 var(--space-xs) 0;
          text-align: center;
        }

        .auth-card__subtitle {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          text-align: center;
          margin: 0 0 var(--space-xl) 0;
        }

        .auth-card__field {
          margin-bottom: var(--space-md);
        }

        .auth-card__footer {
          margin-top: var(--space-lg);
          text-align: center;
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
        }

        .field__label {
          display: block;
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-primary);
          margin-bottom: var(--space-xs);
        }

        .field__input-wrapper {
          position: relative;
          display: flex;
          align-items: center;
        }

        .field__input {
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          font-family: var(--family-base);
          font-size: 16px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-primary);
          background-color: var(--color-surface);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-input);
          outline: none;
          transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }

        .field__input:focus {
          border-color: var(--color-accent-primary);
          box-shadow: var(--elevation-focus);
        }

        .field__input--error {
          border-color: var(--color-error);
        }

        .field__input--with-toggle {
          padding-right: 44px;
        }

        .field__toggle {
          position: absolute;
          right: var(--space-sm);
          background: none;
          border: none;
          cursor: pointer;
          padding: var(--space-xs);
          color: var(--color-text-muted);
          font-size: 14px;
          line-height: 1;
          border-radius: var(--radius-sm);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .field__toggle:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .field__error {
          display: block;
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-error);
          margin-top: var(--space-xs);
        }

        .field--error .field__label {
          color: var(--color-error);
        }

        .password-strength {
          margin-top: var(--space-xs);
        }

        .password-strength__bars {
          display: flex;
          gap: var(--space-xs);
          margin-bottom: var(--space-xs);
        }

        .password-strength__bar {
          height: 4px;
          flex: 1;
          border-radius: var(--radius-full);
          background-color: var(--color-border);
          transition: background-color 0.2s ease;
        }

        .password-strength__label {
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-muted);
        }

        .checkbox-field {
          display: flex;
          align-items: flex-start;
          gap: var(--space-sm);
        }

        .checkbox-field__input {
          width: 16px;
          height: 16px;
          flex-shrink: 0;
          margin-top: 2px;
          accent-color: var(--color-accent-primary);
          cursor: pointer;
        }

        .checkbox-field__label {
          font-size: 14px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-secondary);
          cursor: pointer;
        }

        .btn-primary {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: var(--space-sm);
          width: 100%;
          padding: var(--space-sm) var(--space-md);
          font-family: var(--family-base);
          font-size: 16px;
          font-weight: 600;
          line-height: 1.5;
          color: var(--color-surface);
          background-color: var(--color-accent-primary);
          border: none;
          border-radius: var(--radius-button);
          cursor: pointer;
          transition: background-color 0.15s ease;
          margin-top: var(--space-md);
        }

        .btn-primary:hover:not(:disabled) {
          background-color: var(--color-accent-primary-hover);
        }

        .btn-primary:active:not(:disabled) {
          background-color: var(--color-accent-primary-active);
        }

        .btn-primary:disabled {
          background-color: var(--color-accent-disabled);
          cursor: not-allowed;
        }

        .btn-primary:focus-visible {
          outline: none;
          box-shadow: var(--elevation-focus);
        }

        .spinner {
          width: 16px;
          height: 16px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: #fff;
          border-radius: var(--radius-full);
          animation: spin 0.7s linear infinite;
          flex-shrink: 0;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .alert {
          padding: var(--space-sm) var(--space-md);
          border-radius: var(--radius-input);
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          margin-bottom: var(--space-md);
        }

        .alert--error {
          background-color: #fef2f2;
          color: var(--color-error);
          border: 1px solid #fecaca;
        }

        .alert--success {
          background-color: #f0fdf4;
          color: var(--color-success);
          border: 1px solid #bbf7d0;
        }

        .link {
          color: var(--color-link);
          text-decoration: none;
          font-weight: 500;
        }

        .link:hover {
          text-decoration: underline;
        }

        .link:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
          border-radius: var(--radius-sm);
        }
      `}</style>

      <main className="register-page">
        <div className="auth-branding" aria-label="auth-starter">
          <p className="auth-branding__title">auth-starter</p>
          <p className="auth-branding__subtitle">Secure authentication for your app</p>
        </div>

        <div className="auth-card">
          <h1 className="auth-card__title">Create account</h1>
          <p className="auth-card__subtitle">Join today — it's free</p>

          <div aria-live="polite">
            {serverError && (
              <div role="alert" className="alert alert--error">
                {serverError}
              </div>
            )}
            {successMessage && (
              <div role="status" className="alert alert--success">
                {successMessage}
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} noValidate>
            <div className={`auth-card__field${errors.fullName ? ' field--error' : ''}`}>
              <label className="field__label" htmlFor={fullNameId}>
                Full name
              </label>
              <div className="field__input-wrapper">
                <input
                  id={fullNameId}
                  name="fullName"
                  type="text"
                  autoComplete="name"
                  className={`field__input${errors.fullName ? ' field__input--error' : ''}`}
                  value={values.fullName}
                  onChange={handleChange}
                  aria-describedby={errors.fullName ? fullNameErrId : undefined}
                  aria-invalid={!!errors.fullName}
                  disabled={isSubmitting}
                />
              </div>
              {errors.fullName && (
                <span className="field__error" id={fullNameErrId} role="alert">
                  {errors.fullName}
                </span>
              )}
            </div>

            <div className={`auth-card__field${errors.email ? ' field--error' : ''}`}>
              <label className="field__label" htmlFor={emailId}>
                Email address
              </label>
              <div className="field__input-wrapper">
                <input
                  id={emailId}
                  name="email"
                  type="email"
                  autoComplete="email"
                  className={`field__input${errors.email ? ' field__input--error' : ''}`}
                  value={values.email}
                  onChange={handleChange}
                  aria-describedby={errors.email ? emailErrId : undefined}
                  aria-invalid={!!errors.email}
                  disabled={isSubmitting}
                />
              </div>
              {errors.email && (
                <span className="field__error" id={emailErrId} role="alert">
                  {errors.email}
                </span>
              )}
            </div>

            <div className={`auth-card__field${errors.password ? ' field--error' : ''}`}>
              <label className="field__label" htmlFor={passwordId}>
                Password
              </label>
              <div className="field__input-wrapper">
                <input
                  id={passwordId}
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  className={`field__input field__input--with-toggle${errors.password ? ' field__input--error' : ''}`}
                  value={values.password}
                  onChange={handleChange}
                  aria-describedby={[
                    errors.password ? passwordErrId : '',
                    `${passwordId}-strength`,
                  ]
                    .filter(Boolean)
                    .join(' ') || undefined}
                  aria-invalid={!!errors.password}
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  className="field__toggle"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                  onClick={() => setShowPassword((v) => !v)}
                  tabIndex={0}
                >
                  {showPassword ? '🙈' : '👁'}
                </button>
              </div>
              {values.password.length > 0 && (
                <div className="password-strength" id={`${passwordId}-strength`}>
                  <div className="password-strength__bars" aria-hidden="true">
                    {[1, 2, 3, 4].map((level) => (
                      <div
                        key={level}
                        className="password-strength__bar"
                        style={{
                          backgroundColor:
                            passwordStrength >= level
                              ? strengthColors[passwordStrength]
                              : 'var(--color-border)',
                        }}
                      />
                    ))}
                  </div>
                  <span className="password-strength__label" style={{ color: strengthColors[passwordStrength] }}>
                    {passwordStrength > 0 ? strengthLabels[passwordStrength] : ''}
                  </span>
                </div>
              )}
              {errors.password && (
                <span className="field__error" id={passwordErrId} role="alert">
                  {errors.password}
                </span>
              )}
            </div>

            <div className={`auth-card__field${errors.confirmPassword ? ' field--error' : ''}`}>
              <label className="field__label" htmlFor={confirmPasswordId}>
                Confirm password
              </label>
              <div className="field__input-wrapper">
                <input
                  id={confirmPasswordId}
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  className={`field__input field__input--with-toggle${errors.confirmPassword ? ' field__input--error' : ''}`}
                  value={values.confirmPassword}
                  onChange={handleChange}
                  aria-describedby={errors.confirmPassword ? confirmPasswordErrId : undefined}
                  aria-invalid={!!errors.confirmPassword}
                  disabled={isSubmitting}
                />
                <button
                  type="button"
                  className="field__toggle"
                  aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
                  onClick={() => setShowConfirmPassword((v) => !v)}
                  tabIndex={0}
                >
                  {showConfirmPassword ? '🙈' : '👁'}
                </button>
              </div>
              {errors.confirmPassword && (
                <span className="field__error" id={confirmPasswordErrId} role="alert">
                  {errors.confirmPassword}
                </span>
              )}
            </div>

            <div className={`auth-card__field${errors.acceptTerms ? ' field--error' : ''}`}>
              <div className="checkbox-field">
                <input
                  id={acceptTermsId}
                  name="acceptTerms"
                  type="checkbox"
                  className="checkbox-field__input"
                  checked={values.acceptTerms}
                  onChange={handleChange}
                  aria-describedby={errors.acceptTerms ? acceptTermsErrId : undefined}
                  aria-invalid={!!errors.acceptTerms}
                  disabled={isSubmitting}
                />
                <label className="checkbox-field__label" htmlFor={acceptTermsId}>
                  I agree to the Terms of Service and Privacy Policy
                </label>
              </div>
              {errors.acceptTerms && (
                <span className="field__error" id={acceptTermsErrId} role="alert">
                  {errors.acceptTerms}
                </span>
              )}
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={isSubmitting}
              aria-busy={isSubmitting}
            >
              {isSubmitting && <span className="spinner" aria-hidden="true" />}
              {isSubmitting ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <p className="auth-card__footer">
            Already have an account?{' '}
            <a className="link" href="/login">
              Sign in
            </a>
          </p>
        </div>
      </main>
    </>
  );
}
