import { fetchWithAuth, SESSION_EXPIRED_EVENT } from '@/lib/api/fetchClient';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

describe('fetchWithAuth', () => {
  beforeEach(() => {
    localStorage.setItem('auth_token', 'test-token');
  });

  afterEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it('dispatches session-expired on 401 when auth token exists', async () => {
    const handler = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, handler);

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 401 }))
    );

    await fetchWithAuth('/api/v1/test');

    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('does not dispatch session-expired on 401 without auth token', async () => {
    localStorage.removeItem('auth_token');
    const handler = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, handler);

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response(null, { status: 401 }))
    );

    await fetchWithAuth('/api/v1/test');

    expect(handler).not.toHaveBeenCalled();
  });

  it('does not dispatch session-expired on successful responses', async () => {
    const handler = vi.fn();
    window.addEventListener(SESSION_EXPIRED_EVENT, handler);

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('{}', { status: 200 }))
    );

    await fetchWithAuth('/api/v1/test');

    expect(handler).not.toHaveBeenCalled();
  });
});
