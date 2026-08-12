import React from 'react';

interface CheckboxProps {
  id: string;
  label: React.ReactNode;
  checked: boolean;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void;
  error?: string;
  disabled?: boolean;
  required?: boolean;
}

function Checkbox({
  id,
  label,
  checked,
  onChange,
  onBlur,
  error,
  disabled = false,
  required = false,
}: CheckboxProps) {
  const errorId = `${id}-error`;

  return (
    <div className={`checkbox-field${error ? ' checkbox-field--error' : ''}`}>
      <label className="checkbox-field__label" htmlFor={id}>
        <input
          id={id}
          type="checkbox"
          className="checkbox-field__input"
          checked={checked}
          onChange={onChange}
          onBlur={onBlur}
          disabled={disabled}
          required={required}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? errorId : undefined}
        />
        <span className="checkbox-field__box" aria-hidden="true" />
        <span className="checkbox-field__text">
          {label}
          {required && (
            <span className="field__required" aria-hidden="true">
              {' '}*
            </span>
          )}
        </span>
      </label>
      {error && (
        <span id={errorId} className="field__error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

export default Checkbox;
