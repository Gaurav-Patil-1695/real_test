import React from 'react';
import { render, screen } from '@testing-library/react';
import AuthCard from './AuthCard';

describe('AuthCard', () => {
  it('renders children inside the card', () => {
    render(<AuthCard><p>Hello World</p></AuthCard>);
    expect(screen.getByText('Hello World')).toBeTruthy();
  });

  it('has auth-layout wrapper class', () => {
    const { container } = render(<AuthCard><span>content</span></AuthCard>);
    expect(container.querySelector('.auth-layout')).toBeTruthy();
  });

  it('has auth-card inner class', () => {
    const { container } = render(<AuthCard><span>content</span></AuthCard>);
    expect(container.querySelector('.auth-card')).toBeTruthy();
  });

  it('renders multiple children', () => {
    render(
      <AuthCard>
        <p>First</p>
        <p>Second</p>
      </AuthCard>
    );
    expect(screen.getByText('First')).toBeTruthy();
    expect(screen.getByText('Second')).toBeTruthy();
  });
});
