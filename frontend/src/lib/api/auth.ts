/**
 * Authentication API service for handling login, logout, and user management
 */

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superuser: boolean;
  is_active: boolean;
  date_joined?: string;
  last_login?: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  success: boolean;
  message: string;
  user: User;
  token: string;
  organization?: Organization;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  organization_id?: number;
}

export interface RegisterResponse {
  success: boolean;
  message: string;
  user: User;
}

export interface UserProfileResponse {
  success: boolean;
  user: User;
  organization?: Organization;
}

export interface AuthCheckResponse {
  authenticated: boolean;
  user?: User;
}

export interface ApiError {
  success: false;
  message: string;
  details?: unknown;
}

class AuthApiService {
  private baseUrl: string;
  private token: string | null = null;

  constructor() {
    // Use environment variable or default to localhost
    this.baseUrl =
      import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

    // Load token from localStorage on initialization
    this.token = this.getStoredToken();
  }

  private getStoredToken(): string | null {
    try {
      return localStorage.getItem('auth_token');
    } catch {
      return null;
    }
  }

  private setStoredToken(token: string): void {
    try {
      localStorage.setItem('auth_token', token);
    } catch (error) {
      console.error('Failed to store auth token:', error);
    }
  }

  private clearStoredToken(): void {
    try {
      localStorage.removeItem('auth_token');
    } catch (error) {
      console.error('Failed to clear auth token:', error);
    }
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Token ${this.token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      // Handle 401 Unauthorized - token might be invalid
      if (response.status === 401) {
        this.token = null;
        this.clearStoredToken();
        // Don't throw here, let the calling code handle it
      }

      const errorData: ApiError = await response.json().catch(() => ({
        success: false,
        message: 'An error occurred',
      }));
      throw new Error(
        errorData.message || `HTTP error! status: ${response.status}`
      );
    }

    return response.json();
  }

  /**
   * Login with username/email and password
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/auth/login/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(credentials),
      credentials: 'include', // Include cookies for session authentication
    });

    const data = await this.handleResponse<LoginResponse>(response);

    if (data.success) {
      this.token = data.token;
      this.setStoredToken(data.token);
    }

    return data;
  }

  /**
   * Logout current user
   */
  async logout(): Promise<{ success: boolean; message: string }> {
    if (!this.token) {
      return { success: true, message: 'Already logged out' };
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/logout/`, {
        method: 'POST',
        headers: this.getHeaders(),
        credentials: 'include', // Include cookies for session authentication
      });

      const data = await this.handleResponse<{
        success: boolean;
        message: string;
      }>(response);

      // Clear token regardless of response
      this.token = null;
      this.clearStoredToken();

      return data;
    } catch {
      // Clear token even if logout request fails
      this.token = null;
      this.clearStoredToken();
      return { success: true, message: 'Logged out locally' };
    }
  }

  /**
   * Register a new user
   */
  async register(userData: RegisterRequest): Promise<RegisterResponse> {
    const response = await fetch(`${this.baseUrl}/auth/register/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(userData),
    });

    return this.handleResponse<RegisterResponse>(response);
  }

  /**
   * Get current user profile
   */
  async getProfile(): Promise<UserProfileResponse> {
    if (!this.token) {
      throw new Error('Not authenticated');
    }

    const response = await fetch(`${this.baseUrl}/auth/profile/`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include', // Include cookies for session authentication
    });

    return this.handleResponse<UserProfileResponse>(response);
  }

  /**
   * Check authentication status
   */
  async checkAuth(): Promise<AuthCheckResponse> {
    if (!this.token) {
      return { authenticated: false };
    }

    try {
      const response = await fetch(`${this.baseUrl}/auth/check/`, {
        method: 'GET',
        headers: this.getHeaders(),
      });

      if (!response.ok) {
        // If check fails, clear token
        this.token = null;
        localStorage.removeItem('auth_token');
        return { authenticated: false };
      }

      const data = await this.handleResponse<AuthCheckResponse>(response);
      return data;
    } catch {
      // If check fails, clear token
      this.token = null;
      this.clearStoredToken();
      return { authenticated: false };
    }
  }

  /**
   * Get current token
   */
  getToken(): string | null {
    return this.token;
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!this.token;
  }

  /**
   * Set token manually (useful for initialization)
   */
  setToken(token: string | null): void {
    this.token = token;
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  }

  /**
   * Demo login - creates a temporary demo user
   */
  async demoLogin(): Promise<LoginResponse> {
    const response = await fetch(`${this.baseUrl}/auth/api/demo-login/`, {
      method: 'POST',
      headers: this.getHeaders(),
      credentials: 'include', // Include cookies for session authentication
    });

    const data = await this.handleResponse<LoginResponse>(response);

    if (data.success) {
      this.token = data.token;
      this.setStoredToken(data.token);
    }

    return data;
  }
}

// Export singleton instance
export const authApi = new AuthApiService();
