import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import RegisterPage from '../../src/pages/RegisterPage';
import * as AuthContext from '../../src/contexts/AuthContext';

vi.mock('../../src/contexts/AuthContext');
vi.mock('@react-oauth/google', () => ({
  GoogleLogin: ({ onSuccess, onError }: any) => (
    <div>
      <button
        data-testid="google-login-button"
        onClick={() => onSuccess({ credential: 'test-credential' })}
      >
        Sign up with Google
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
  ),
}));

const mockNavigate = vi.fn();
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('RegisterPage', () => {
  const mockRegister = vi.fn();
  const mockGoogleLogin = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(AuthContext.useAuth).mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: mockRegister,
      googleLogin: mockGoogleLogin,
      logout: vi.fn(),
      refreshUser: vi.fn(),
    });
  });

  it('renders registration form', () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Create your account')).toBeInTheDocument();
    expect(screen.getByLabelText('Full name')).toBeInTheDocument();
    expect(screen.getByLabelText('Email address')).toBeInTheDocument();
    expect(screen.getByLabelText('Password')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirm password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Create account' })).toBeInTheDocument();
  });

  it('renders link to login page', () => {
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Sign in')).toBeInTheDocument();
  });

  it('updates form fields', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Full name'), 'Test User');
    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.type(screen.getByLabelText('Confirm password'), 'password123');

    expect(screen.getByLabelText('Full name')).toHaveValue('Test User');
    expect(screen.getByLabelText('Email address')).toHaveValue('test@example.com');
    expect(screen.getByLabelText('Password')).toHaveValue('password123');
    expect(screen.getByLabelText('Confirm password')).toHaveValue('password123');
  });

  it('shows error when passwords do not match', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Full name'), 'Test User');
    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.type(screen.getByLabelText('Confirm password'), 'differentpassword');
    await user.click(screen.getByRole('button', { name: 'Create account' }));

    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('shows error when password is too short', async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Full name'), 'Test User');
    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'short');
    await user.type(screen.getByLabelText('Confirm password'), 'short');
    await user.click(screen.getByRole('button', { name: 'Create account' }));

    expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
    expect(mockRegister).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    mockRegister.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Full name'), 'Test User');
    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.type(screen.getByLabelText('Confirm password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => {
      expect(mockRegister).toHaveBeenCalledWith('test@example.com', 'password123', 'Test User');
    });

    expect(mockNavigate).toHaveBeenCalledWith('/');
  });

  it('shows loading state while submitting', async () => {
    const user = userEvent.setup();
    let resolveRegister: () => void;
    const registerPromise = new Promise<void>(resolve => {
      resolveRegister = resolve;
    });
    mockRegister.mockReturnValue(registerPromise);

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Full name'), 'Test User');
    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.type(screen.getByLabelText('Confirm password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Create account' }));

    expect(screen.getByRole('button', { name: 'Creating account...' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Creating account...' })).toBeDisabled();

    resolveRegister!();
  });

  it('displays error message on registration failure', async () => {
    const user = userEvent.setup();
    mockRegister.mockRejectedValue(new Error('Email already exists'));

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Full name'), 'Test User');
    await user.type(screen.getByLabelText('Email address'), 'existing@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.type(screen.getByLabelText('Confirm password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => {
      expect(screen.getByText('Email already exists')).toBeInTheDocument();
    });
  });

  it('displays generic error message for non-Error failures', async () => {
    const user = userEvent.setup();
    mockRegister.mockRejectedValue('Unknown error');

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.type(screen.getByLabelText('Full name'), 'Test User');
    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.type(screen.getByLabelText('Confirm password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => {
      expect(screen.getByText('Registration failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('handles successful Google login', async () => {
    const user = userEvent.setup();
    mockGoogleLogin.mockResolvedValue(undefined);

    render(
      <MemoryRouter>
        <RegisterPage />
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
        <RegisterPage />
      </MemoryRouter>
    );

    await user.click(screen.getByTestId('google-login-button'));

    await waitFor(() => {
      expect(screen.getByText('Google auth failed')).toBeInTheDocument();
    });
  });

  it('handles Google login onError callback', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.click(screen.getByTestId('google-login-error'));

    await waitFor(() => {
      expect(screen.getByText('Google login failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('handles Google login with no credential', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.click(screen.getByTestId('google-login-no-cred'));

    await waitFor(() => {
      expect(screen.getByText('Google login failed. No credential received.')).toBeInTheDocument();
    });

    expect(mockGoogleLogin).not.toHaveBeenCalled();
  });

  it('handles Google login generic failure', async () => {
    const user = userEvent.setup();
    mockGoogleLogin.mockRejectedValue('Unknown error');

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    await user.click(screen.getByTestId('google-login-button'));

    await waitFor(() => {
      expect(screen.getByText('Google login failed. Please try again.')).toBeInTheDocument();
    });
  });

  it('clears error on form submit', async () => {
    const user = userEvent.setup();
    mockRegister.mockRejectedValueOnce(new Error('First error'));
    mockRegister.mockResolvedValueOnce(undefined);

    render(
      <MemoryRouter>
        <RegisterPage />
      </MemoryRouter>
    );

    // First attempt - fails
    await user.type(screen.getByLabelText('Full name'), 'Test User');
    await user.type(screen.getByLabelText('Email address'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');
    await user.type(screen.getByLabelText('Confirm password'), 'password123');
    await user.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => {
      expect(screen.getByText('First error')).toBeInTheDocument();
    });

    // Second attempt - should clear error and succeed
    await user.click(screen.getByRole('button', { name: 'Create account' }));

    await waitFor(() => {
      expect(screen.queryByText('First error')).not.toBeInTheDocument();
    });
  });
});
