import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const TenantRequiredRoute: React.FC = () => {
  const { activeCompany, user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="d-flex justify-content-center align-items-center vh-100 bg-light">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading tenant...</span>
        </div>
      </div>
    );
  }

  // If user has companies but none selected, navigate to selection
  if (!activeCompany && user && user.companies.length > 0) {
    return <Navigate to="/select-tenant" replace />;
  }

  return <Outlet />;
};
