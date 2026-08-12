import { useState, useCallback, ChangeEvent, FocusEvent, FormEvent } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type FieldValues = Record<string, string | boolean>;

export type FieldErrors = Record<string, string>;

export type TouchedFields = Record<string, boolean>;

export type Validator<T extends FieldValues> = (
  values: T
) => FieldErrors;

export interface UseAuthFormOptions<T extends FieldValues> {
  initialValues: T;
  validate: Validator<T>;
  onSubmit: (values: T) => Promise<void>;
}

export interface UseAuthFormReturn<T extends FieldValues> {
  values: T;
  errors: FieldErrors;
  touched: TouchedFields;
  isSubmitting: boolean;
  submitError: string | null;
  submitSuccess: boolean;
  handleChange: (e: ChangeEvent<HTMLInputElement>) => void;
  handleBlur: (e: FocusEvent<HTMLInputElement>) => void;
  handleSubmit: (e: FormEvent<HTMLFormElement>) => void;
  setFieldValue: (name: string, value: string | boolean) => void;
  setSubmitError: (message: string | null) => void;
  reset: () => void;
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuthForm<T extends FieldValues>({
  initialValues,
  validate,
  onSubmit,
}: UseAuthFormOptions<T>): UseAuthFormReturn<T> {
  const [values, setValues] = useState<T>(initialValues);
  const [touched, setTouched] = useState<TouchedFields>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Derive errors on every render so they are always fresh.
  const errors: FieldErrors = validate(values);

  // -------------------------------------------------------------------------
  // Handlers
  // -------------------------------------------------------------------------

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLInputElement>) => {
      const { name, type, checked, value } = e.target;
      const fieldValue: string | boolean = type === 'checkbox' ? checked : value;
      setValues((prev) => ({ ...prev, [name]: fieldValue }));
      // Clear top-level submit error when the user corrects a field.
      setSubmitError(null);
      setSubmitSuccess(false);
    },
    []
  );

  const handleBlur = useCallback(
    (e: FocusEvent<HTMLInputElement>) => {
      const { name } = e.target;
      setTouched((prev) => ({ ...prev, [name]: true }));
    },
    []
  );

  const handleSubmit = useCallback(
    async (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();

      // Mark every field as touched so all inline errors appear on submit.
      const allTouched = Object.keys(values).reduce<TouchedFields>(
        (acc, key) => ({ ...acc, [key]: true }),
        {}
      );
      setTouched(allTouched);

      // Run validation; bail out if any errors exist.
      const validationErrors = validate(values);
      if (Object.keys(validationErrors).length > 0) {
        return;
      }

      setIsSubmitting(true);
      setSubmitError(null);
      setSubmitSuccess(false);

      try {
        await onSubmit(values);
        setSubmitSuccess(true);
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : 'An unexpected error occurred.';
        setSubmitError(message);
      } finally {
        setIsSubmitting(false);
      }
    },
    [values, validate, onSubmit]
  );

  const setFieldValue = useCallback((name: string, value: string | boolean) => {
    setValues((prev) => ({ ...prev, [name]: value }));
    setSubmitError(null);
    setSubmitSuccess(false);
  }, []);

  const reset = useCallback(() => {
    setValues(initialValues);
    setTouched({});
    setIsSubmitting(false);
    setSubmitError(null);
    setSubmitSuccess(false);
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    isSubmitting,
    submitError,
    submitSuccess,
    handleChange,
    handleBlur,
    handleSubmit,
    setFieldValue,
    setSubmitError,
    reset,
  };
}
