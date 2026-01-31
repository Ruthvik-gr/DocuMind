import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { authService } from '../../src/services/authService';
import api from '../../src/services/api';

vi.mock('../../src/services/api');

describe('authService', () => {
  const mockTokenResponse = {
    access_token: 'test-access-token',
    refresh_token: 'test-refresh-token',
    token_type: 'Bearer',
  };

  const mockUser = {
    id: 'user-123',
    email: 'test@example.com',
    name: 'Test User',
    auth_provider: 'local' as const,
    created_at: '2024-01-15T10:00:00Z',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  describe('register', () => {
    it('registers user and stores tokens', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockTokenResponse });

      const result = await authService.register({
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User',
      });

      expect(api.post).toHaveBeenCalledWith('/auth/register', {
        email: 'test@example.com',
        password: 'password123',
        name: 'Test User',
      });
      expect(result).toEqual(mockTokenResponse);
      expect(localStorage.getItem('access_token')).toBe('test-access-token');
      expect(localStorage.getItem('refresh_token')).toBe('test-refresh-token');
    });
  });

  describe('login', () => {
    it('logs in user and stores tokens', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockTokenResponse });

      const result = await authService.login({
        email: 'test@example.com',
        password: 'password123',
      });

      expect(api.post).toHaveBeenCalledWith('/auth/login', {
        email: 'test@example.com',
        password: 'password123',
      });
      expect(result).toEqual(mockTokenResponse);
      expect(localStorage.getItem('access_token')).toBe('test-access-token');
      expect(localStorage.getItem('refresh_token')).toBe('test-refresh-token');
    });
  });

  describe('googleLogin', () => {
    it('logs in with Google and stores tokens', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: mockTokenResponse });

      const result = await authService.googleLogin({
        credential: 'google-credential-token',
      });

      expect(api.post).toHaveBeenCalledWith('/auth/google', {
        credential: 'google-credential-token',
      });
      expect(result).toEqual(mockTokenResponse);
      expect(localStorage.getItem('access_token')).toBe('test-access-token');
    });
  });

  describe('refreshToken', () => {
    it('refreshes token when refresh token exists', async () => {
      localStorage.setItem('refresh_token', 'existing-refresh-token');
      vi.mocked(api.post).mockResolvedValue({ data: mockTokenResponse });

      const result = await authService.refreshToken();

      expect(api.post).toHaveBeenCalledWith('/auth/refresh', {
        refresh_token: 'existing-refresh-token',
      });
      expect(result).toEqual(mockTokenResponse);
    });

    it('throws error when no refresh token exists', async () => {
      await expect(authService.refreshToken()).rejects.toThrow('No refresh token available');
    });
  });

  describe('getMe', () => {
    it('fetches current user', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: mockUser });

      const result = await authService.getMe();

      expect(api.get).toHaveBeenCalledWith('/auth/me');
      expect(result).toEqual(mockUser);
    });
  });

  describe('setTokens', () => {
    it('stores tokens in localStorage', () => {
      authService.setTokens(mockTokenResponse);

      expect(localStorage.getItem('access_token')).toBe('test-access-token');
      expect(localStorage.getItem('refresh_token')).toBe('test-refresh-token');
    });
  });

  describe('getAccessToken', () => {
    it('returns access token from localStorage', () => {
      localStorage.setItem('access_token', 'stored-token');

      expect(authService.getAccessToken()).toBe('stored-token');
    });

    it('returns null when no token exists', () => {
      expect(authService.getAccessToken()).toBeNull();
    });
  });

  describe('getRefreshToken', () => {
    it('returns refresh token from localStorage', () => {
      localStorage.setItem('refresh_token', 'stored-refresh-token');

      expect(authService.getRefreshToken()).toBe('stored-refresh-token');
    });

    it('returns null when no token exists', () => {
      expect(authService.getRefreshToken()).toBeNull();
    });
  });

  describe('clearTokens', () => {
    it('removes tokens from localStorage', () => {
      localStorage.setItem('access_token', 'token');
      localStorage.setItem('refresh_token', 'refresh');

      authService.clearTokens();

      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });

  describe('isAuthenticated', () => {
    it('returns true when access token exists', () => {
      localStorage.setItem('access_token', 'token');

      expect(authService.isAuthenticated()).toBe(true);
    });

    it('returns false when no access token exists', () => {
      expect(authService.isAuthenticated()).toBe(false);
    });
  });

  describe('logout', () => {
    it('clears tokens on logout', () => {
      localStorage.setItem('access_token', 'token');
      localStorage.setItem('refresh_token', 'refresh');

      authService.logout();

      expect(localStorage.getItem('access_token')).toBeNull();
      expect(localStorage.getItem('refresh_token')).toBeNull();
    });
  });
});
