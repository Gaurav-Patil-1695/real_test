import {
  validateFullName,
  validateEmail,
  validatePassword,
  validateConfirmPassword,
  validateTerms,
  getPasswordStrength,
  validateLoginForm,
  validateRegisterForm,
  validateForgotPasswordForm,
  validateResetPasswordForm,
  isFormValid,
} from './validation';

// ---------------------------------------------------------------------------
// validateFullName
// ---------------------------------------------------------------------------
describe('validateFullName', () => {
  test('returns invalid for empty string', () => {
    const result = validateFullName('');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Full name is required.');
  });

  test('returns invalid for whitespace-only string', () => {
    const result = validateFullName('   ');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Full name is required.');
  });

  test('returns invalid for single character after trim', () => {
    const result = validateFullName('A');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Full name must be at least 2 characters.');
  });

  test('returns invalid for name exceeding 100 characters', () => {
    const longName = 'A'.repeat(101);
    const result = validateFullName(longName);
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Full name must not exceed 100 characters.');
  });

  test('returns valid for exactly 2 characters', () => {
    const result = validateFullName('Jo');
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });

  test('returns valid for exactly 100 characters', () => {
    const name = 'A'.repeat(100);
    const result = validateFullName(name);
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });

  test('returns valid for a normal name', () => {
    const result = validateFullName('John Doe');
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });

  test('trims whitespace before checking length', () => {
    // " A " trims to "A" which is length 1
    const result = validateFullName(' A ');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Full name must be at least 2 characters.');
  });
});

// ---------------------------------------------------------------------------
// validateEmail
// ---------------------------------------------------------------------------
describe('validateEmail', () => {
  test('returns invalid for empty string', () => {
    const result = validateEmail('');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Email is required.');
  });

  test('returns invalid for whitespace-only string', () => {
    const result = validateEmail('   ');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Email is required.');
  });

  test('returns invalid for missing @ symbol', () => {
    const result = validateEmail('notanemail.com');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Enter a valid email address.');
  });

  test('returns invalid for missing domain', () => {
    const result = validateEmail('user@');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Enter a valid email address.');
  });

  test('returns invalid for missing TLD', () => {
    const result = validateEmail('user@domain');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Enter a valid email address.');
  });

  test('returns invalid for email with spaces', () => {
    const result = validateEmail('user @domain.com');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Enter a valid email address.');
  });

  test('returns valid for a proper email address', () => {
    const result = validateEmail('user@example.com');
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });

  test('returns valid for email with subdomain', () => {
    const result = validateEmail('user@mail.example.com');
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });

  test('trims whitespace before validation', () => {
    const result = validateEmail('  user@example.com  ');
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// validatePassword
// ---------------------------------------------------------------------------
describe('validatePassword', () => {
  test('returns invalid for empty string', () => {
    const result = validatePassword('');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Password is required.');
  });

  test('returns invalid for password shorter than 8 characters', () => {
    const result = validatePassword('Ab1defg');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Password must be at least 8 characters.');
  });

  test('returns invalid for password without uppercase letter', () => {
    const result = validatePassword('abcdefg1');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Password must contain at least one uppercase letter.');
  });

  test('returns invalid for password without lowercase letter', () => {
    const result = validatePassword('ABCDEFG1');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Password must contain at least one lowercase letter.');
  });

  test('returns invalid for password without number', () => {
    const result = validatePassword('Abcdefgh');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Password must contain at least one number.');
  });

  test('returns valid for password meeting all requirements', () => {
    const result = validatePassword('Abcdefg1');
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });

  test('returns valid for password with special characters (not required but allowed)', () => {
    const result = validatePassword('Abcdef1!');
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });

  test('returns valid for password of exactly 8 characters', () => {
    const result = validatePassword('Abcdef1g');
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// validateConfirmPassword
// ---------------------------------------------------------------------------
describe('validateConfirmPassword', () => {
  test('returns invalid when confirm password is empty', () => {
    const result = validateConfirmPassword('Password1', '');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Please confirm your password.');
  });

  test('returns invalid when passwords do not match', () => {
    const result = validateConfirmPassword('Password1', 'Password2');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Passwords do not match.');
  });

  test('returns valid when passwords match', () => {
    const result = validateConfirmPassword('Password1', 'Password1');
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });

  test('returns invalid when passwords differ by case', () => {
    const result = validateConfirmPassword('Password1', 'password1');
    expect(result.valid).toBe(false);
    expect(result.message).toBe('Passwords do not match.');
  });
});

// ---------------------------------------------------------------------------
// validateTerms
// ---------------------------------------------------------------------------
describe('validateTerms', () => {
  test('returns invalid when terms not accepted', () => {
    const result = validateTerms(false);
    expect(result.valid).toBe(false);
    expect(result.message).toBe('You must accept the Terms of Service to register.');
  });

  test('returns valid when terms are accepted', () => {
    const result = validateTerms(true);
    expect(result.valid).toBe(true);
    expect(result.message).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// getPasswordStrength
// ---------------------------------------------------------------------------
describe('getPasswordStrength', () => {
  test('returns score 0 for empty string', () => {
    const strength = getPasswordStrength('');
    expect(strength.hasMinLength).toBe(false);
    expect(strength.hasUppercase).toBe(false);
    expect(strength.hasLowercase).toBe(false);
    expect(strength.hasNumber).toBe(false);
    expect(strength.score).toBe(0);
  });

  test('returns score 1 for only lowercase short password', () => {
    const strength = getPasswordStrength('abc');
    expect(strength.hasMinLength).toBe(false);
    expect(strength.hasUppercase).toBe(false);
    expect(strength.hasLowercase).toBe(true);
    expect(strength.hasNumber).toBe(false);
    expect(strength.score).toBe(1);
  });

  test('returns score 2 for lowercase + number, short', () => {
    const strength = getPasswordStrength('abc1');
    expect(strength.hasMinLength).toBe(false);
    expect(strength.hasUppercase).toBe(false);
    expect(strength.hasLowercase).toBe(true);
    expect(strength.hasNumber).toBe(true);
    expect(strength.score).toBe(2);
  });

  test('returns score 3 for lowercase + uppercase + number, short', () => {
    const strength = getPasswordStrength('Abc1');
    expect(strength.hasMinLength).toBe(false);
    expect(strength.hasUppercase).toBe(true);
    expect(strength.hasLowercase).toBe(true);
    expect(strength.hasNumber).toBe(true);
    expect(strength.score).toBe(3);
  });

  test('returns score 4 for password meeting all requirements', () => {
    const strength = getPasswordStrength('Abcdef1g');
    expect(strength.hasMinLength).toBe(true);
    expect(strength.hasUppercase).toBe(true);
    expect(strength.hasLowercase).toBe(true);
    expect(strength.hasNumber).toBe(true);
    expect(strength.score).toBe(4);
  });

  test('counts min length correctly at exactly 8 chars', () => {
    const strength = getPasswordStrength('abcdefgh');
    expect(strength.hasMinLength).toBe(true);
  });

  test('counts min length false at 7 chars', () => {
    const strength = getPasswordStrength('abcdefg');
    expect(strength.hasMinLength).toBe(false);
  });

  test('does not include special characters in score', () => {
    // Only lowercase + special chars — score should be 1
    const strength = getPasswordStrength('abc!@#$');
    expect(strength.score).toBe(1);
  });
});

// ---------------------------------------------------------------------------
// validateLoginForm
// ---------------------------------------------------------------------------
describe('validateLoginForm', () => {
  test('returns errors for both empty fields', () => {
    const errors = validateLoginForm({ email: '', password: '' });
    expect(errors.email).toBe('Email is required.');
    expect(errors.password).toBe('Password is required.');
  });

  test('returns email error for invalid email', () => {
    const errors = validateLoginForm({ email: 'notvalid', password: 'anypassword' });
    expect(errors.email).toBe('Enter a valid email address.');
    expect(errors.password).toBeUndefined();
  });

  test('returns password error when password is empty', () => {
    const errors = validateLoginForm({ email: 'user@example.com', password: '' });
    expect(errors.email).toBeUndefined();
    expect(errors.password).toBe('Password is required.');
  });

  test('returns no errors for valid credentials', () => {
    const errors = validateLoginForm({ email: 'user@example.com', password: 'anypassword' });
    expect(errors.email).toBeUndefined();
    expect(errors.password).toBeUndefined();
  });

  test('login does not enforce password policy (only non-empty)', () => {
    // A password that would fail policy but is non-empty should pass login validation
    const errors = validateLoginForm({ email: 'user@example.com', password: 'weakpass' });
    expect(errors.password).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// validateRegisterForm
// ---------------------------------------------------------------------------
describe('validateRegisterForm', () => {
  const validFields = {
    full_name: 'John Doe',
    email: 'john@example.com',
    password: 'Abcdef1g',
    confirm_password: 'Abcdef1g',
    terms: true,
  };

  test('returns no errors for fully valid form', () => {
    const errors = validateRegisterForm(validFields);
    expect(errors.full_name).toBeUndefined();
    expect(errors.email).toBeUndefined();
    expect(errors.password).toBeUndefined();
    expect(errors.confirm_password).toBeUndefined();
    expect(errors.terms).toBeUndefined();
  });

  test('returns full_name error for empty name', () => {
    const errors = validateRegisterForm({ ...validFields, full_name: '' });
    expect(errors.full_name).toBe('Full name is required.');
  });

  test('returns email error for invalid email', () => {
    const errors = validateRegisterForm({ ...validFields, email: 'bademail' });
    expect(errors.email).toBe('Enter a valid email address.');
  });

  test('returns password error when password is too short', () => {
    const errors = validateRegisterForm({
      ...validFields,
      password: 'Ab1',
      confirm_password: 'Ab1',
    });
    expect(errors.password).toBe('Password must be at least 8 characters.');
  });

  test('returns confirm_password error when passwords do not match', () => {
    const errors = validateRegisterForm({
      ...validFields,
      confirm_password: 'Different1',
    });
    expect(errors.confirm_password).toBe('Passwords do not match.');
  });

  test('returns terms error when terms not accepted', () => {
    const errors = validateRegisterForm({ ...validFields, terms: false });
    expect(errors.terms).toBe('You must accept the Terms of Service to register.');
  });

  test('returns multiple errors simultaneously', () => {
    const errors = validateRegisterForm({
      full_name: '',
      email: '',
      password: '',
      confirm_password: '',
      terms: false,
    });
    expect(errors.full_name).toBeDefined();
    expect(errors.email).toBeDefined();
    expect(errors.password).toBeDefined();
    expect(errors.confirm_password).toBeDefined();
    expect(errors.terms).toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// validateForgotPasswordForm
// ---------------------------------------------------------------------------
describe('validateForgotPasswordForm', () => {
  test('returns email error for empty email', () => {
    const errors = validateForgotPasswordForm({ email: '' });
    expect(errors.email).toBe('Email is required.');
  });

  test('returns email error for invalid email', () => {
    const errors = validateForgotPasswordForm({ email: 'notvalid' });
    expect(errors.email).toBe('Enter a valid email address.');
  });

  test('returns no errors for valid email', () => {
    const errors = validateForgotPasswordForm({ email: 'user@example.com' });
    expect(errors.email).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// validateResetPasswordForm
// ---------------------------------------------------------------------------
describe('validateResetPasswordForm', () => {
  test('returns errors for empty fields', () => {
    const errors = validateResetPasswordForm({ password: '', confirm_password: '' });
    expect(errors.password).toBe('Password is required.');
    expect(errors.confirm_password).toBe('Please confirm your password.');
  });

  test('returns password error for weak password', () => {
    const errors = validateResetPasswordForm({
      password: 'weakpass',
      confirm_password: 'weakpass',
    });
    expect(errors.password).toBeDefined();
  });

  test('returns confirm_password error when passwords do not match', () => {
    const errors = validateResetPasswordForm({
      password: 'Abcdef1g',
      confirm_password: 'Different1',
    });
    expect(errors.confirm_password).toBe('Passwords do not match.');
  });

  test('returns no errors for valid matching passwords', () => {
    const errors = validateResetPasswordForm({
      password: 'Abcdef1g',
      confirm_password: 'Abcdef1g',
    });
    expect(errors.password).toBeUndefined();
    expect(errors.confirm_password).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// isFormValid
// ---------------------------------------------------------------------------
describe('isFormValid', () => {
  test('returns true when all values are undefined', () => {
    expect(isFormValid({ email: undefined, password: undefined })).toBe(true);
  });

  test('returns true for empty object', () => {
    expect(isFormValid({})).toBe(true);
  });

  test('returns false when any value is a string message', () => {
    expect(isFormValid({ email: 'Email is required.', password: undefined })).toBe(false);
  });

  test('returns false when all values are error messages', () => {
    expect(isFormValid({ email: 'Email is required.', password: 'Password is required.' })).toBe(false);
  });

  test('returns true for valid register form errors object', () => {
    const errors = { full_name: undefined, email: undefined, password: undefined };
    expect(isFormValid(errors)).toBe(true);
  });

  test('returns false for invalid register form errors object', () => {
    const errors = { full_name: 'Full name is required.', email: undefined };
    expect(isFormValid(errors)).toBe(false);
  });
});
