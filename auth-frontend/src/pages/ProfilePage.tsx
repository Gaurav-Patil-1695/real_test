import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { me, logout } from '../api/auth';

interface UserProfile {
  id: string;
  full_name: string;
  email: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const styles = `
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
    --elevation-card: 0 12px 32px rgba(15,23,42,0.12);
    --elevation-1: 0 1px 2px rgba(15,23,42,0.06);
    --elevation-2: 0 4px 12px rgba(15,23,42,0.08);
    --elevation-focus: 0 0 0 3px rgba(129,140,248,0.45);
    --family-base: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif;
    --radius-button: 8px;
    --radius-card: 16px;
    --radius-full: 9999px;
    --radius-input: 8px;
    --radius-sm: 4px;
    --space-2xl: 48px;
    --space-lg: 24px;
    --space-md: 16px;
    --space-sm: 8px;
    --space-xl: 32px;
    --space-xs: 4px;
  }

  .profile-layout {
    min-height: 100vh;
    background-color: var(--color-bg-app);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: var(--space-lg);
    font-family: var(--family-base);
  }

  .profile-branding {
    text-align: center;
    margin-bottom: var(--space-lg);
  }

  .profile-branding__title {
    font-size: 30px;
    font-weight: 700;
    line-height: 1.2;
    color: var(--color-accent-primary);
    margin: 0 0 var(--space-xs);
  }

  .profile-branding__subtitle {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    color: var(--color-text-secondary);
    margin: 0;
  }

  .profile-card {
    background-color: var(--color-surface);
    border-radius: var(--radius-card);
    box-shadow: var(--elevation-card);
    padding: var(--space-2xl);
    width: 100%;
    max-width: 480px;
  }

  .profile-card__header {
    display: flex;
    align-items: center;
    gap: var(--space-md);
    margin-bottom: var(--space-xl);
    padding-bottom: var(--space-lg);
    border-bottom: 1px solid var(--color-border);
  }

  .profile-card__avatar {
    width: 64px;
    height: 64px;
    border-radius: var(--radius-full);
    background-color: var(--color-accent-primary);
    color: var(--color-surface);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: 700;
    flex-shrink: 0;
  }

  .profile-card__identity {
    flex: 1;
    min-width: 0;
  }

  .profile-card__name {
    font-size: 18px;
    font-weight: 600;
    line-height: 1.25;
    color: var(--color-text-primary);
    margin: 0 0 var(--space-xs);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .profile-card__email {
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    color: var(--color-text-secondary);
    margin: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .profile-card__badge {
    display: inline-flex;
    align-items: center;
    padding: 2px var(--space-sm);
    border-radius: var(--radius-full);
    font-size: 12px;
    font-weight: 400;
    line-height: 1.5;
  }

  .profile-card__badge--active {
    background-color: #dcfce7;
    color: var(--color-success);
  }

  .profile-card__badge--inactive {
    background-color: #fee2e2;
    color: var(--color-error);
  }

  .profile-card__section {
    margin-bottom: var(--space-xl);
  }

  .profile-card__section-title {
    font-size: 12px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0 0 var(--space-md);
  }

  .profile-card__field {
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
    margin-bottom: var(--space-md);
  }

  .profile-card__field:last-child {
    margin-bottom: 0;
  }

  .profile-card__label {
    font-size: 12px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--color-text-muted);
  }

  .profile-card__value {
    font-size: 16px;
    font-weight: 400;
    line-height: 1.5;
    color: var(--color-text-primary);
    background-color: var(--color-muted-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
  }

  .profile-card__actions {
    display: flex;
    flex-direction: column;
    gap: var(--space-sm);
  }

  .profile-card__btn {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    border-radius: var(--radius-button);
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    cursor: pointer;
    border: none;
    transition: background-color 0.15s ease, box-shadow 0.15s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-sm);
  }

  .profile-card__btn:focus-visible {
    outline: none;
    box-shadow: var(--elevation-focus);
  }

  .profile-card__btn:disabled {
    cursor: not-allowed;
  }

  .profile-card__btn--logout {
    background-color: var(--color-accent-primary);
    color: var(--color-surface);
  }

  .profile-card__btn--logout:hover:not(:disabled) {
    background-color: var(--color-accent-primary-hover);
  }

  .profile-card__btn--logout:active:not(:disabled) {
    background-color: var(--color-accent-primary-active);
  }

  .profile-card__btn--logout:disabled {
    background-color: var(--color-accent-disabled);
  }

  .profile-card__spinner {
    width: 16px;
    height: 16px;
    border: 2px solid rgba(255,255,255,0.4);
    border-top-color: var(--color-surface);
    border-radius: var(--radius-full);
    animation: profile-spin 0.6s linear infinite;
  }

  @keyframes profile-spin {
    to { transform: rotate(360deg); }
  }

  .profile-banner {
    border-radius: var(--radius-input);
    padding: var(--space-sm) var(--space-md);
    font-size: 14px;
    font-weight: 500;
    line-height: 1.5;
    margin-bottom: var(--space-md);
  }

  .profile-banner--error {
    background-color: #fee2e2;
    color: var(--color-error);
    border: 1px solid #fca5a5;
  }

  .profile-skeleton {
    border-radius: var(--radius-sm);
    background: linear-gradient(90deg, var(--color-border) 25%, var(--color-muted-surface) 50%, var(--color-border) 75%);
    background-size: 200% 100%;
    animation: profile-shimmer 1.4s ease infinite;
  }

  @keyframes profile-shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }

  .profile-skeleton--name {
    height: 22px;
    width: 160px;
    margin-bottom: var(--space-xs);
  }

  .profile-skeleton--email {
    height: 16px;
    width: 200px;
  }

  .profile-skeleton--value {
    height: 40px;
    width: 100%;
    border-radius: var(--radius-input);
  }
`;

function getInitials(fullName: string): string {
  return fullName
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0].toUpperCase())
    .join('');
}

function formatDate(isoString: string): string {
  try {
    return new Date(isoString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  } catch {
    return isoString;
  }
}

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [isLoadingProfile, setIsLoadingProfile] = useState<boolean>(true);
  const [isLoggingOut, setIsLoggingOut] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string>('');

  useEffect(() => {
    let cancelled = false;

    const fetchProfile = async () => {
      setIsLoadingProfile(true);
      setErrorMessage('');
      try {
        const data = await me();
        if (!cancelled) {
          setProfile(data as UserProfile);
        }
      } catch {
        if (!cancelled) {
          setErrorMessage('Failed to load profile. Please try again.');
        }
      } finally {
        if (!cancelled) {
          setIsLoadingProfile(false);
        }
      }
    };

    fetchProfile();

    return () => {
      cancelled = true;
    };
  }, []);

  const handleLogout = async () => {
    setIsLoggingOut(true);
    setErrorMessage('');
    try {
      await logout();
      navigate('/login', { replace: true });
    } catch {
      setErrorMessage('Logout failed. Please try again.');
      setIsLoggingOut(false);
    }
  };

  const isDisabled = isLoggingOut;

  return (
    <>
      <style>{styles}</style>
      <div className='profile-layout'>
        <div className='profile-branding'>
          <h1 className='profile-branding__title'>auth-starter</h1>
          <p className='profile-branding__subtitle'>Your account profile</p>
        </div>

        <div className='profile-card'>
          <div
            className='profile-card__header'
            aria-live='polite'
          >
            {isLoadingProfile ? (
              <>
                <div
                  className='profile-card__avatar'
                  aria-hidden='true'
                />
                <div className='profile-card__identity'>
                  <div className='profile-skeleton profile-skeleton--name' />
                  <div className='profile-skeleton profile-skeleton--email' />
                </div>
              </>
            ) : profile ? (
              <>
                <div
                  className='profile-card__avatar'
                  aria-hidden='true'
                >
                  {getInitials(profile.full_name)}
                </div>
                <div className='profile-card__identity'>
                  <p className='profile-card__name'>{profile.full_name}</p>
                  <p className='profile-card__email'>{profile.email}</p>
                </div>
                <span
                  className={`profile-card__badge ${
                    profile.is_active
                      ? 'profile-card__badge--active'
                      : 'profile-card__badge--inactive'
                  }`}
                >
                  {profile.is_active ? 'Active' : 'Inactive'}
                </span>
              </>
            ) : null}
          </div>

          <div
            aria-live='polite'
            aria-atomic='true'
          >
            {errorMessage && (
              <div
                className='profile-banner profile-banner--error'
                role='alert'
              >
                {errorMessage}
              </div>
            )}
          </div>

          {isLoadingProfile ? (
            <div className='profile-card__section'>
              <div className='profile-skeleton profile-skeleton--value' style={{ marginBottom: 'var(--space-md)' }} />
              <div className='profile-skeleton profile-skeleton--value' />
            </div>
          ) : profile ? (
            <div className='profile-card__section'>
              <p className='profile-card__section-title'>Account details</p>

              <div className='profile-card__field'>
                <label className='profile-card__label' htmlFor='profile-full-name'>
                  Full name
                </label>
                <div
                  className='profile-card__value'
                  id='profile-full-name'
                  aria-readonly='true'
                >
                  {profile.full_name}
                </div>
              </div>

              <div className='profile-card__field'>
                <label className='profile-card__label' htmlFor='profile-email'>
                  Email address
                </label>
                <div
                  className='profile-card__value'
                  id='profile-email'
                  aria-readonly='true'
                >
                  {profile.email}
                </div>
              </div>

              <div className='profile-card__field'>
                <label className='profile-card__label' htmlFor='profile-member-since'>
                  Member since
                </label>
                <div
                  className='profile-card__value'
                  id='profile-member-since'
                  aria-readonly='true'
                >
                  {formatDate(profile.created_at)}
                </div>
              </div>
            </div>
          ) : null}

          <div className='profile-card__actions'>
            <button
              type='button'
              className='profile-card__btn profile-card__btn--logout'
              onClick={handleLogout}
              disabled={isDisabled}
              aria-busy={isLoggingOut}
            >
              {isLoggingOut ? (
                <>
                  <span className='profile-card__spinner' aria-hidden='true' />
                  Logging out…
                </>
              ) : (
                'Log out'
              )}
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default ProfilePage;
