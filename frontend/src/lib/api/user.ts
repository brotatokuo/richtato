import {
  User,
  CreateUserRequest,
  UpdateUserRequest,
  UserRole,
} from '@/types/user';

/**
 * User API service class for handling user management operations
 * This class abstracts the API calls and provides a clean interface for user CRUD operations
 */
export class UserApiService {
  // TODO: Use baseUrl when implementing actual API calls
  // private readonly baseUrl = '/api/users';

  /**
   * Fetch all users with optional filtering and pagination
   * TODO: Implement actual API call to backend
   */
  async getUsers(_params?: {
    page?: number;
    limit?: number;
    role?: UserRole;
    search?: string;
    organizationId?: string;
  }): Promise<{
    users: User[];
    total: number;
    page: number;
    limit: number;
  }> {
    // TODO: Replace with actual API call
    // const response = await fetch(`${this.baseUrl}?${new URLSearchParams(params)}`);
    // return response.json();

    throw new Error('API implementation needed');
  }

  /**
   * Get a specific user by ID
   * TODO: Implement actual API call to backend
   */
  async getUser(_id: string): Promise<User> {
    // TODO: Replace with actual API call
    // const response = await fetch(`${this.baseUrl}/${id}`);
    // return response.json();

    throw new Error('API implementation needed');
  }

  /**
   * Create a new user
   * TODO: Implement actual API call to backend
   */
  async createUser(_userData: CreateUserRequest): Promise<User> {
    // TODO: Replace with actual API call
    // const response = await fetch(this.baseUrl, {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(userData)
    // });
    // return response.json();

    throw new Error('API implementation needed');
  }

  /**
   * Update an existing user
   * TODO: Implement actual API call to backend
   */
  async updateUser(_id: string, _userData: UpdateUserRequest): Promise<User> {
    // TODO: Replace with actual API call
    // const response = await fetch(`${this.baseUrl}/${id}`, {
    //   method: 'PUT',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(userData)
    // });
    // return response.json();

    throw new Error('API implementation needed');
  }

  /**
   * Delete a user
   * TODO: Implement actual API call to backend
   */
  async deleteUser(_id: string): Promise<void> {
    // TODO: Replace with actual API call
    // await fetch(`${this.baseUrl}/${id}`, {
    //   method: 'DELETE'
    // });

    throw new Error('API implementation needed');
  }

  /**
   * Update user role - specialized endpoint for RBAC
   * TODO: Implement actual API call to backend
   */
  async updateUserRole(_id: string, _role: UserRole): Promise<User> {
    // TODO: Replace with actual API call
    // const response = await fetch(`${this.baseUrl}/${id}/role`, {
    //   method: 'PATCH',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({ role })
    // });
    // return response.json();

    throw new Error('API implementation needed');
  }

  /**
   * Get available roles for the current user's organization
   * TODO: Implement actual API call to backend
   */
  async getAvailableRoles(): Promise<UserRole[]> {
    // TODO: Replace with actual API call
    // const response = await fetch('/api/roles');
    // return response.json();

    throw new Error('API implementation needed');
  }
}

// Export singleton instance
export const userApi = new UserApiService();
