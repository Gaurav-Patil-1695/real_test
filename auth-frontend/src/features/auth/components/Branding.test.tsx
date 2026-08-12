import React from 'react';
import { render, screen } from '@testing-library/react';
import Branding from './Branding';

describe('Branding', () => {
  it('renders the wordmark AuthStarter', () => {
    render(<Branding />);
    expect(screen.getByText('AuthStarter')).toBeTruthy();
  });

  it('renders with branding class', () => {
    const { container } = render(<Branding />);
    expect(container.querySelector('.branding')).toBeTruthy();
  });

  it('renders the logo icon with aria-hidden', () => {
    const { container } = render(<Branding />);
    const logoDiv = container.querySelector('.branding__logo');
    expect(logoDiv).toBeTruthy();
    expect(logoDiv?.getAttribute('aria-hidden')).toBe('true');
  });

  it('renders an SVG inside the logo', () => {
    const { container } = render(<Branding />);
    const svg = container.querySelector('.branding__logo-icon');
    expect(svg).toBeTruthy();
    expect(svg?.tagName.toLowerCase()).toBe('svg');
  });

  it('renders the wordmark span with correct class', () => {
    const { container } = render(<Branding />);
    const wordmark = container.querySelector('.branding__wordmark');
    expect(wordmark).toBeTruthy();
    expect(wordmark?.textContent).toBe('AuthStarter');
  });
});
