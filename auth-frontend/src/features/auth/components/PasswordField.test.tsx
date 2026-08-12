import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import PasswordField from './PasswordField';

const noop = () => {};

describe('PasswordField', () => {
  it('renders the label', () => {
    render(<PasswordField id="password" label="Password" value="" onChange={noop} />);
    expect(screen.getByText('Password')).toBeTruthy();
  });

  it('renders input with type password by default', () => {
    render(<PasswordField id="password" label="Password" value="" onChange={noop} />);
    const input = document.getElementById('password') as HTMLInputElement;
    expect(input.type).toBe('password');
  });

  it('renders toggle button with aria-label Show password initially', () => {
    render(<PasswordField id="password" label="Password" value="" onChange={noop} />);
    expect(screen.getByRole('button', { name: 'Show password' })).toBeTruthy();
  });

  it('toggles input type to text when Show password is clicked', () => {
    render(<PasswordField id="password" label="Password" value="" onChange={noop} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    const input = document.getElementById('password') as HTMLInputElement;
    expect(input.type).toBe('text');
  });

  it('toggles button label to Hide password after clicking show', () => {
    render(<PasswordField id="password" label="Password" value="" onChange={noop} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    expect(screen.getByRole('button', { name: 'Hide password' })).toBeTruthy();
  });

  it('toggles back to password type when Hide password is clicked', () => {
    render(<PasswordField id="password" label="Password" value="" onChange={noop} />);
    fireEvent.click(screen.getByRole('button', { name: 'Show password' }));
    fireEvent.click(screen.getByRole('button', { name: 'Hide password' }));
    const input = document.getElementById('password') as HTMLInputElement;
    expect(input.type).toBe('password');
  });

  it('calls onChange when user types', () => {
    const handleChange = jest.fn();
    render(<PasswordField id="password" label="Password" value="" onChange={handleChange} />);
    fireEvent.change(document.getElementById('password')!, { target: { value: 'abc' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it('calls onBlur when input loses focus', () => {
    const handleBlur = jest.fn();
    render(
      <PasswordField id="password" label="Password" value="" onChange={noop} onBlur={handleBlur} />
    );
    fireEvent.blur(document.getElementById('password')!);
    expect(handleBlur).toHaveBeenCalledTimes(1);
  });

  it('renders error message and applies error class', () => {
    const { container } = render(
      <PasswordField id="password" label="Password" value="" onChange={noop} error="Too short" />
    );
    expect(screen.getByRole('alert').textContent).toBe('Too short');
    expect(container.querySelector('.field--error')).toBeTruthy();
  });

  it('sets aria-invalid when error is present', () => {
    render(
      <PasswordField id="password" label="Password" value="" onChange={noop} error="Required" />
    );
    expect(document.getElementById('password')?.getAttribute('aria-invalid')).toBe('true');
  });

  it('does not set aria-invalid when no error', () => {
    render(<PasswordField id="password" label="Password" value="" onChange={noop} />);
    expect(document.getElementById('password')?.getAttribute('aria-invalid')).toBeNull();
  });

  it('renders hint when no error', () => {
    render(
      <PasswordField id="password" label="Password" value="" onChange={noop} hint="Min 8 chars" />
    );
    expect(screen.getByText('Min 8 chars')).toBeTruthy();
  });

  it('does not render hint when error is present', () => {
    render(
      <PasswordField
        id="password"
        label="Password"
        value=""
        onChange={noop}
        hint="Min 8 chars"
        error="Too short"
      />
    );
    expect(screen.queryByText('Min 8 chars')).toBeNull();
  });

  it('shows required asterisk when required=true', () => {
    const { container } = render(
      <PasswordField id="password" label="Password" value="" onChange={noop} required />
    );
    expect(container.querySelector('.field__required')).toBeTruthy();
  });

  it('disables the input and toggle button when disabled=true', () => {
    render(<PasswordField id="password" label="Password" value="" onChange={noop} disabled />);
    expect((document.getElementById('password') as HTMLInputElement).disabled).toBe(true);
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(true);
  });

  it('passes placeholder to input', () => {
    render(
      <PasswordField id="password" label="Password" value="" onChange={noop} placeholder="••••••" />
    );
    expect(document.getElementById('password')?.getAttribute('placeholder')).toBe('••••••');
  });

  it('passes autoComplete to input', () => {
    render(
      <PasswordField
        id="password"
        label="Password"
        value=""
        onChange={noop}
        autoComplete="current-password"
      />
    );
    expect(document.getElementById('password')?.getAttribute('autocomplete')).toBe(
      'current-password'
    );
  });

  it('sets aria-describedby to error id when error is present', () => {
    render(
      <PasswordField id="password" label="Password" value="" onChange={noop} error="Bad" />
    );
    expect(document.getElementById('password')?.getAttribute('aria-describedby')).toBe(
      'password-error'
    );
  });

  it('sets aria-describedby to hint id when hint present and no error', () => {
    render(
      <PasswordField id="password" label="Password" value="" onChange={noop} hint="A hint" />
    );
    expect(document.getElementById('password')?.getAttribute('aria-describedby')).toBe(
      'password-hint'
    );
  });
});
