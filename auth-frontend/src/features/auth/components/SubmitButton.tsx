import React from 'react';

interface SubmitButtonProps {
  label: string;
  loadingLabel?: string;
  isLoading?: boolean;
  disabled?: boolean;
}

function SubmitButton({
  label,
  loadingLabel,
  isLoading = false,
  disabled = false,
}: SubmitButtonProps) {
  const isDisabled = disabled || isLoading;

  return (
    <button
      type="submit"
      className={`submit-button${isLoading ? ' submit-button--loading' : ''}`}
      disabled={isDisabled}
      aria-busy={isLoading ? 'true' : undefined}
      aria-disabled={isDisabled ? 'true' : undefined}
    >
      {isLoading && (
        <svg
          className="submit-button__spinner"
          width="18"
          height="18"
          viewBox="0 0 18 18"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden="true"
          focusable="false"
        >
          <circle
            cx="9"
            cy="9"
            r="7"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray="38"
            strokeDashoffset="10"
          />
        </svg>
      )}
      <span className="submit-button__label">
        {isLoading && loadingLabel ? loadingLabel : label}
      </span>
    </button>
  );
}

export default SubmitButton;
