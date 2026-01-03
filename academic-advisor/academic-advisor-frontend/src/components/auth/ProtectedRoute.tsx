import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

type Role = 'student' | 'faculty' | 'admin';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: Role[];          // optional role enforcement
  redirectTo?: string;            // unauthenticated -> default /login
  unauthorizedTo?: string;        // unauthorized -> default /unauthorized
  showSpinner?: boolean;          // show spinner during auth load (default true)
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  allowedRoles,
  redirectTo = '/login',
  unauthorizedTo = '/unauthorized',
  showSpinner = true
}) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  // Wait for auth state
  if (loading) {
    return showSpinner ? (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    ) : null;
  }

  // Not authenticated -> go to login and preserve intended path
  if (!user) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // Enforce allowed roles if provided
  if (allowedRoles && !allowedRoles.includes(user.role as Role)) {
    return <Navigate to={unauthorizedTo} state={{ from: location }} replace />;
  }

  // Authorized
  return <>{children}</>;
};

export default ProtectedRoute;
export { ProtectedRoute };