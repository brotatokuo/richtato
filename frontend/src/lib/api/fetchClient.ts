/**
 * Centralized fetch wrapper that detects 401 responses and dispatches
 * a session-expired event so AuthContext can log the user out.
 *
 * All API services should use fetchWithAuth() instead of native fetch().
 */

export const SESSION_EXPIRED_EVENT = 'auth:session-expired';

export async function fetchWithAuth(
  input: string | URL,
  init?: RequestInit
): Promise<Response> {
  const url = input instanceof URL ? input.toString() : input;
  const response = await fetch(url, { ...init, credentials: 'include' });

  if (response.status === 401) {
    try {
      if (localStorage.getItem('auth_token')) {
        window.dispatchEvent(new CustomEvent(SESSION_EXPIRED_EVENT));
      }
    } catch {
      // Ignore if localStorage is unavailable
    }
  }

  return response;
}
