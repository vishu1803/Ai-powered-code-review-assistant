import { toast } from 'sonner';
import apiClient from './api/client';
import { User, Token, LoginRequest } from './types/api';

const AUTH_TOKEN_KEY = 'auth_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user_data';

// Token management
export const getAuthToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
};

export const getRefreshToken = (): string | null => {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
};

export const setAuthTokens = (tokens: Token): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(AUTH_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);
};

export const removeAuthToken = (): void => {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
};

// User data management
export const getCurrentUser = (): User | null => {
  if (typeof window === 'undefined') return null;
  const userData = localStorage.getItem(USER_KEY);
  return userData ? JSON.parse(userData) : null;
};

export const setCurrentUser = (user: User): void => {
  if (typeof window === 'undefined') return;
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};

// Auth state checking
export const isAuthenticated = (): boolean => {
  return !!getAuthToken();
};

// Authentication API calls
export const login = async (credentials: LoginRequest): Promise<{ user: User; tokens: Token }> => {
  try {
    const formData = new FormData();
    formData.append('username', credentials.email);
    formData.append('password', credentials.password);

    const tokens = await apiClient.post<Token>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    // Store tokens
    setAuthTokens(tokens);

    // Get user profile
    const user = await apiClient.get<User>('/users/me');
    setCurrentUser(user);

    toast.success('Successfully logged in');
    return { user, tokens };
  } catch (error: any) {
    const message = error.response?.data?.error?.message || 'Login failed';
    toast.error(message);
    throw error;
  }
};

export const register = async (userData: {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}): Promise<User> => {
  try {
    const user = await apiClient.post<User>('/auth/register', userData);
    toast.success('Account created successfully. Please log in.');
    return user;
  } catch (error: any) {
    const message = error.response?.data?.error?.message || 'Registration failed';
    toast.error(message);
    throw error;
  }
};

export const logout = async (): Promise<void> => {
  try {
    await apiClient.post('/auth/logout');
  } catch (error) {
    // Ignore logout errors
  } finally {
    removeAuthToken();
    toast.success('Successfully logged out');
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/login';
    }
  }
};

export const refreshAccessToken = async (): Promise<Token | null> => {
  const refreshToken = getRefreshToken();
  if (!refreshToken) {
    removeAuthToken();
    return null;
  }

  try {
    const tokens = await apiClient.post<Token>('/auth/refresh', {
      refresh_token: refreshToken,
    });

    setAuthTokens(tokens);
    return tokens;
  } catch (error) {
    removeAuthToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/login';
    }
    return null;
  }
};

export const getCurrentUserProfile = async (): Promise<User | null> => {
  try {
    if (!isAuthenticated()) return null;
    
    const user = await apiClient.get<User>('/users/me');
    setCurrentUser(user);
    return user;
  } catch (error) {
    return null;
  }
};

export const updateProfile = async (updates: Partial<User>): Promise<User> => {
  try {
    const user = await apiClient.put<User>('/users/me', updates);
    setCurrentUser(user);
    toast.success('Profile updated successfully');
    return user;
  } catch (error: any) {
    const message = error.response?.data?.error?.message || 'Profile update failed';
    toast.error(message);
    throw error;
  }
};

export const changePassword = async (currentPassword: string, newPassword: string): Promise<void> => {
  try {
    await apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    toast.success('Password changed successfully');
  } catch (error: any) {
    const message = error.response?.data?.error?.message || 'Password change failed';
    toast.error(message);
    throw error;
  }
};

// OAuth handlers
export const initiateOAuthLogin = (provider: 'github' | 'gitlab' | 'bitbucket'): void => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  const redirectUrl = `${baseUrl}/api/v1/auth/oauth/${provider}`;
  window.location.href = redirectUrl;
};

export const handleOAuthCallback = async (code: string, state: string, provider: string): Promise<{ user: User; tokens: Token }> => {
  try {
    const response = await apiClient.get<{ user: User; tokens: Token }>(`/auth/oauth/${provider}/callback`, {
      params: { code, state },
    });

    const { user, tokens } = response;
    setAuthTokens(tokens);
    setCurrentUser(user);

    toast.success(`Successfully logged in with ${provider}`);
    return { user, tokens };
  } catch (error: any) {
    const message = error.response?.data?.error?.message || 'OAuth login failed';
    toast.error(message);
    throw error;
  }
};

// Auto-refresh token setup
let refreshTimer: NodeJS.Timeout | null = null;

export const setupTokenRefresh = (): void => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
  }

  // Refresh token every 23 hours (tokens expire in 24 hours)
  refreshTimer = setInterval(async () => {
    if (isAuthenticated()) {
      await refreshAccessToken();
    }
  }, 23 * 60 * 60 * 1000);
};

export const clearTokenRefresh = (): void => {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
};
