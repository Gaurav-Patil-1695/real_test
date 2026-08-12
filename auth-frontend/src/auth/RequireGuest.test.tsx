import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import RequireGuest from './RequireGuest';
import * as AuthContextModule from './AuthContext';

jest.mock('./AuthContext', () => ({
  ...jest.requireActual('./AuthContext'),
  useAuth: jest.fn(),
}));

const mockedUseAuth = AuthContextModule.useAuth as jest.MockedFunction<typeof AuthContextModule.useAuth>;

function renderWithRouter(ui: React.ReactElement, initialEntry = '/login') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path='/login' element={ui} />
        <Route path='/profile' element={<div>Profile Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('RequireGuest', () => {
  it('renders null while loading', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: true,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refresh: jest.fn(),
    });

    const { container } = renderWithRouter(
      <RequireGuest><div>Guest Content</div></RequireGuest>
    );

    expect(container.firstChild).toBeNull();
    expect(screen.queryByText('Guest Content')).toBeNull();
  });

  it('renders children when not authenticated and not loading', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refresh: jest.fn(),
    });

    renderWithRouter(
      <RequireGuest><div>Guest Content</div></RequireGuest>
    );

    expect(screen.getByText('Guest Content')).toBeTruthy();
  });

  it('redirects to /profile when authenticated', () => {
    mockedUseAuth.mockReturnValue({
      user: { id: '1', email: 'a@b.com', name: 'A' },
      isAuthenticated: true,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refresh: jest.fn(),
    });

    renderWithRouter(
      <RequireGuest><div>Guest Content</div></RequireGuest>
    );

    expect(screen.queryByText('Guest Content')).toBeNull();
    expect(screen.getByText('Profile Page')).toBeTruthy();
  });

  it('does not render children when authenticated regardless of user object shape', () => {
    mockedUseAuth.mockReturnValue({
      user: { id: '99', email: 'other@example.com', name: 'Other' },
      isAuthenticated: true,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refresh: jest.fn(),
    });

    renderWithRouter(
      <RequireGuest><div>Should Not See</div></RequireGuest>
    );

    expect(screen.queryByText('Should Not See')).toBeNull();
  });
});
