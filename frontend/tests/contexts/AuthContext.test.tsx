import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import React from 'react';
import { AuthProvider, useAuth } from '../../src/contexts/AuthContext';
import { authService } from '../../src/services/authService';

vi.mock('../../src/services/authService');

const TestComponent: React.FC = () => {
  const { user, isAuthenticated, isLoading, login, register, googleLogin, logout, refreshUser } = useAuth();

  return (
    <div>
      <p data-testid="loading">{isLoading ? 'loading' : 'not-loading'}</p>
      <p data-testid="authenticated">{isAuthenticated ? 'authenticated' : 'not-authenticated'}</p>
      <p data-testid="user">{user ? user.name : 'no-user'}</p>
      <button onClick={() => login('test@example.com', 'password')}>Login</button>
      <button onClick={() => register('test@example.com', 'password', 'Test User')}>Register</button>
      <button onClick={() => googleLogin('google-credential')}>Google Login</button>
      <button onClick={logout}>Logout</button>
      <button onClick={refreshUser}>Refresh</button>
    </div>
  );
};

describe('AuthContext', () => {
  const mockUser = {
    id: 'user-123',
    email: 'test@example.com',
    name: 'Test User',
    auth_provider: 'local' as const,
    created_at: '2024-01-15T10:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(authService.isAuthenticated).mockReturnValue(false);
  });

  it('provides initial unauthenticated state', async () => {
    vi.mocked(authService.isAuthenticated).mockReturnValue(false);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('not-loading');
    });

    expect(screen.getByTestId('authenticated').textContent).toBe('not-authenticated');
    expect(screen.getByTestId('user').textContent).toBe('no-user');
  });

  it('loads user on mount when authenticated', async () => {
    vi.mocked(authService.isAuthenticated).mockReturnValue(true);
    vi.mocked(authService.getMe).mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('not-loading');
    });

    expect(screen.getByTestId('authenticated').textContent).toBe('authenticated');
    expect(screen.getByTestId('user').textContent).toBe('Test User');
  });

  it('handles login', async () => {
    const user = userEvent.setup();
    vi.mocked(authService.isAuthenticated).mockReturnValue(false);
    vi.mocked(authService.login).mockResolvedValue({
      access_token: 'token',
      refresh_token: 'refresh',
      token_type: 'Bearer',
    });
    vi.mocked(authService.getMe).mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('not-loading');
    });

    vi.mocked(authService.isAuthenticated).mockReturnValue(true);

    await user.click(screen.getByText('Login'));

    await waitFor(() => {
      expect(authService.login).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password',
      });
    });

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toBe('Test User');
    });
  });

  it('handles register', async () => {
    const user = userEvent.setup();
    vi.mocked(authService.isAuthenticated).mockReturnValue(false);
    vi.mocked(authService.register).mockResolvedValue({
      access_token: 'token',
      refresh_token: 'refresh',
      token_type: 'Bearer',
    });
    vi.mocked(authService.getMe).mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('not-loading');
    });

    vi.mocked(authService.isAuthenticated).mockReturnValue(true);

    await user.click(screen.getByText('Register'));

    await waitFor(() => {
      expect(authService.register).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password',
        name: 'Test User',
      });
    });
  });

  it('handles google login', async () => {
    const user = userEvent.setup();
    vi.mocked(authService.isAuthenticated).mockReturnValue(false);
    vi.mocked(authService.googleLogin).mockResolvedValue({
      access_token: 'token',
      refresh_token: 'refresh',
      token_type: 'Bearer',
    });
    vi.mocked(authService.getMe).mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('not-loading');
    });

    vi.mocked(authService.isAuthenticated).mockReturnValue(true);

    await user.click(screen.getByText('Google Login'));

    await waitFor(() => {
      expect(authService.googleLogin).toHaveBeenCalledWith({
        credential: 'google-credential',
      });
    });
  });

  it('handles logout', async () => {
    const user = userEvent.setup();
    vi.mocked(authService.isAuthenticated).mockReturnValue(true);
    vi.mocked(authService.getMe).mockResolvedValue(mockUser);

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toBe('Test User');
    });

    await user.click(screen.getByText('Logout'));

    expect(authService.logout).toHaveBeenCalled();
    expect(screen.getByTestId('user').textContent).toBe('no-user');
    expect(screen.getByTestId('authenticated').textContent).toBe('not-authenticated');
  });

  it('handles refresh user error', async () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(authService.isAuthenticated).mockReturnValue(true);
    vi.mocked(authService.getMe).mockRejectedValue(new Error('Auth failed'));

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('not-loading');
    });

    expect(authService.logout).toHaveBeenCalled();
    expect(screen.getByTestId('user').textContent).toBe('no-user');

    consoleErrorSpy.mockRestore();
  });

  it('throws error when useAuth is used outside AuthProvider', () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TestComponent />);
    }).toThrow('useAuth must be used within an AuthProvider');

    consoleErrorSpy.mockRestore();
  });
});
