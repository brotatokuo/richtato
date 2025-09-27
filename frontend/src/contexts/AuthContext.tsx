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
    // TODO: Implement actual login API call
    // For now, just set a mock user
    console.log('Login attempt:', username, password); // Use password parameter
    setUser({
      id: 1,
      username,
      email: 'user@example.com',
      first_name: 'User',
      last_name: 'Name',
      is_staff: false,
      is_superuser: false,
      is_active: true,
      date_joined: new Date().toISOString(),
      last_login: new Date().toISOString(),
    } as User);
  };

  const register = async (data: RegisterRequest) => {
    // TODO: Implement actual registration API call
    // For now, just set a mock user
    setUser({
      id: 1,
      username: data.username,
      email: data.email,
      first_name: data.firstName,
      last_name: data.lastName,
      is_staff: false,
      is_superuser: false,
      is_active: true,
      date_joined: new Date().toISOString(),
      last_login: new Date().toISOString(),
    } as User);
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
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
