// Client-side mirror of validation-rules.md
// Rule order and exact messages match the server-side rules verbatim.

// Password policy mirrored from config (capabilities.yaml):
//   min_length: 8
//   require_uppercase: true
//   require_lowercase: true
//   require_number: true
//   require_special_character: false

export interface ValidationResult {
  valid: boolean;
  message: string | null;
}

export interface PasswordStrength {
  hasMinLength: boolean;
  hasUppercase: boolean;
  hasLowercase: boolean;
  hasNumber: boolean;
  score: number; // 0-4
}

// ---------------------------------------------------------------------------
// Individual field validators
// ---------------------------------------------------------------------------

export function validateFullName(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Full name is required.' };
  }
  if (value.trim().length < 2) {
    return { valid: false, message: 'Full name must be at least 2 characters.' };
  }
  if (value.trim().length > 100) {
    return { valid: false, message: 'Full name must not exceed 100 characters.' };
  }
  return { valid: true, message: null };
}

export function validateEmail(value: string): ValidationResult {
  if (!value || value.trim().length === 0) {
    return { valid: false, message: 'Email is required.' };
  }
  // RFC-5322 simplified pattern
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(value.trim())) {
    return { valid: false, message: 'Enter a valid email address.' };
  }
  return { valid: true, message: null };
}

export function validatePassword(value: string): ValidationResult {
  if (!value || value.length === 0) {
    return { valid: false, message: 'Password is required.' };
  }
  if (value.length < 8) {
    return { valid: false, message: 'Password must be at least 8 characters.' };
  }
  if (!/[A-Z]/.test(value)) {
    return { valid: false, message: 'Password must contain at least one uppercase letter.' };
  }
  if (!/[a-z]/.test(value)) {
    return { valid: false, message: 'Password must contain at least one lowercase letter.' };
  }
  if (!/[0-9]/.test(value)) {
    return { valid: false, message: 'Password must contain at least one number.' };
  }
  // require_special_character is false per config — no special-char rule
  return { valid: true, message: null };
}

export function validateConfirmPassword(
  password: string,
  confirmPassword: string,
): ValidationResult {
  if (!confirmPassword || confirmPassword.length === 0) {
    return { valid: false, message: 'Please confirm your password.' };
  }
  if (password !== confirmPassword) {
    return { valid: false, message: 'Passwords do not match.' };
  }
  return { valid: true, message: null };
}

export function validateTerms(accepted: boolean): ValidationResult {
  if (!accepted) {
    return { valid: false, message: 'You must accept the Terms of Service to register.' };
  }
  return { valid: true, message: null };
}

// ---------------------------------------------------------------------------
// Password strength meter
// Checks exactly the four active rules: length >= 8, uppercase, lowercase, number.
// Special character is NOT required (require_special_character=false).
// ---------------------------------------------------------------------------

export function getPasswordStrength(value: string): PasswordStrength {
  const hasMinLength = value.length >= 8;
  const hasUppercase = /[A-Z]/.test(value);
  const hasLowercase = /[a-z]/.test(value);
  const hasNumber = /[0-9]/.test(value);

  const score = [hasMinLength, hasUppercase, hasLowercase, hasNumber].filter(Boolean).length;

  return {
    hasMinLength,
    hasUppercase,
    hasLowercase,
    hasNumber,
    score,
  };
}

// ---------------------------------------------------------------------------
// Form-level validators (run all rules and return a map of field -> message)
// ---------------------------------------------------------------------------

export interface LoginFormErrors {
  email?: string;
  password?: string;
}

export function validateLoginForm(fields: {
  email: string;
  password: string;
}): LoginFormErrors {
  const errors: LoginFormErrors = {};

  const emailResult = validateEmail(fields.email);
  if (!emailResult.valid) {
    errors.email = emailResult.message as string;
  }

  // Login only checks that password is non-empty (server handles policy)
  if (!fields.password || fields.password.length === 0) {
    errors.password = 'Password is required.';
  }

  return errors;
}

export interface RegisterFormErrors {
  full_name?: string;
  email?: string;
  password?: string;
  confirm_password?: string;
  terms?: string;
}

export function validateRegisterForm(fields: {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
  terms: boolean;
}): RegisterFormErrors {
  const errors: RegisterFormErrors = {};

  const fullNameResult = validateFullName(fields.full_name);
  if (!fullNameResult.valid) {
    errors.full_name = fullNameResult.message as string;
  }

  const emailResult = validateEmail(fields.email);
  if (!emailResult.valid) {
    errors.email = emailResult.message as string;
  }

  const passwordResult = validatePassword(fields.password);
  if (!passwordResult.valid) {
    errors.password = passwordResult.message as string;
  }

  const confirmResult = validateConfirmPassword(fields.password, fields.confirm_password);
  if (!confirmResult.valid) {
    errors.confirm_password = confirmResult.message as string;
  }

  const termsResult = validateTerms(fields.terms);
  if (!termsResult.valid) {
    errors.terms = termsResult.message as string;
  }

  return errors;
}

export interface ForgotPasswordFormErrors {
  email?: string;
}

export function validateForgotPasswordForm(fields: {
  email: string;
}): ForgotPasswordFormErrors {
  const errors: ForgotPasswordFormErrors = {};

  const emailResult = validateEmail(fields.email);
  if (!emailResult.valid) {
    errors.email = emailResult.message as string;
  }

  return errors;
}

export interface ResetPasswordFormErrors {
  password?: string;
  confirm_password?: string;
}

export function validateResetPasswordForm(fields: {
  password: string;
  confirm_password: string;
}): ResetPasswordFormErrors {
  const errors: ResetPasswordFormErrors = {};

  const passwordResult = validatePassword(fields.password);
  if (!passwordResult.valid) {
    errors.password = passwordResult.message as string;
  }

  const confirmResult = validateConfirmPassword(fields.password, fields.confirm_password);
  if (!confirmResult.valid) {
    errors.confirm_password = confirmResult.message as string;
  }

  return errors;
}

// ---------------------------------------------------------------------------
// Utility: check if a form-errors object has no errors
// ---------------------------------------------------------------------------

export function isFormValid(errors: Record<string, string | undefined>): boolean {
  return Object.values(errors).every((msg) => msg === undefined);
}
