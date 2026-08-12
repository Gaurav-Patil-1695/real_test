import React from 'react';
import { render, screen } from '@testing-library/react';
import AlertBanner from './AlertBanner';

describe('AlertBanner', () => {
  it('returns null when message is empty string', () => {
    const { container } = render(<AlertBanner type="error" message="" />);
    expect(container.firstChild).toBeNull();
  });

  it('renders the message text', () => {
    render(<AlertBanner type="error" message="Something went wrong" />);
    expect(screen.getByText('Something went wrong')).toBeTruthy();
  });

  it('renders error banner with alert role', () => {
    render(<AlertBanner type="error" message="Error occurred" />);
    expect(screen.getByRole('alert')).toBeTruthy();
  });

  it('renders success banner with status role', () => {
    render(<AlertBanner type="success" message="Account created" />);
    expect(screen.getByRole('status')).toBeTruthy();
  });

  it('applies error modifier class', () => {
    const { container } = render(<AlertBanner type="error" message="Error" />);
    expect(container.querySelector('.alert-banner--error')).toBeTruthy();
  });

  it('applies success modifier class', () => {
    const { container } = render(<AlertBanner type="success" message="Success" />);
    expect(container.querySelector('.alert-banner--success')).toBeTruthy();
  });

  it('has aria-live polite', () => {
    const { container } = render(<AlertBanner type="error" message="Error" />);
    const banner = container.querySelector('.alert-banner');
    expect(banner?.getAttribute('aria-live')).toBe('polite');
  });

  it('has aria-atomic true', () => {
    const { container } = render(<AlertBanner type="error" message="Error" />);
    const banner = container.querySelector('.alert-banner');
    expect(banner?.getAttribute('aria-atomic')).toBe('true');
  });

  it('renders icon with aria-hidden', () => {
    const { container } = render(<AlertBanner type="error" message="Error" />);
    const icon = container.querySelector('.alert-banner__icon');
    expect(icon?.getAttribute('aria-hidden')).toBe('true');
  });

  it('renders success icon svg when type is success', () => {
    const { container } = render(<AlertBanner type="success" message="Done" />);
    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBeGreaterThan(0);
  });

  it('renders error icon svg when type is error', () => {
    const { container } = render(<AlertBanner type="error" message="Fail" />);
    const svgs = container.querySelectorAll('svg');
    expect(svgs.length).toBeGreaterThan(0);
  });

  it('renders message in alert-banner__message span', () => {
    const { container } = render(<AlertBanner type="success" message="Welcome!" />);
    const msgSpan = container.querySelector('.alert-banner__message');
    expect(msgSpan?.textContent).toBe('Welcome!');
  });
});
