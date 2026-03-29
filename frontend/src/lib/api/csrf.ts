/**
 * CSRF token utility for Django session authentication
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1';

class CSRFService {
  // Only used as a fallback when the cookie is absent (e.g. API-fetched token
  // before Django has set the cookie). The cookie is always preferred because
  // Django rotates it on every login() call; caching the old value causes 403s.
  private fetchedToken: string | null = null;

  /**
   * Get CSRF token from Django's CSRF cookie.
   *
   * Always reads from the cookie first so we pick up any rotation Django
   * performed (e.g. the rotate_token() call inside django.contrib.auth.login).
   * Falls back to a lightweight GET request that causes Django to set the
   * cookie when none is present yet (first visit, hard-reload, etc.).
   */
  async getCSRFToken(): Promise<string> {
    // Always prefer the live cookie value — it is the source of truth.
    const cookieValue = document.cookie
      .split('; ')
      .find(row => row.startsWith('csrftoken='))
      ?.split('=')[1];

    if (cookieValue) {
      this.fetchedToken = null; // discard any previously API-fetched token
      return decodeURIComponent(cookieValue);
    }

    // Cookie not present yet — use a previously API-fetched token if available.
    if (this.fetchedToken) {
      return this.fetchedToken;
    }

    // Last resort: hit the CSRF endpoint so Django sets the cookie, then
    // read it back. Cache the result in case the cookie still isn't readable
    // (e.g. HttpOnly misconfiguration).
    try {
      const response = await fetch(`${API_BASE}/auth/csrf/`, {
        method: 'GET',
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        this.fetchedToken = data.csrfToken;
        return data.csrfToken as string;
      }
    } catch {
      // ignore — will throw below
    }

    throw new Error('Unable to obtain CSRF token');
  }

  /**
   * Clear any cached token state (no-op for cookie-based tokens, but clears
   * the API-fetched fallback so it gets re-fetched on the next call).
   */
  clearToken(): void {
    this.fetchedToken = null;
  }

  /**
   * Force a fresh read on the next getCSRFToken() call.
   * Because we now always read the cookie, this mainly matters for the rare
   * API-fetched fallback path.
   */
  async refreshToken(): Promise<string> {
    this.fetchedToken = null;
    return this.getCSRFToken();
  }

  /**
   * Get headers with CSRF token for mutating requests.
   */
  async getHeaders(): Promise<HeadersInit> {
    const token = await this.getCSRFToken();
    return {
      'Content-Type': 'application/json',
      'X-CSRFToken': token,
      'X-Requested-With': 'XMLHttpRequest',
    };
  }

  /**
   * Wrapper around fetch that automatically includes CSRF headers and retries
   * once with a fresh token on 403.  Use this for all mutating requests
   * (POST / PUT / PATCH / DELETE) so the retry logic lives in one place.
   *
   * @example
   *   const response = await csrfService.fetchWithCsrf('/api/v1/accounts/', {
   *     method: 'POST',
   *     body: JSON.stringify(payload),
   *   });
   */
  async fetchWithCsrf(url: string, options: RequestInit): Promise<Response> {
    let response = await fetch(url, {
      ...options,
      headers: {
        ...(options.headers ?? {}),
        ...(await this.getHeaders()),
      },
      credentials: 'include',
    });

    if (response.status === 403) {
      await this.refreshToken();
      response = await fetch(url, {
        ...options,
        headers: {
          ...(options.headers ?? {}),
          ...(await this.getHeaders()),
        },
        credentials: 'include',
      });
    }

    return response;
  }
}

export const csrfService = new CSRFService();
