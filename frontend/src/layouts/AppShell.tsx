import React from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export const AppShell: React.FC = () => {
  const { user, activeCompany, logout, hasPermission } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="d-flex min-vh-100">
      {/* Sidebar Navigation */}
      <aside className="app-sidebar">
        <div className="brand-header d-flex align-items-center gap-2">
          <span className="fs-4">🚀</span>
          <div>
            <div className="fw-bold text-white lh-1 fs-6">SIMS</div>
            <small style={{ fontSize: '0.70rem', color: '#94a3b8' }}>Sales Intelligence & Management</small>
          </div>
        </div>

        {/* Active Tenant Card */}
        {activeCompany && (
          <div className="tenant-badge">
            <div className="d-flex justify-content-between align-items-center mb-1">
              <span className="badge bg-primary text-uppercase" style={{ fontSize: '0.65rem' }}>
                Active Tenant
              </span>
              {user && user.companies.length > 1 && (
                <button
                  onClick={() => navigate('/select-tenant')}
                  className="btn btn-link btn-sm p-0 text-decoration-none"
                  style={{ fontSize: '0.75rem', color: '#60a5fa' }}
                >
                  Switch
                </button>
              )}
            </div>
            <div className="fw-semibold text-white text-truncate">{activeCompany.company_name}</div>
            <small style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              {activeCompany.role_name}
            </small>
          </div>
        )}

        {/* Navigation Items */}
        <nav className="nav flex-column mt-2 flex-grow-1">
          <NavLink to="/dashboard" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span>📊</span> Dashboard
          </NavLink>
          <NavLink to="/orders" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span>🛒</span> Orders
          </NavLink>
          <NavLink to="/inventory" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span>📦</span> Inventory
          </NavLink>
          <NavLink to="/products" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span>🏷️</span> Products
          </NavLink>
          <NavLink to="/customers" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span>👥</span> Customers
          </NavLink>
          <NavLink to="/analytics" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span>📈</span> Sales Analytics
          </NavLink>
          <NavLink to="/imports" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span>📥</span> Flexible CSV Import
          </NavLink>
          <NavLink to="/integrations" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span>🔗</span> Integrations
          </NavLink>
          <NavLink to="/stores" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            <span>🏬</span> Stores
          </NavLink>

          {/* Platform Administrator Menu */}
          {user?.is_system_admin && (
            <>
              <div className="px-3 pt-3 pb-1 text-uppercase text-muted" style={{ fontSize: '0.68rem', letterSpacing: '0.05em' }}>
                Platform Admin
              </div>
              <NavLink to="/companies" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
                <span>🏢</span> All Tenants
              </NavLink>
            </>
          )}
        </nav>

        {/* User Footer Profile */}
        <div className="p-3 border-top border-secondary border-opacity-25 d-flex align-items-center justify-content-between">
          <div className="text-truncate me-2">
            <div className="text-white fw-medium text-truncate" style={{ fontSize: '0.85rem' }}>
              {user?.name}
            </div>
            <div className="text-muted text-truncate" style={{ fontSize: '0.75rem' }}>
              {user?.email}
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="btn btn-outline-danger btn-sm px-2 py-1"
            title="Log Out"
          >
            Logout
          </button>
        </div>
      </aside>

      {/* Main View Area */}
      <div className="d-flex flex-column flex-grow-1 overflow-auto">
        <header className="app-topbar d-flex justify-content-between align-items-center">
          <div className="d-flex align-items-center gap-2">
            <span className="badge bg-light text-dark border">
              Tenant: <strong>{activeCompany ? activeCompany.company_name : 'None'}</strong>
            </span>
            {activeCompany?.store_name ? (
              <span className="badge bg-info-subtle text-info-emphasis border border-info-subtle">
                Assigned Store: {activeCompany.store_name}
              </span>
            ) : (
              <span className="badge bg-primary-subtle text-primary border border-primary-subtle">
                Visibility: All Stores (Consolidated)
              </span>
            )}
          </div>

          <div className="d-flex align-items-center gap-3">
            <span className="badge bg-success-subtle text-success border border-success-subtle small py-1 px-2">
              🍃 MongoDB — SIMS Multi-Tenant Engine
            </span>
          </div>
        </header>

        <main className="content-wrapper flex-grow-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
