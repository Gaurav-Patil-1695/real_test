import React, { useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { resetPassword } from '../../../api/auth';

const fieldErrors = {
  password: {
    required: 'Password is required.',
    minLength: 'Password must be at least 8 characters.',
    uppercase: 'Password must contain at least one uppercase letter.',
    lowercase: 'Password must contain at least one lowercase letter.',
    number: 'Password must contain at least one number.',
  },
  confirmPassword: {
    required: 'Please confirm your password.',
    mismatch: 'Passwords do not match.',
  },
  token: {
    missing: 'Reset token is missing or invalid.',
  },
};

function validatePassword(value: string): string {
  if (!value) return fieldErrors.password.required;
  if (value.length < 8) return fieldErrors.password.minLength;
  if (!/[A-Z]/.test(value)) return fieldErrors.password.uppercase;
  if (!/[a-z]/.test(value)) return fieldErrors.password.lowercase;
  if (!/[0-9]/.test(value)) return fieldErrors.password.number;
  return '';
}

function validateConfirmPassword(password: string, confirm: string): string {
  if (!confirm) return fieldErrors.confirmPassword.required;
  if (confirm !== password) return fieldErrors.confirmPassword.mismatch;
  return '';
}

function getStrengthLevel(value: string): number {
  let score = 0;
  if (value.length >= 8) score++;
  if (/[A-Z]/.test(value)) score++;
  if (/[a-z]/.test(value)) score++;
  if (/[0-9]/.test(value)) score++;
  return score;
}

const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
const strengthColors = [
  'transparent',
  'var(--color-error)',
  'var(--color-warning)',
  'var(--color-info)',
  'var(--color-success)',
];

const styles: Record<string, React.CSSProperties> = {
  app: {
    minHeight: '100vh',
    backgroundColor: 'var(--color-bg-app)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    fontFamily: 'var(--font-family-base)',
    padding: 'var(--space-md)',
  },
  branding: {
    marginBottom: 'var(--space-md)',
    textAlign: 'center',
  },
  brandName: {
    fontSize: '18px',
    fontWeight: 700,
    color: 'var(--color-accent-primary)',
    margin: 0,
  },
  card: {
    backgroundColor: 'var(--color-surface)',
    borderRadius: 'var(--radius-card)',
    boxShadow: 'var(--elevation-card)',
    padding: 'var(--space-xl)',
    width: '100%',
    maxWidth: '420px',
  },
  title: {
    fontSize: '30px',
    fontWeight: 700,
    lineHeight: 1.2,
    color: 'var(--color-text-primary)',
    margin: '0 0 var(--space-xs)',
  },
  subtitle: {
    fontSize: '14px',
    fontWeight: 400,
    color: 'var(--color-text-secondary)',
    margin: '0 0 var(--space-lg)',
    lineHeight: 1.5,
  },
  field: {
    marginBottom: 'var(--space-md)',
  },
  label: {
    display: 'block',
    fontSize: '14px',
    fontWeight: 500,
    color: 'var(--color-text-primary)',
    marginBottom: 'var(--space-xs)',
  },
  inputWrapper: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
  },
  input: {
    width: '100%',
    padding: 'var(--space-sm) var(--space-md)',
    fontSize: '16px',
    lineHeight: 1.5,
    color: 'var(--color-text-primary)',
    backgroundColor: 'var(--color-surface)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-input)',
    outline: 'none',
    boxSizing: 'border-box',
    paddingRight: '44px',
  },
  inputError: {
    borderColor: 'var(--color-error)',
  },
  toggleBtn: {
    position: 'absolute',
    right: '10px',
    background: 'none',
    border: 'none',
    cursor: 'pointer',
    padding: 'var(--space-xs)',
    color: 'var(--color-text-muted)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  errorMsg: {
    display: 'block',
    fontSize: '12px',
    color: 'var(--color-error)',
    marginTop: 'var(--space-xs)',
    lineHeight: 1.5,
  },
  strengthBar: {
    display: 'flex',
    gap: '4px',
    marginTop: 'var(--space-xs)',
  },
  strengthSegment: {
    height: '4px',
    flex: 1,
    borderRadius: 'var(--radius-sm)',
    backgroundColor: 'var(--color-border)',
    transition: 'background-color 0.2s',
  },
  strengthLabel: {
    fontSize: '12px',
    color: 'var(--color-text-muted)',
    marginTop: '4px',
    lineHeight: 1.5,
  },
  submitBtn: {
    width: '100%',
    padding: 'var(--space-sm) var(--space-md)',
    fontSize: '16px',
    fontWeight: 600,
    color: 'var(--color-surface)',
    backgroundColor: 'var(--color-accent-primary)',
    border: 'none',
    borderRadius: 'var(--radius-button)',
    cursor: 'pointer',
    marginTop: 'var(--space-md)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 'var(--space-sm)',
    transition: 'background-color 0.2s',
  },
  submitBtnDisabled: {
    backgroundColor: 'var(--color-accent-disabled)',
    cursor: 'not-allowed',
  },
  banner: {
    borderRadius: 'var(--radius-input)',
    padding: 'var(--space-sm) var(--space-md)',
    marginBottom: 'var(--space-md)',
    fontSize: '14px',
    lineHeight: 1.5,
  },
  bannerError: {
    backgroundColor: '#fef2f2',
    color: 'var(--color-error)',
    border: '1px solid #fecaca',
  },
  bannerSuccess: {
    backgroundColor: '#f0fdf4',
    color: 'var(--color-success)',
    border: '1px solid #bbf7d0',
  },
  link: {
    color: 'var(--color-link)',
    textDecoration: 'none',
    fontWeight: 500,
    fontSize: '14px',
  },
  backToLogin: {
    textAlign: 'center',
    marginTop: 'var(--space-md)',
    fontSize: '14px',
    color: 'var(--color-text-secondary)',
  },
};

const EyeIcon: React.FC<{ visible: boolean }> = ({ visible }) =>
  visible ? (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  ) : (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );

const SpinnerIcon: React.FC = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ animation: 'spin 0.8s linear infinite' }}>
    <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
  </svg>
);

const ResetPasswordPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token') ?? '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [touched, setTouched] = useState({ password: false, confirmPassword: false });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [bannerError, setBannerError] = useState('');
  const [success, setSuccess] = useState(false);

  const passwordError = touched.password ? validatePassword(password) : '';
  const confirmError = touched.confirmPassword ? validateConfirmPassword(password, confirmPassword) : '';
  const strengthLevel = getStrengthLevel(password);

  const handleBlurPassword = useCallback(() => {
    setTouched((prev) => ({ ...prev, password: true }));
  }, []);

  const handleBlurConfirm = useCallback(() => {
    setTouched((prev) => ({ ...prev, confirmPassword: true }));
  }, []);

  const handleSubmit = useCallback(
    async (e: React.FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      setBannerError('');

      if (!token) {
        setBannerError(fieldErrors.token.missing);
        return;
      }

      setTouched({ password: true, confirmPassword: true });
      const pErr = validatePassword(password);
      const cErr = validateConfirmPassword(password, confirmPassword);
      if (pErr || cErr) return;

      setIsSubmitting(true);
      try {
        await resetPassword({ token, password, confirmPassword });
        setSuccess(true);
        setTimeout(() => navigate('/login'), 3000);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : 'Something went wrong. Please try again.';
        setBannerError(message);
      } finally {
        setIsSubmitting(false);
      }
    },
    [token, password, confirmPassword, navigate],
  );

  const isDisabled = isSubmitting || success;

  return (
    <>
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .auth-input:focus {
          border-color: var(--color-accent-primary);
          box-shadow: var(--elevation-focus);
        }
        .auth-submit-btn:hover:not(:disabled) {
          background-color: var(--color-accent-primary-hover);
        }
        .auth-submit-btn:active:not(:disabled) {
          background-color: var(--color-accent-primary-active);
        }
        .auth-link:hover {
          text-decoration: underline;
        }
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
          --font-family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
          --font-family-mono: 'JetBrains Mono', 'Courier New', monospace;
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
      `}</style>
      <div className="auth-app" style={styles.app}>
        <div className="auth-branding" style={styles.branding}>
          <p style={styles.brandName}>auth-starter</p>
        </div>
        <div className="auth-card" style={styles.card} role="main">
          <h1 className="auth-card__title" style={styles.title}>Set new password</h1>
          <p className="auth-card__subtitle" style={styles.subtitle}>
            Your new password must meet the requirements below.
          </p>

          <div aria-live="polite" aria-atomic="true">
            {bannerError && (
              <div
                className="auth-card__banner auth-card__banner--error"
                role="alert"
                style={{ ...styles.banner, ...styles.bannerError }}
              >
                {bannerError}
              </div>
            )}
            {success && (
              <div
                className="auth-card__banner auth-card__banner--success"
                role="status"
                style={{ ...styles.banner, ...styles.bannerSuccess }}
              >
                Password reset successfully. Redirecting to login…
              </div>
            )}
          </div>

          {!success && (
            <form onSubmit={handleSubmit} noValidate>
              <div className="auth-card__field" style={styles.field}>
                <label
                  htmlFor="reset-password"
                  className="auth-card__label"
                  style={styles.label}
                >
                  New Password
                </label>
                <div className="auth-card__input-wrapper" style={styles.inputWrapper}>
                  <input
                    id="reset-password"
                    className="auth-input"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onBlur={handleBlurPassword}
                    disabled={isDisabled}
                    autoComplete="new-password"
                    aria-required="true"
                    aria-invalid={!!passwordError}
                    aria-describedby={passwordError ? 'reset-password-error' : 'password-strength-label'}
                    style={{
                      ...styles.input,
                      ...(passwordError ? styles.inputError : {}),
                    }}
                  />
                  <button
                    type="button"
                    className="auth-card__toggle"
                    style={styles.toggleBtn}
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    tabIndex={0}
                  >
                    <EyeIcon visible={showPassword} />
                  </button>
                </div>
                {password && (
                  <>
                    <div className="auth-card__strength-bar" style={styles.strengthBar} aria-hidden="true">
                      {[1, 2, 3, 4].map((seg) => (
                        <div
                          key={seg}
                          style={{
                            ...styles.strengthSegment,
                            backgroundColor:
                              seg <= strengthLevel
                                ? strengthColors[strengthLevel]
                                : 'var(--color-border)',
                          }}
                        />
                      ))}
                    </div>
                    <span
                      id="password-strength-label"
                      className="auth-card__strength-label"
                      style={styles.strengthLabel}
                    >
                      {strengthLevel > 0 ? `Strength: ${strengthLabels[strengthLevel]}` : ''}
                    </span>
                  </>
                )}
                {passwordError && (
                  <span
                    id="reset-password-error"
                    className="auth-card__error field--error"
                    style={styles.errorMsg}
                    role="alert"
                  >
                    {passwordError}
                  </span>
                )}
              </div>

              <div className="auth-card__field" style={styles.field}>
                <label
                  htmlFor="reset-confirm-password"
                  className="auth-card__label"
                  style={styles.label}
                >
                  Confirm New Password
                </label>
                <div className="auth-card__input-wrapper" style={styles.inputWrapper}>
                  <input
                    id="reset-confirm-password"
                    className="auth-input"
                    type={showConfirm ? 'text' : 'password'}
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    onBlur={handleBlurConfirm}
                    disabled={isDisabled}
                    autoComplete="new-password"
                    aria-required="true"
                    aria-invalid={!!confirmError}
                    aria-describedby={confirmError ? 'reset-confirm-error' : undefined}
                    style={{
                      ...styles.input,
                      ...(confirmError ? styles.inputError : {}),
                    }}
                  />
                  <button
                    type="button"
                    className="auth-card__toggle"
                    style={styles.toggleBtn}
                    onClick={() => setShowConfirm((v) => !v)}
                    aria-label={showConfirm ? 'Hide confirm password' : 'Show confirm password'}
                    tabIndex={0}
                  >
                    <EyeIcon visible={showConfirm} />
                  </button>
                </div>
                {confirmError && (
                  <span
                    id="reset-confirm-error"
                    className="auth-card__error field--error"
                    style={styles.errorMsg}
                    role="alert"
                  >
                    {confirmError}
                  </span>
                )}
              </div>

              <button
                type="submit"
                className="auth-submit-btn"
                style={{
                  ...styles.submitBtn,
                  ...(isDisabled ? styles.submitBtnDisabled : {}),
                }}
                disabled={isDisabled}
                aria-busy={isSubmitting}
              >
                {isSubmitting && <SpinnerIcon />}
                {isSubmitting ? 'Resetting…' : 'Reset Password'}
              </button>
            </form>
          )}

          <div className="auth-card__footer" style={styles.backToLogin}>
            <a href="/login" className="auth-link" style={styles.link}>
              Back to login
            </a>
          </div>
        </div>
      </div>
    </>
  );
};

export default ResetPasswordPage;
