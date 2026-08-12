import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ProfilePage from './ProfilePage';
import * as authApi from '../api/auth';

// Mock the api module
vi.mock('../api/auth', () => ({
  me: vi.fn(),
  logout: vi.fn(),
}));

// Mock react-router-dom's useNavigate
const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const sampleProfile = {
  id: '1',
  full_name: 'Alice Wonderland',
  email: 'alice@example.com',
  is_active: true,
  created_at: '2024-01-15T00:00:00.000Z',
  updated_at: '2024-06-01T00:00:00.000Z',
};

function renderPage() {
  return render(
    <MemoryRouter>
      <ProfilePage />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.mocked(authApi.me).mockResolvedValue(sampleProfile);
  vi.mocked(authApi.logout).mockResolvedValue(undefined);
  mockNavigate.mockReset();
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('ProfilePage – branding', () => {
  it('renders the app title', async () => {
    renderPage();
    expect(screen.getByText('auth-starter')).toBeTruthy();
  });

  it('renders the subtitle', async () => {
    renderPage();
    expect(screen.getByText('Your account profile')).toBeTruthy();
  });
});

describe('ProfilePage – loading state', () => {
  it('shows skeleton elements while profile is loading', () => {
    // keep me() pending
    vi.mocked(authApi.me).mockReturnValue(new Promise(() => {}));
    const { container } = renderPage();
    expect(container.querySelector('.profile-skeleton--name')).toBeTruthy();
    expect(container.querySelector('.profile-skeleton--email')).toBeTruthy();
    expect(container.querySelector('.profile-skeleton--value')).toBeTruthy();
  });

  it('does not show account details section while loading', () => {
    vi.mocked(authApi.me).mockReturnValue(new Promise(() => {}));
    renderPage();
    expect(screen.queryByText('Account details')).toBeNull();
  });
});

describe('ProfilePage – successful profile load', () => {
  it('displays the user full name', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Alice Wonderland')).toBeTruthy());
  });

  it('displays the user email', async () => {
    renderPage();
    await waitFor(() => expect(screen.getAllByText('alice@example.com').length).toBeGreaterThan(0));
  });

  it('shows Active badge when is_active is true', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Active')).toBeTruthy());
  });

  it('shows Inactive badge when is_active is false', async () => {
    vi.mocked(authApi.me).mockResolvedValue({ ...sampleProfile, is_active: false });
    renderPage();
    await waitFor(() => expect(screen.getByText('Inactive')).toBeTruthy());
  });

  it('renders Account details section title', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Account details')).toBeTruthy());
  });

  it('renders Full name field label', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Full name')).toBeTruthy());
  });

  it('renders Email address field label', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Email address')).toBeTruthy());
  });

  it('renders Member since field label', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Member since')).toBeTruthy());
  });

  it('does not show skeleton after load completes', async () => {
    const { container } = renderPage();
    await waitFor(() => expect(screen.getByText('Alice Wonderland')).toBeTruthy());
    expect(container.querySelector('.profile-skeleton--name')).toBeNull();
  });
});

describe('ProfilePage – error loading profile', () => {
  it('shows an error banner when me() rejects', async () => {
    vi.mocked(authApi.me).mockRejectedValue(new Error('Network error'));
    renderPage();
    await waitFor(() =>
      expect(screen.getByText('Failed to load profile. Please try again.')).toBeTruthy(),
    );
  });

  it('renders the error banner with role=alert', async () => {
    vi.mocked(authApi.me).mockRejectedValue(new Error('err'));
    renderPage();
    await waitFor(() => expect(screen.getByRole('alert')).toBeTruthy());
  });

  it('does not show profile details on error', async () => {
    vi.mocked(authApi.me).mockRejectedValue(new Error('err'));
    renderPage();
    await waitFor(() => expect(screen.queryByText('Account details')).toBeNull());
  });
});

describe('ProfilePage – logout', () => {
  it('renders the Log out button', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Alice Wonderland')).toBeTruthy());
    expect(screen.getByRole('button', { name: /log out/i })).toBeTruthy();
  });

  it('calls logout() and navigates to /login on success', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('Alice Wonderland')).toBeTruthy());
    const btn = screen.getByRole('button', { name: /log out/i });
    await act(async () => {
      fireEvent.click(btn);
    });
    expect(authApi.logout).toHaveBeenCalledOnce();
    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true });
  });

  it('shows spinner text while logging out', async () => {
    let resolveLogout!: () => void;
    vi.mocked(authApi.logout).mockReturnValue(
      new Promise<void>((res) => {
        resolveLogout = res;
      }),
    );
    renderPage();
    await waitFor(() => expect(screen.getByText('Alice Wonderland')).toBeTruthy());
    fireEvent.click(screen.getByRole('button', { name: /log out/i }));
    await waitFor(() => expect(screen.getByText('Logging out…')).toBeTruthy());
    // cleanup
    await act(async () => {
      resolveLogout();
    });
  });

  it('disables the button while logging out', async () => {
    vi.mocked(authApi.logout).mockReturnValue(new Promise(() => {}));
    renderPage();
    await waitFor(() => expect(screen.getByText('Alice Wonderland')).toBeTruthy());
    const btn = screen.getByRole('button', { name: /log out/i });
    fireEvent.click(btn);
    await waitFor(() => expect((btn as HTMLButtonElement).disabled).toBe(true));
  });

  it('shows an error banner when logout() rejects', async () => {
    vi.mocked(authApi.logout).mockRejectedValue(new Error('Logout error'));
    renderPage();
    await waitFor(() => expect(screen.getByText('Alice Wonderland')).toBeTruthy());
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /log out/i }));
    });
    await waitFor(() =>
      expect(screen.getByText('Logout failed. Please try again.')).toBeTruthy(),
    );
  });

  it('re-enables the button after logout failure', async () => {
    vi.mocked(authApi.logout).mockRejectedValue(new Error('fail'));
    renderPage();
    await waitFor(() => expect(screen.getByText('Alice Wonderland')).toBeTruthy());
    const btn = screen.getByRole('button', { name: /log out/i });
    await act(async () => {
      fireEvent.click(btn);
    });
    await waitFor(() => expect((btn as HTMLButtonElement).disabled).toBe(false));
  });

  it('does not navigate when logout fails', async () => {
    vi.mocked(authApi.logout).mockRejectedValue(new Error('fail'));
    renderPage();
    await waitFor(() => expect(screen.getByText('Alice Wonderland')).toBeTruthy());
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /log out/i }));
    });
    await waitFor(() => expect(screen.getByText('Logout failed. Please try again.')).toBeTruthy());
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});

describe('getInitials (via rendered avatar)', () => {
  it('shows two-letter initials for a two-word name', async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText('AW')).toBeTruthy());
  });

  it('shows one-letter initial for a single-word name', async () => {
    vi.mocked(authApi.me).mockResolvedValue({ ...sampleProfile, full_name: 'Alice' });
    renderPage();
    await waitFor(() => expect(screen.getByText('A')).toBeTruthy());
  });

  it('uses only first two parts for a three-word name', async () => {
    vi.mocked(authApi.me).mockResolvedValue({ ...sampleProfile, full_name: 'Alice B Wonderland' });
    renderPage();
    await waitFor(() => expect(screen.getByText('AB')).toBeTruthy());
  });
});
