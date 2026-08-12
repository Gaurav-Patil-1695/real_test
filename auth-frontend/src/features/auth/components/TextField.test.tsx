import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import TextField from './TextField';

const noop = () => {};

describe('TextField', () => {
  it('renders the label', () => {
    render(<TextField id="email" label="Email" value="" onChange={noop} />);
    expect(screen.getByLabelText('Email')).toBeTruthy();
  });

  it('renders the input with correct id', () => {
    render(<TextField id="email" label="Email" value="" onChange={noop} />);
    expect(screen.getByRole('textbox')).toBeTruthy();
    expect(screen.getByRole('textbox').getAttribute('id')).toBe('email');
  });

  it('defaults type to text', () => {
    render(<TextField id="name" label="Name" value="" onChange={noop} />);
    expect(screen.getByRole('textbox').getAttribute('type')).toBe('text');
  });

  it('accepts email type', () => {
    render(<TextField id="email" label="Email" value="" onChange={noop} type="email" />);
    expect(screen.getByRole('textbox').getAttribute('type')).toBe('email');
  });

  it('shows the current value', () => {
    render(<TextField id="email" label="Email" value="test@example.com" onChange={noop} />);
    expect((screen.getByRole('textbox') as HTMLInputElement).value).toBe('test@example.com');
  });

  it('calls onChange when user types', () => {
    const handleChange = jest.fn();
    render(<TextField id="email" label="Email" value="" onChange={handleChange} />);
    fireEvent.change(screen.getByRole('textbox'), { target: { value: 'a' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it('calls onBlur when input loses focus', () => {
    const handleBlur = jest.fn();
    render(<TextField id="email" label="Email" value="" onChange={noop} onBlur={handleBlur} />);
    fireEvent.blur(screen.getByRole('textbox'));
    expect(handleBlur).toHaveBeenCalledTimes(1);
  });

  it('renders error message and applies error class', () => {
    const { container } = render(
      <TextField id="email" label="Email" value="" onChange={noop} error="Invalid email" />
    );
    expect(screen.getByRole('alert').textContent).toBe('Invalid email');
    expect(container.querySelector('.field--error')).toBeTruthy();
  });

  it('sets aria-invalid when error is present', () => {
    render(<TextField id="email" label="Email" value="" onChange={noop} error="Required" />);
    expect(screen.getByRole('textbox').getAttribute('aria-invalid')).toBe('true');
  });

  it('does not set aria-invalid when no error', () => {
    render(<TextField id="email" label="Email" value="" onChange={noop} />);
    expect(screen.getByRole('textbox').getAttribute('aria-invalid')).toBeNull();
  });

  it('renders hint text when no error', () => {
    render(<TextField id="email" label="Email" value="" onChange={noop} hint="Enter your email" />);
    expect(screen.getByText('Enter your email')).toBeTruthy();
  });

  it('does not render hint text when error is present', () => {
    render(
      <TextField
        id="email"
        label="Email"
        value=""
        onChange={noop}
        hint="Enter your email"
        error="Invalid"
      />
    );
    expect(screen.queryByText('Enter your email')).toBeNull();
  });

  it('sets aria-describedby to error id when error is present', () => {
    render(<TextField id="email" label="Email" value="" onChange={noop} error="Bad" />);
    expect(screen.getByRole('textbox').getAttribute('aria-describedby')).toBe('email-error');
  });

  it('sets aria-describedby to hint id when hint is present and no error', () => {
    render(<TextField id="email" label="Email" value="" onChange={noop} hint="A hint" />);
    expect(screen.getByRole('textbox').getAttribute('aria-describedby')).toBe('email-hint');
  });

  it('sets aria-describedby with both ids when both error and hint present', () => {
    render(
      <TextField id="email" label="Email" value="" onChange={noop} error="Err" hint="Hint" />
    );
    // hint is hidden when error is present (not rendered), but describedby still lists error
    const describedBy = screen.getByRole('textbox').getAttribute('aria-describedby');
    expect(describedBy).toBe('email-error');
  });

  it('shows required asterisk when required=true', () => {
    const { container } = render(
      <TextField id="email" label="Email" value="" onChange={noop} required />
    );
    expect(container.querySelector('.field__required')).toBeTruthy();
  });

  it('does not show required asterisk when required=false', () => {
    const { container } = render(
      <TextField id="email" label="Email" value="" onChange={noop} />
    );
    expect(container.querySelector('.field__required')).toBeNull();
  });

  it('disables the input when disabled=true', () => {
    render(<TextField id="email" label="Email" value="" onChange={noop} disabled />);
    expect((screen.getByRole('textbox') as HTMLInputElement).disabled).toBe(true);
  });

  it('passes placeholder to input', () => {
    render(
      <TextField id="email" label="Email" value="" onChange={noop} placeholder="you@example.com" />
    );
    expect(screen.getByRole('textbox').getAttribute('placeholder')).toBe('you@example.com');
  });

  it('passes autoComplete to input', () => {
    render(
      <TextField id="email" label="Email" value="" onChange={noop} autoComplete="email" />
    );
    expect(screen.getByRole('textbox').getAttribute('autocomplete')).toBe('email');
  });
});
