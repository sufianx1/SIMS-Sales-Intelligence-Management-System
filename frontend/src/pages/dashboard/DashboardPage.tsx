import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { dashboardApi } from '../../api';
import { BarChart } from '../../components/charts/BarChart';
import { PieChart } from '../../components/charts/PieChart';

export const DashboardPage: React.FC = () => {
  const { activeCompany } = useAuth();

  const [metrics, setMetrics] = useState<{
    total_sales: number;
    total_profit: number;
    total_orders: number;
    average_order_value?: number;
    total_customers: number;
    total_products: number;
  } | null>(null);

  const [charts, setCharts] = useState<{
    sales_by_category: { category: string; total_sales: number; total_profit: number }[];
    profit_by_category: { category: string; total_sales: number; total_profit: number }[];
    sales_by_region: { region: string; total_sales: number; total_profit: number }[];
    top_products: { product_name: string; total_sales: number }[];
    top_customers: { customer_name: string; total_sales: number }[];
  } | null>(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [m, c] = await Promise.all([
          dashboardApi.getMetrics(),
          dashboardApi.getCharts(),
        ]);
        setMetrics(m);
        setCharts(c);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load dashboard analytics.');
      } finally {
        setLoading(false);
      }
    };

    if (activeCompany) {
      fetchDashboardData();
    }
  }, [activeCompany]);

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading dashboard analytics...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger p-3 rounded" role="alert">
        <h5 className="alert-heading">Dashboard Error</h5>
        <p className="mb-0">{error}</p>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Executive Dashboard</h3>
          <p className="text-muted small mb-0">
            Real-time sales performance and operational overview for <strong>{activeCompany?.company_name}</strong>
          </p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1"
        >
          <span>🔄</span> Refresh Metrics
        </button>
      </div>

      {/* KPI Cards Row */}
      <div className="row g-3 mb-4">
        <div className="col-12 col-sm-6 col-xl">
          <div className="metric-card">
            <div className="metric-label">Total Revenue</div>
            <div className="metric-value text-primary">
              ${metrics?.total_sales.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <small className="text-muted" style={{ fontSize: '0.75rem' }}>Gross sales across all orders</small>
          </div>
        </div>

        <div className="col-12 col-sm-6 col-xl">
          <div className="metric-card">
            <div className="metric-label">Total Profit</div>
            <div className={`metric-value ${metrics && metrics.total_profit >= 0 ? 'text-success' : 'text-danger'}`}>
              ${metrics?.total_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <small className="text-muted" style={{ fontSize: '0.75rem' }}>
              Margin: {metrics && metrics.total_sales > 0 ? ((metrics.total_profit / metrics.total_sales) * 100).toFixed(1) : 0}%
            </small>
          </div>
        </div>

        <div className="col-12 col-sm-6 col-xl">
          <div className="metric-card">
            <div className="metric-label">Total Orders</div>
            <div className="metric-value">
              {metrics?.total_orders.toLocaleString()}
            </div>
            <small className="text-muted" style={{ fontSize: '0.75rem' }}>Processed transaction headers</small>
          </div>
        </div>

        <div className="col-12 col-sm-6 col-xl">
          <div className="metric-card">
            <div className="metric-label">Avg Order Value</div>
            <div className="metric-value text-info">
              ${(metrics?.average_order_value ?? (metrics && metrics.total_orders > 0 ? metrics.total_sales / metrics.total_orders : 0)).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
            <small className="text-muted" style={{ fontSize: '0.75rem' }}>Revenue per transaction</small>
          </div>
        </div>

        <div className="col-12 col-sm-6 col-xl">
          <div className="metric-card">
            <div className="metric-label">Total Customers</div>
            <div className="metric-value">
              {metrics?.total_customers.toLocaleString()}
            </div>
            <small className="text-muted" style={{ fontSize: '0.75rem' }}>Registered client directory</small>
          </div>
        </div>

        <div className="col-12 col-sm-6 col-xl">
          <div className="metric-card">
            <div className="metric-label">Active SKUs</div>
            <div className="metric-value">
              {metrics?.total_products.toLocaleString()}
            </div>
            <small className="text-muted" style={{ fontSize: '0.75rem' }}>Catalog items available</small>
          </div>
        </div>
      </div>

      {/* Visualizations Grid */}
      <div className="row g-4 mb-4">
        {/* Sales by Category */}
        <div className="col-12 col-lg-6">
          <div className="card-saas p-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <h6 className="fw-bold mb-0">Sales by Category</h6>
              <span className="badge bg-light text-secondary border">Product Lines</span>
            </div>
            {charts && charts.sales_by_category.length > 0 ? (
              <BarChart
                x={charts.sales_by_category.map((c) => c.category)}
                y={charts.sales_by_category.map((c) => c.total_sales)}
                color="#2563eb"
                height={280}
              />
            ) : (
              <div className="text-center py-5 text-muted small">No category data recorded.</div>
            )}
          </div>
        </div>

        {/* Sales by Region */}
        <div className="col-12 col-lg-6">
          <div className="card-saas p-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <h6 className="fw-bold mb-0">Regional Market Share</h6>
              <span className="badge bg-light text-secondary border">Geographic</span>
            </div>
            {charts && charts.sales_by_region.length > 0 ? (
              <PieChart
                labels={charts.sales_by_region.map((r) => r.region)}
                values={charts.sales_by_region.map((r) => r.total_sales)}
                height={280}
              />
            ) : (
              <div className="text-center py-5 text-muted small">No regional data recorded.</div>
            )}
          </div>
        </div>

        {/* Top 10 Products by Revenue */}
        <div className="col-12 col-lg-6">
          <div className="card-saas p-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <h6 className="fw-bold mb-0">Top 10 Products by Revenue</h6>
              <span className="badge bg-light text-secondary border">Top Sellers</span>
            </div>
            {charts && charts.top_products.length > 0 ? (
              <BarChart
                x={charts.top_products.map((p) => p.product_name)}
                y={charts.top_products.map((p) => p.total_sales)}
                orientation="h"
                color="#3b82f6"
                height={320}
              />
            ) : (
              <div className="text-center py-5 text-muted small">No product sales yet.</div>
            )}
          </div>
        </div>

        {/* Top 10 Customers by Purchases */}
        <div className="col-12 col-lg-6">
          <div className="card-saas p-3">
            <div className="d-flex justify-content-between align-items-center mb-2">
              <h6 className="fw-bold mb-0">Top 10 Customers by Lifetime Value</h6>
              <span className="badge bg-light text-secondary border">VIP Clients</span>
            </div>
            {charts && charts.top_customers.length > 0 ? (
              <BarChart
                x={charts.top_customers.map((c) => c.customer_name)}
                y={charts.top_customers.map((c) => c.total_sales)}
                orientation="h"
                color="#059669"
                height={320}
              />
            ) : (
              <div className="text-center py-5 text-muted small">No customer transactions yet.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
