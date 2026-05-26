import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useDrive } from '@/contexts/DriveContext';
import { Navigate, useLocation } from 'react-router-dom';

interface DriveSetupGateProps {
  children: React.ReactNode;
}

export function DriveSetupGate({ children }: DriveSetupGateProps) {
  const location = useLocation();
  const { isDriveActive, isReady } = useDrive();

  if (!isReady) {
    return (
      <div className="flex h-screen items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isDriveActive && location.pathname !== '/setup') {
    return (
      <Navigate
        to="/setup?tab=statements"
        replace
        state={{ from: location.pathname + location.search }}
      />
    );
  }

  return <>{children}</>;
}
