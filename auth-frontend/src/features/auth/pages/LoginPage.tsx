import React, { useState, useId } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { login } from '../../../api/auth';

interface LoginFormState {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface LoginFormErrors {
  email?: string;
  password?: string;
  form?: string;
}

function validateLoginForm(values: LoginFormState): LoginFormErrors {
  const errors: LoginFormErrors = {};

  if (!values.email) {
    errors.email = 'Enter a valid email address.';
  } else {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(values.email)) {
      errors.email = 'Enter a valid email address.';
    }
  }

  if (!values.password || values.password.length < 1) {
    errors.password = 'Password is required.';
  }

  return errors;
}

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const emailId = useId();
  const passwordId = useId();
  const rememberMeId = useId();
  const emailErrorId = useId();
  const passwordErrorId = useId();
  const formErrorId = useId();

  const [values, setValues] = useState<LoginFormState>({
    email: '',
    password: '',
    rememberMe: false,
  });
  const [errors, setErrors] = useState<LoginFormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, email: e.target.value }));
    if (errors.email) {
      setErrors((prev) => ({ ...prev, email: undefined }));
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, password: e.target.value }));
    if (errors.password) {
      setErrors((prev) => ({ ...prev, password: undefined }));
    }
  };

  const handleRememberMeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValues((prev) => ({ ...prev, rememberMe: e.target.checked }));
  };

  const handleTogglePassword = () => {
    setShowPassword((prev) => !prev);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const validationErrors = validateLoginForm(values);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors({});
    setIsSubmitting(true);
    try {
      await login({
        email: values.email,
        password: values.password,
        rememberMe: values.rememberMe,
      });
      navigate('/');
    } catch (err: unknown) {
      const message =
        err instanceof Error
          ? err.message
          : 'Invalid email or password.';
      setErrors({ form: message });
    } finally {
      setIsSubmitting(false);
    }
  };

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

        .login-page {
          min-height: 100vh;
          background-color: var(--color-bg-app);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          font-family: var(--family-base);
          color: var(--color-text-primary);
          padding: var(--space-md);
        }

        .login-page__branding {
          margin-bottom: var(--space-lg);
          text-align: center;
        }

        .login-page__brand-name {
          font-size: 18px;
          font-weight: 600;
          line-height: 1.25;
          color: var(--color-accent-primary);
          margin: 0;
        }

        .auth-card {
          background-color: var(--color-surface);
          border-radius: var(--radius-card);
          box-shadow: var(--elevation-card);
          padding: var(--space-2xl);
          width: 100%;
          max-width: 400px;
          box-sizing: border-box;
        }

        .auth-card__title {
          font-size: 30px;
          font-weight: 700;
          line-height: 1.2;
          color: var(--color-text-primary);
          margin: 0 0 var(--space-xs) 0;
        }

        .auth-card__subtitle {
          font-size: 14px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-secondary);
          margin: 0 0 var(--space-xl) 0;
        }

        .auth-card__form-error {
          background-color: #fef2f2;
          border: 1px solid var(--color-error);
          border-radius: var(--radius-sm);
          color: var(--color-error);
          font-size: 14px;
          line-height: 1.5;
          padding: var(--space-sm) var(--space-md);
          margin-bottom: var(--space-md);
        }

        .auth-card__field {
          margin-bottom: var(--space-md);
        }

        .auth-card__label {
          display: block;
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-primary);
          margin-bottom: var(--space-xs);
        }

        .auth-card__input-wrapper {
          position: relative;
        }

        .auth-card__input {
          width: 100%;
          box-sizing: border-box;
          font-family: var(--family-base);
          font-size: 16px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-primary);
          background-color: var(--color-surface);
          border: 1px solid var(--color-border-strong);
          border-radius: var(--radius-input);
          padding: var(--space-sm) var(--space-md);
          outline: none;
          transition: border-color 0.15s ease, box-shadow 0.15s ease;
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

        .auth-card__input--has-toggle {
          padding-right: 48px;
        }

        .auth-card__toggle-btn {
          position: absolute;
          right: var(--space-sm);
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          cursor: pointer;
          color: var(--color-text-muted);
          font-size: 14px;
          font-family: var(--family-base);
          font-weight: 500;
          padding: var(--space-xs);
          border-radius: var(--radius-sm);
          line-height: 1;
        }

        .auth-card__toggle-btn:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .auth-card__field-error {
          display: block;
          font-size: 12px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-error);
          margin-top: var(--space-xs);
        }

        .field--error .auth-card__label {
          color: var(--color-error);
        }

        .auth-card__row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--space-lg);
        }

        .auth-card__checkbox-label {
          display: flex;
          align-items: center;
          gap: var(--space-xs);
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-text-secondary);
          cursor: pointer;
        }

        .auth-card__checkbox {
          width: 16px;
          height: 16px;
          accent-color: var(--color-accent-primary);
          cursor: pointer;
        }

        .auth-card__link {
          font-size: 14px;
          font-weight: 500;
          line-height: 1.5;
          color: var(--color-link);
          text-decoration: none;
        }

        .auth-card__link:hover {
          text-decoration: underline;
        }

        .auth-card__link:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
          border-radius: var(--radius-sm);
        }

        .btn {
          display: block;
          width: 100%;
          box-sizing: border-box;
          font-family: var(--family-base);
          font-size: 16px;
          font-weight: 600;
          line-height: 1.5;
          text-align: center;
          border: none;
          border-radius: var(--radius-button);
          padding: var(--space-sm) var(--space-md);
          cursor: pointer;
          transition: background-color 0.15s ease;
        }

        .btn--primary {
          background-color: var(--color-accent-primary);
          color: var(--color-surface);
        }

        .btn--primary:hover:not(:disabled) {
          background-color: var(--color-accent-primary-hover);
        }

        .btn--primary:active:not(:disabled) {
          background-color: var(--color-accent-primary-active);
        }

        .btn--primary:disabled {
          background-color: var(--color-accent-disabled);
          cursor: not-allowed;
        }

        .btn--primary:focus-visible {
          outline: 2px solid var(--color-focus-ring);
          outline-offset: 2px;
        }

        .btn__spinner {
          display: inline-block;
          width: 14px;
          height: 14px;
          border: 2px solid rgba(255,255,255,0.4);
          border-top-color: #ffffff;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
          vertical-align: middle;
          margin-right: var(--space-xs);
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .auth-card__footer {
          margin: var(--space-lg) 0 0 0;
          text-align: center;
          font-size: 14px;
          font-weight: 400;
          line-height: 1.5;
          color: var(--color-text-secondary);
        }
      `}</style>

      <div className='login-page'>
        <div className='login-page__branding'>
          <p className='login-page__brand-name'>auth-starter</p>
        </div>

        <form
          className='auth-card'
          aria-labelledby='login-title'
          onSubmit={handleSubmit}
          noValidate
        >
          <h1 className='auth-card__title' id='login-title'>
            Sign in
          </h1>
          <p className='auth-card__subtitle'>Welcome back. Please enter your details.</p>

          {errors.form && (
            <div
              className='auth-card__form-error'
              role='alert'
              aria-live='polite'
              id={formErrorId}
            >
              {errors.form}
            </div>
          )}

          <div className={`auth-card__field${errors.email ? ' field--error' : ''}`}>
            <label className='auth-card__label' htmlFor={emailId}>
              Email address
            </label>
            <div className='auth-card__input-wrapper'>
              <input
                id={emailId}
                type='email'
                className={`auth-card__input${errors.email ? ' auth-card__input--error' : ''}`}
                value={values.email}
                onChange={handleEmailChange}
                autoComplete='email'
                aria-required='true'
                aria-invalid={errors.email ? 'true' : 'false'}
                aria-describedby={errors.email ? emailErrorId : undefined}
                disabled={isSubmitting}
              />
            </div>
            {errors.email && (
              <span
                id={emailErrorId}
                className='auth-card__field-error'
                role='alert'
              >
                {errors.email}
              </span>
            )}
          </div>

          <div className={`auth-card__field${errors.password ? ' field--error' : ''}`}>
            <label className='auth-card__label' htmlFor={passwordId}>
              Password
            </label>
            <div className='auth-card__input-wrapper'>
              <input
                id={passwordId}
                type={showPassword ? 'text' : 'password'}
                className={`auth-card__input auth-card__input--has-toggle${
                  errors.password ? ' auth-card__input--error' : ''
                }`}
                value={values.password}
                onChange={handlePasswordChange}
                autoComplete='current-password'
                aria-required='true'
                aria-invalid={errors.password ? 'true' : 'false'}
                aria-describedby={errors.password ? passwordErrorId : undefined}
                disabled={isSubmitting}
              />
              <button
                type='button'
                className='auth-card__toggle-btn'
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                onClick={handleTogglePassword}
                tabIndex={0}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            {errors.password && (
              <span
                id={passwordErrorId}
                className='auth-card__field-error'
                role='alert'
              >
                {errors.password}
              </span>
            )}
          </div>

          <div className='auth-card__row'>
            <label className='auth-card__checkbox-label' htmlFor={rememberMeId}>
              <input
                id={rememberMeId}
                type='checkbox'
                className='auth-card__checkbox'
                checked={values.rememberMe}
                onChange={handleRememberMeChange}
                disabled={isSubmitting}
              />
              Remember me
            </label>
            <Link to='/forgot-password' className='auth-card__link'>
              Forgot password?
            </Link>
          </div>

          <button
            type='submit'
            className='btn btn--primary'
            disabled={isSubmitting}
            aria-busy={isSubmitting}
          >
            {isSubmitting && <span className='btn__spinner' aria-hidden='true' />}
            {isSubmitting ? 'Signing in…' : 'Sign in'}
          </button>

          <p className='auth-card__footer'>
            Don&apos;t have an account?{' '}
            <Link to='/register' className='auth-card__link'>
              Create account
            </Link>
          </p>
        </form>
      </div>
    </>
  );
};

export default LoginPage;
