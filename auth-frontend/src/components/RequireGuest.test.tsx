import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import React from 'react';
import { RequireGuest } from './RequireGuest';
import * as AuthContextModule from '../context/AuthContext';

const mockUseAuth = vi.spyOn(AuthContextModule, 'useAuth');

describe('RequireGuest', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders children when user is NOT authenticated (guest)', () => {
    mockUseAuth.mockReturnValue({ user: null, loading: false } as any);

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route
            path="/login"
            element={
              <RequireGuest>
                <div>Login Form</div>
              </RequireGuest>
            }
          />
          <Route path="/profile" element={<div>Profile Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByText('Login Form')).toBeDefined();
  });

  it('redirects to /profile when user IS authenticated', () => {
    mockUseAuth.mockReturnValue({ user: { email: 'user@example.com' }, loading: false } as any);

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route
            path="/login"
            element={
              <RequireGuest>
                <div>Login Form</div>
              </RequireGuest>
            }
          />
          <Route path="/profile" element={<div>Profile Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.queryByText('Login Form')).toBeNull();
    expect(screen.getByText('Profile Page')).toBeDefined();
  });

  it('renders guest content while auth is loading', () => {
    mockUseAuth.mockReturnValue({ user: null, loading: true } as any);

    render(
      <MemoryRouter initialEntries={['/login']}>
        <Routes>
          <Route
            path="/login"
            element={
              <RequireGuest>
                <div>Login Form</div>
              </RequireGuest>
            }
          />
          <Route path="/profile" element={<div>Profile Page</div>} />
        </Routes>
      </MemoryRouter>
    );

    // Should not redirect to profile while loading with no user
    expect(screen.queryByText('Profile Page')).toBeNull();
  });
});
