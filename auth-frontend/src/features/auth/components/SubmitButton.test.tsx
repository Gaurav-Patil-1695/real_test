import React from 'react';
import { render, screen } from '@testing-library/react';
import SubmitButton from './SubmitButton';

describe('SubmitButton', () => {
  it('renders the label text', () => {
    render(<SubmitButton label="Sign In" />);
    expect(screen.getByRole('button').textContent).toContain('Sign In');
  });

  it('renders a submit button', () => {
    render(<SubmitButton label="Sign In" />);
    expect(screen.getByRole('button').getAttribute('type')).toBe('submit');
  });

  it('is enabled by default', () => {
    render(<SubmitButton label="Sign In" />);
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(false);
  });

  it('is disabled when disabled=true', () => {
    render(<SubmitButton label="Sign In" disabled />);
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(true);
  });

  it('is disabled when isLoading=true', () => {
    render(<SubmitButton label="Sign In" isLoading />);
    expect((screen.getByRole('button') as HTMLButtonElement).disabled).toBe(true);
  });

  it('sets aria-busy when isLoading=true', () => {
    render(<SubmitButton label="Sign In" isLoading />);
    expect(screen.getByRole('button').getAttribute('aria-busy')).toBe('true');
  });

  it('does not set aria-busy when not loading', () => {
    render(<SubmitButton label="Sign In" />);
    expect(screen.getByRole('button').getAttribute('aria-busy')).toBeNull();
  });

  it('sets aria-disabled when disabled', () => {
    render(<SubmitButton label="Sign In" disabled />);
    expect(screen.getByRole('button').getAttribute('aria-disabled')).toBe('true');
  });

  it('sets aria-disabled when isLoading', () => {
    render(<SubmitButton label="Sign In" isLoading />);
    expect(screen.getByRole('button').getAttribute('aria-disabled')).toBe('true');
  });

  it('does not set aria-disabled when neither disabled nor loading', () => {
    render(<SubmitButton label="Sign In" />);
    expect(screen.getByRole('button').getAttribute('aria-disabled')).toBeNull();
  });

  it('shows loadingLabel when isLoading and loadingLabel provided', () => {
    render(<SubmitButton label="Sign In" loadingLabel="Signing in..." isLoading />);
    expect(screen.getByRole('button').textContent).toContain('Signing in...');
  });

  it('shows regular label when isLoading but no loadingLabel', () => {
    render(<SubmitButton label="Sign In" isLoading />);
    expect(screen.getByRole('button').textContent).toContain('Sign In');
  });

  it('shows regular label when not loading even if loadingLabel is provided', () => {
    render(<SubmitButton label="Sign In" loadingLabel="Signing in..." />);
    expect(screen.getByRole('button').textContent).toContain('Sign In');
    expect(screen.getByRole('button').textContent).not.toContain('Signing in...');
  });

  it('renders spinner svg when isLoading', () => {
    const { container } = render(<SubmitButton label="Sign In" isLoading />);
    expect(container.querySelector('.submit-button__spinner')).toBeTruthy();
  });

  it('does not render spinner when not loading', () => {
    const { container } = render(<SubmitButton label="Sign In" />);
    expect(container.querySelector('.submit-button__spinner')).toBeNull();
  });

  it('applies loading class when isLoading', () => {
    const { container } = render(<SubmitButton label="Sign In" isLoading />);
    expect(container.querySelector('.submit-button--loading')).toBeTruthy();
  });

  it('does not apply loading class when not loading', () => {
    const { container } = render(<SubmitButton label="Sign In" />);
    expect(container.querySelector('.submit-button--loading')).toBeNull();
  });
});
