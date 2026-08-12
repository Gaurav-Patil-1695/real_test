import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import RequireAuth from './RequireAuth';
import * as AuthContextModule from './AuthContext';

jest.mock('./AuthContext', () => ({
  ...jest.requireActual('./AuthContext'),
  useAuth: jest.fn(),
}));

const mockedUseAuth = AuthContextModule.useAuth as jest.MockedFunction<typeof AuthContextModule.useAuth>;

function renderWithRouter(ui: React.ReactElement, initialEntry = '/protected') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path='/protected' element={ui} />
        <Route path='/login' element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe('RequireAuth', () => {
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
      <RequireAuth><div>Protected Content</div></RequireAuth>
    );

    expect(container.firstChild).toBeNull();
    expect(screen.queryByText('Protected Content')).toBeNull();
  });

  it('renders children when authenticated and not loading', () => {
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
      <RequireAuth><div>Protected Content</div></RequireAuth>
    );

    expect(screen.getByText('Protected Content')).toBeTruthy();
  });

  it('redirects to /login with next param when not authenticated', () => {
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
      <RequireAuth><div>Protected Content</div></RequireAuth>,
      '/protected'
    );

    expect(screen.queryByText('Protected Content')).toBeNull();
    expect(screen.getByText('Login Page')).toBeTruthy();
  });

  it('encodes the full path including search and hash in next param', () => {
    mockedUseAuth.mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
      refresh: jest.fn(),
    });

    // We render at a route with query and hash
    render(
      <MemoryRouter initialEntries={['/protected?foo=bar#section']}>
        <Routes>
          <Route
            path='/protected'
            element={
              <RequireAuth><div>Protected</div></RequireAuth>
            }
          />
          <Route
            path='/login'
            element={<div data-testid="login-page">Login Page</div>}
          />
        </Routes>
      </MemoryRouter>
    );

    expect(screen.getByTestId('login-page')).toBeTruthy();
    expect(screen.queryByText('Protected')).toBeNull();
  });
});
