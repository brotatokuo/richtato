import { authApi, Organization, User } from '@/lib/api/auth';
import { ReactNode, useEffect, useState } from 'react';
import {
  AuthContext,
  AuthContextType,
  RegisterRequest,
} from './AuthContextInstance';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const isAuthenticated = !!user;

  const login = async (username: string, password: string) => {
    try {
      console.log('Login attempt:', username, password);
      const response = await authApi.login({ username, password });

      if (response.success) {
        setUser(response.user);
        setOrganization(response.organization || null);
        console.log('Login successful:', response.user);
      } else {
        console.error('Login failed:', response.message);
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const demoLogin = async () => {
    try {
      console.log('Demo login attempt');
      const response = await authApi.demoLogin();

      if (response.success) {
        setUser(response.user);
        setOrganization(response.organization || null);
        console.log('Demo login successful:', response.user);
      } else {
        console.error('Demo login failed:', response.message);
        throw new Error(response.message);
      }
    } catch (error) {
      console.error('Demo login error:', error);
      throw error;
    }
  };

  const register = async (data: RegisterRequest) => {
    // Call backend register endpoint
    const res = await authApi.register({
      username: data.username,
      email: data.email,
      password: data.password,
    });

    if (!res.success) {
      throw new Error(res.message || 'Registration failed');
    }

    // Auto-login after successful registration
    await login(data.username, data.password);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
      setOrganization(null);
    }
  };

  const refreshUser = async () => {
    if (!authApi.isAuthenticated()) {
      setUser(null);
      setOrganization(null);
      setIsLoading(false);
      return;
    }

    try {
      const response = await authApi.getProfile();
      if (response.success) {
        setUser(response.user);
        setOrganization(response.organization || null);
      } else {
        // If profile fetch fails, user might not be authenticated
        setUser(null);
        setOrganization(null);
      }
    } catch {
      // If profile fetch fails, clear user data
      setUser(null);
      setOrganization(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize authentication state on mount
  useEffect(() => {
    const initializeAuth = async () => {
      if (authApi.isAuthenticated()) {
        await refreshUser();
      } else {
        setIsLoading(false);
      }
    };

    initializeAuth();
  }, []);

  const value: AuthContextType = {
    user,
    organization,
    isAuthenticated,
    isLoading,
    login,
    demoLogin,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
