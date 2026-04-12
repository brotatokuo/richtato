/**
 * Shared base API client that provides common fetch helpers.
 *
 * Subclass this in each service to eliminate repeated getHeaders /
 * handleResponse / fetch boilerplate.
 */
export class BaseApiClient {
  protected baseUrl: string;

  constructor(path: string) {
    const root = import.meta.env.VITE_API_BASE_URL || '/api/v1';
    this.baseUrl = `${root}${path}`;
  }

  protected getHeaders(): HeadersInit {
    return {
      'Content-Type': 'application/json',
    };
  }

  protected async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.error || `HTTP error! status: ${response.status}`
      );
    }
    return response.json();
  }

  protected async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: this.getHeaders(),
      credentials: 'include',
    });
    return this.handleResponse<T>(response);
  }
}
