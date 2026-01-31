import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from '../../src/pages/LoginPage';
import * as AuthContext from '../../src/contexts/AuthContext';

vi.mock('../../src/contexts/AuthContext');

// Store callbacks so we can trigger them in tests
let googleSuccessCallback: ((response: { credential?: string }) => void) | null = null;
let googleErrorCallback: (() => void) | null = null;

vi.mock('@react-oauth/google', () => ({
  GoogleLogin: ({ onSuccess, onError }: any) => {
    googleSuccessCallback = onSuccess;
    googleErrorCallback = onError;
    return (
      <div>
        <button
          data-testid="google-login-button"
          onClick={() => onSuccess({ credential: 'test-credential' })}
        >
          Sign in with Google
        </button>
        <button
          data-testid="google-login-no-cred"
          onClick={() => onSuccess({})}
        >
          Google No Cred
        </button>
        <button
          data-testid="google-login-error"
          onClick={() => onError()}
        >
          Google Error
        </button>
      </div>
    );
  },
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('LoginPage', () => {
  const mockLogin = vi.fn();
  const mockGoogleLogin = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: mockLogin,
      register: vi.fn(),
      googleLogin: mockGoogleLogin,
      logout: vi.fn(),
      refreshUser: vi.fn(),
    });
  });

  it('renders login form', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Sign in to your account')).toBeInTheDocument();
    expect(screen.getByLabelText('Email address')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument();
  });

  it('renders link to register page', () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    expect(screen.getByText('create a new account')).toBeInTheDocument();
  });

  it('updates email and password fields', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    const emailInput = screen.getByLabelText('Email address');
    const passwordInput = screen.getByLabelText('Password');

    await user.type(emailInput, 'test@example.com');
    await user.type(passwordInput, 'password123');

    expect(emailInput).toHaveValue('test@example.com');
    expect(passwordInput).toHaveValue('password123');
  });

  it('submits form with credentials', async () => {
    const user = userEvent.setup();
    mockLogin.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
    });

    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('shows loading state while submitting', async () => {
    const user = userEvent.setup();
    let resolveLogin: () => void;
    const loginPromise = new Promise<void>(resolve => {
      resolveLogin = resolve;
    });
    mockLogin.mockReturnValue(loginPromise);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    expect(screen.getByRole('button', { name: 'Signing in...' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Signing in...' })).toBeDisabled();

    resolveLogin!();
  });

  it('displays error message on login failure', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue(new Error('Invalid credentials'));

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'wrongpassword');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument();
    });
  });

  it('displays generic error message for non-Error failures', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValue('Unknown error');

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => {
      expect(screen.getByText('Login failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('handles successful Google login', async () => {
    const user = userEvent.setup();
    mockGoogleLogin.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.click(screen.getByTestId('google-login-button'));

    await waitFor(() => {
      expect(mockGoogleLogin).toHaveBeenCalledWith('test-credential');
    });

    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('handles Google login failure', async () => {
    const user = userEvent.setup();
    mockGoogleLogin.mockRejectedValue(new Error('Google auth failed'));

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.click(screen.getByTestId('google-login-button'));

    await waitFor(() => {
      expect(screen.getByText('Google auth failed')).toBeInTheDocument();
    });
  });

  it('handles Google login with no credential', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.click(screen.getByTestId('google-login-no-cred'));

    await waitFor(() => {
      expect(screen.getByText('Google login failed. No credential received.')).toBeInTheDocument();
    });

    expect(mockGoogleLogin).not.toHaveBeenCalled();
  });

  it('handles Google login onError callback', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    await user.click(screen.getByTestId('google-login-error'));

    await waitFor(() => {
      expect(screen.getByText('Google login failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('clears error on form submit', async () => {
    const user = userEvent.setup();
    mockLogin.mockRejectedValueOnce(new Error('First error'));
    mockLogin.mockResolvedValueOnce(undefined);

    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );

    // First attempt - fails
    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'wrong');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => {
      expect(screen.getByText('First error')).toBeInTheDocument();
    });

    // Second attempt - should clear error
    await user.clear(screen.getByLabelText('Password'));
    await user.type(screen.getByLabelText('Password'), 'correct');
    await user.click(screen.getByRole('button', { name: 'Sign in' }));

    await waitFor(() => {
      expect(screen.queryByText('First error')).not.toBeInTheDocument();
    });
  });
});
