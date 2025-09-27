/**
 * CSRF token utility for Django session authentication
 */

class CSRFService {
  private token: string | null = null;

  /**
   * Get CSRF token from Django's CSRF cookie
   */
  async getCSRFToken(): Promise<string> {
    if (this.token) {
      return this.token;
    }

    try {
      // First, try to get from cookie (Django sets this automatically)
      const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];

      if (cookieValue) {
        this.token = cookieValue;
        return this.token;
      }

      // If no cookie, try to get from Django endpoint
      const response = await fetch('http://localhost:8000/api/auth/csrf/', {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        this.token = data.csrfToken;
        return this.token;
      }
    } catch (error) {
      console.warn('Failed to get CSRF token:', error);
    }

    throw new Error('Unable to obtain CSRF token');
  }

  /**
   * Clear stored CSRF token
   */
  clearToken(): void {
    this.token = null;
  }

  /**
   * Force refresh of CSRF token
   */
  async refreshToken(): Promise<string> {
    this.token = null;
    return this.getCSRFToken();
  }

  /**
   * Get headers with CSRF token
   */
  async getHeaders(): Promise<HeadersInit> {
    const token = await this.getCSRFToken();
    return {
      'Content-Type': 'application/json',
      'X-CSRFToken': token,
    };
  }
}

export const csrfService = new CSRFService();
