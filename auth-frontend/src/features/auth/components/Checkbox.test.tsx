import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Checkbox from './Checkbox';

const noop = () => {};

describe('Checkbox', () => {
  it('renders the label text', () => {
    render(<Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} />);
    expect(screen.getByText('Accept terms')).toBeTruthy();
  });

  it('renders checkbox input with correct id', () => {
    render(<Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} />);
    const input = document.getElementById('terms') as HTMLInputElement;
    expect(input).toBeTruthy();
    expect(input.type).toBe('checkbox');
  });

  it('reflects checked state', () => {
    render(<Checkbox id="terms" label="Accept terms" checked={true} onChange={noop} />);
    const input = document.getElementById('terms') as HTMLInputElement;
    expect(input.checked).toBe(true);
  });

  it('reflects unchecked state', () => {
    render(<Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} />);
    const input = document.getElementById('terms') as HTMLInputElement;
    expect(input.checked).toBe(false);
  });

  it('calls onChange when clicked', () => {
    const handleChange = jest.fn();
    render(<Checkbox id="terms" label="Accept terms" checked={false} onChange={handleChange} />);
    fireEvent.click(document.getElementById('terms')!);
    expect(handleChange).toHaveBeenCalledTimes(1);
  });

  it('calls onBlur when focus leaves', () => {
    const handleBlur = jest.fn();
    render(
      <Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} onBlur={handleBlur} />
    );
    fireEvent.blur(document.getElementById('terms')!);
    expect(handleBlur).toHaveBeenCalledTimes(1);
  });

  it('renders error message and applies error class', () => {
    const { container } = render(
      <Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} error="Required" />
    );
    expect(screen.getByRole('alert').textContent).toBe('Required');
    expect(container.querySelector('.checkbox-field--error')).toBeTruthy();
  });

  it('sets aria-invalid when error is present', () => {
    render(
      <Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} error="Required" />
    );
    const input = document.getElementById('terms') as HTMLInputElement;
    expect(input.getAttribute('aria-invalid')).toBe('true');
  });

  it('does not set aria-invalid when no error', () => {
    render(<Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} />);
    const input = document.getElementById('terms') as HTMLInputElement;
    expect(input.getAttribute('aria-invalid')).toBeNull();
  });

  it('sets aria-describedby when error is present', () => {
    render(
      <Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} error="Required" />
    );
    const input = document.getElementById('terms') as HTMLInputElement;
    expect(input.getAttribute('aria-describedby')).toBe('terms-error');
  });

  it('does not set aria-describedby when no error', () => {
    render(<Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} />);
    const input = document.getElementById('terms') as HTMLInputElement;
    expect(input.getAttribute('aria-describedby')).toBeNull();
  });

  it('shows required asterisk when required=true', () => {
    const { container } = render(
      <Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} required />
    );
    expect(container.querySelector('.field__required')).toBeTruthy();
  });

  it('does not show required asterisk when required=false', () => {
    const { container } = render(
      <Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} />
    );
    expect(container.querySelector('.field__required')).toBeNull();
  });

  it('disables the input when disabled=true', () => {
    render(<Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} disabled />);
    const input = document.getElementById('terms') as HTMLInputElement;
    expect(input.disabled).toBe(true);
  });

  it('renders React node as label', () => {
    render(
      <Checkbox
        id="terms"
        label={<span>Accept <strong>terms</strong></span>}
        checked={false}
        onChange={noop}
      />
    );
    expect(screen.getByText('terms')).toBeTruthy();
  });

  it('renders the custom checkbox box element', () => {
    const { container } = render(
      <Checkbox id="terms" label="Accept terms" checked={false} onChange={noop} />
    );
    expect(container.querySelector('.checkbox-field__box')).toBeTruthy();
  });
});
