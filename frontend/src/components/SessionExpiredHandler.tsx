import { SESSION_EXPIRED_EVENT } from '@/lib/api/fetchClient';
import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const PUBLIC_PATHS = new Set(['/welcome', '/login', '/register']);

/**
 * Redirects to /welcome when any API call detects a stale session (401).
 * Must render inside BrowserRouter.
 */
export function SessionExpiredHandler() {
  const navigate = useNavigate();
  const { pathname } = useLocation();

  useEffect(() => {
    const handleSessionExpired = () => {
      if (!PUBLIC_PATHS.has(pathname)) {
        navigate('/welcome', { replace: true });
      }
    };

    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    return () =>
      window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
  }, [navigate, pathname]);

  return null;
}
