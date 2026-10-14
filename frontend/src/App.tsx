import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './routes/ProtectedRoute';
import { TenantRequiredRoute } from './routes/TenantRequiredRoute';
import { AppShell } from './layouts/AppShell';
import { LoginPage } from './pages/auth/LoginPage';
import { SelectTenantPage } from './pages/auth/SelectTenantPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { OrdersPage } from './pages/orders/OrdersPage';
import { CustomersPage } from './pages/customers/CustomersPage';
import { ProductsPage } from './pages/products/ProductsPage';
import { StoresPage } from './pages/stores/StoresPage';
import { CompaniesPage } from './pages/companies/CompaniesPage';
import { AnalyticsPage } from './pages/analytics/AnalyticsPage';
import { ImportPage } from './pages/imports/ImportPage';
import { InventoryPage } from './pages/inventory/InventoryPage';
import { IntegrationsPage } from './pages/integrations/IntegrationsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public Authentication */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Area */}
          <Route element={<ProtectedRoute />}>
            <Route path="/select-tenant" element={<SelectTenantPage />} />

            {/* Tenant-Scoped Operations */}
            <Route element={<TenantRequiredRoute />}>
              <Route element={<AppShell />}>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/orders" element={<OrdersPage />} />
                <Route path="/inventory" element={<InventoryPage />} />
                <Route path="/customers" element={<CustomersPage />} />
                <Route path="/products" element={<ProductsPage />} />
                <Route path="/analytics" element={<AnalyticsPage />} />
                <Route path="/imports" element={<ImportPage />} />
                <Route path="/integrations" element={<IntegrationsPage />} />
                <Route path="/stores" element={<StoresPage />} />
                <Route path="/companies" element={<CompaniesPage />} />
              </Route>
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
