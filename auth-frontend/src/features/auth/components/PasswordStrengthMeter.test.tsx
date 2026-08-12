import React from 'react';
import { render, screen } from '@testing-library/react';
import PasswordStrengthMeter from './PasswordStrengthMeter';

describe('PasswordStrengthMeter', () => {
  it('returns null when password is empty string', () => {
    const { container } = render(<PasswordStrengthMeter password="" />);
    expect(container.firstChild).toBeNull();
  });

  it('renders when password is non-empty', () => {
    const { container } = render(<PasswordStrengthMeter password="a" />);
    expect(container.querySelector('.password-strength')).toBeTruthy();
  });

  it('shows Weak strength for a single lowercase letter', () => {
    render(<PasswordStrengthMeter password="a" />);
    expect(screen.getByText('Weak')).toBeTruthy();
  });

  it('shows Fair strength for a password with 2 rules passing', () => {
    // 'Ab' — uppercase + lowercase, no number, length < 8 => 2 rules pass
    render(<PasswordStrengthMeter password="Ab" />);
    expect(screen.getByText('Fair')).toBeTruthy();
  });

  it('shows Good strength for a password passing 3 rules', () => {
    // 'Ab1' — uppercase + lowercase + number, length < 8 => 3 rules pass
    render(<PasswordStrengthMeter password="Ab1" />);
    expect(screen.getByText('Good')).toBeTruthy();
  });

  it('shows Strong strength for a password passing all 4 rules', () => {
    // 'Ab1cdefg' — length>=8, uppercase, lowercase, number
    render(<PasswordStrengthMeter password="Ab1cdefg" />);
    expect(screen.getByText('Strong')).toBeTruthy();
  });

  it('renders 4 segments in the meter track', () => {
    const { container } = render(<PasswordStrengthMeter password="a" />);
    const segments = container.querySelectorAll('.password-strength__segment');
    expect(segments.length).toBe(4);
  });

  it('has meter role with correct aria attributes', () => {
    render(<PasswordStrengthMeter password="Ab1cdefg" />);
    const meter = screen.getByRole('meter');
    expect(meter.getAttribute('aria-valuemin')).toBe('0');
    expect(meter.getAttribute('aria-valuemax')).toBe('4');
    expect(meter.getAttribute('aria-valuenow')).toBe('4');
  });

  it('meter label reflects strength', () => {
    render(<PasswordStrengthMeter password="Ab1cdefg" />);
    const meter = screen.getByRole('meter');
    expect(meter.getAttribute('aria-label')).toBe('Password strength: Strong');
  });

  it('renders all 4 requirement checklist items', () => {
    render(<PasswordStrengthMeter password="x" />);
    const list = screen.getByRole('list', { name: 'Password requirements' });
    expect(list.querySelectorAll('li').length).toBe(4);
  });

  it('marks passed requirements with --passed class', () => {
    const { container } = render(<PasswordStrengthMeter password="abcdefgh" />);
    // length>=8 passes, lowercase passes, no uppercase, no number => 2 passed
    const passed = container.querySelectorAll('.password-strength__check--passed');
    expect(passed.length).toBe(2);
  });

  it('marks failed requirements with --failed class', () => {
    const { container } = render(<PasswordStrengthMeter password="abcdefgh" />);
    const failed = container.querySelectorAll('.password-strength__check--failed');
    expect(failed.length).toBe(2);
  });

  it('aria-label on check text reflects passed/not met', () => {
    render(<PasswordStrengthMeter password="abcdefgh" />);
    // length passes
    const lengthCheck = screen.getByLabelText('At least 8 characters: passed');
    expect(lengthCheck).toBeTruthy();
    // uppercase fails
    const uppercaseCheck = screen.getByLabelText('At least one uppercase letter: not met');
    expect(uppercaseCheck).toBeTruthy();
  });

  it('applies strength modifier class to label', () => {
    const { container } = render(<PasswordStrengthMeter password="Ab1cdefg" />);
    const label = container.querySelector('.password-strength__label--strong');
    expect(label).toBeTruthy();
  });

  it('applies none modifier when only one char that fails all but lowercase', () => {
    // single lowercase: 1 rule (lowercase) passes => 'Weak', not none
    const { container } = render(<PasswordStrengthMeter password="a" />);
    const weakLabel = container.querySelector('.password-strength__label--weak');
    expect(weakLabel).toBeTruthy();
  });

  it('meter aria-valuenow reflects number of passed rules', () => {
    // 'Ab' passes uppercase + lowercase = 2
    render(<PasswordStrengthMeter password="Ab" />);
    const meter = screen.getByRole('meter');
    expect(meter.getAttribute('aria-valuenow')).toBe('2');
  });
});
