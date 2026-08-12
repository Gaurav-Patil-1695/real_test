import React from 'react';

interface Rule {
  key: string;
  label: string;
  test: (password: string) => boolean;
}

const RULES: Rule[] = [
  {
    key: 'length',
    label: 'At least 8 characters',
    test: (password) => password.length >= 8,
  },
  {
    key: 'uppercase',
    label: 'At least one uppercase letter',
    test: (password) => /[A-Z]/.test(password),
  },
  {
    key: 'lowercase',
    label: 'At least one lowercase letter',
    test: (password) => /[a-z]/.test(password),
  },
  {
    key: 'number',
    label: 'At least one number',
    test: (password) => /[0-9]/.test(password),
  },
];

interface PasswordStrengthMeterProps {
  password: string;
}

function PasswordStrengthMeter({ password }: PasswordStrengthMeterProps) {
  const results = RULES.map((rule) => ({
    key: rule.key,
    label: rule.label,
    passed: rule.test(password),
  }));

  const passedCount = results.filter((r) => r.passed).length;
  const total = RULES.length;

  const strengthLabel =
    passedCount === 0
      ? 'None'
      : passedCount === 1
      ? 'Weak'
      : passedCount === 2
      ? 'Fair'
      : passedCount === 3
      ? 'Good'
      : 'Strong';

  const strengthModifier =
    passedCount === 0
      ? 'none'
      : passedCount === 1
      ? 'weak'
      : passedCount === 2
      ? 'fair'
      : passedCount === 3
      ? 'good'
      : 'strong';

  if (password.length === 0) {
    return null;
  }

  return (
    <div className="password-strength" aria-label="Password strength">
      <div
        className="password-strength__track"
        role="meter"
        aria-valuenow={passedCount}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label={`Password strength: ${strengthLabel}`}
      >
        {Array.from({ length: total }).map((_, index) => (
          <div
            key={index}
            className={[
              'password-strength__segment',
              index < passedCount
                ? `password-strength__segment--${strengthModifier}`
                : 'password-strength__segment--empty',
            ].join(' ')}
          />
        ))}
      </div>
      <span className={`password-strength__label password-strength__label--${strengthModifier}`}>
        {strengthLabel}
      </span>
      <ul className="password-strength__checklist" aria-label="Password requirements">
        {results.map((result) => (
          <li
            key={result.key}
            className={[
              'password-strength__check',
              result.passed
                ? 'password-strength__check--passed'
                : 'password-strength__check--failed',
            ].join(' ')}
          >
            <span
              className="password-strength__check-icon"
              aria-hidden="true"
            >
              {result.passed ? (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  focusable="false"
                >
                  <circle cx="7" cy="7" r="7" fill="var(--color-success)" />
                  <path
                    d="M4 7L6 9L10 5"
                    stroke="var(--color-text-on-accent)"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              ) : (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 14 14"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  focusable="false"
                >
                  <circle cx="7" cy="7" r="7" fill="var(--color-border)" />
                  <path
                    d="M4 7L6 9L10 5"
                    stroke="var(--color-text-muted)"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              )}
            </span>
            <span
              className="password-strength__check-text"
              aria-label={`${result.label}: ${result.passed ? 'passed' : 'not met'}`}
            >
              {result.label}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default PasswordStrengthMeter;
