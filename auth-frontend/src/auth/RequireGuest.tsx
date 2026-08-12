import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from './AuthContext';

interface RequireGuestProps {
  children: React.ReactNode;
}

function RequireGuest({ children }: RequireGuestProps): React.ReactElement | null {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    return <Navigate to='/profile' replace />;
  }

  return <>{children}</>;
}

export default RequireGuest;
