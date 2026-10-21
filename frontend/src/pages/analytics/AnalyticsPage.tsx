import React, { useEffect, useState } from 'react';
import { analyticsApi, dashboardApi, BusinessInsight } from '../../api';
import { LineChart } from '../../components/charts/LineChart';
import { BarChart } from '../../components/charts/BarChart';
import { PieChart } from '../../components/charts/PieChart';

export const AnalyticsPage: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(true);
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [trends, setTrends] = useState<{ month: string; sales: number; profit: number }[]>([]);
  const [categoryData, setCategoryData] = useState<{ category: string; total_sales: number; total_profit: number }[]>([]);
  const [regionData, setRegionData] = useState<{ region: string; total_sales: number; total_profit: number }[]>([]);
  const [topProducts, setTopProducts] = useState<{ product_name: string; total_sales: number }[]>([]);
  const [topCustomers, setTopCustomers] = useState<{ customer_name: string; total_sales: number }[]>([]);
  const [insights, setInsights] = useState<BusinessInsight[]>([]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [trendRes, chartsRes, insightsRes] = await Promise.all([
        analyticsApi.getTrends({
          start_date: startDate || undefined,
          end_date: endDate || undefined,
        }),
        dashboardApi.getCharts(),
        analyticsApi.getInsights(),
      ]);

      setTrends(trendRes);
      setCategoryData(chartsRes.sales_by_category || []);
      setRegionData(chartsRes.sales_by_region || []);
      setTopProducts(chartsRes.top_products || []);
      setTopCustomers(chartsRes.top_customers || []);
      setInsights(insightsRes || []);
    } catch (err) {
      console.error('Failed to load analytics data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [startDate, endDate]);

  const totalPeriodSales = trends.reduce((acc, t) => acc + t.sales, 0);
  const totalPeriodProfit = trends.reduce((acc, t) => acc + t.profit, 0);
  const profitMargin = totalPeriodSales > 0 ? ((totalPeriodProfit / totalPeriodSales) * 100).toFixed(1) : '0';

  const exportCSV = () => {
    if (trends.length === 0) return;
    const csvContent =
      'data:text/csv;charset=utf-8,' +
      ['Month,Sales,Profit']
        .concat(trends.map((t) => `${t.month},${t.sales.toFixed(2)},${t.profit.toFixed(2)}`))
        .join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `sales_analytics_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div>
      {/* Header & Filter Controls */}
      <div className="d-flex flex-wrap align-items-center justify-content-between gap-3 mb-4">
        <div>
          <h3 className="fw-bold mb-1">Sales Analytics & Insights</h3>
          <p className="text-muted small mb-0">Multi-dimensional slice analysis and time-series performance metrics.</p>
        </div>
        <div className="d-flex flex-wrap align-items-center gap-2">
          <div className="input-group input-group-sm" style={{ width: 'auto' }}>
            <span className="input-group-text bg-white">From</span>
            <input
              type="date"
              className="form-control"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
            />
          </div>
          <div className="input-group input-group-sm" style={{ width: 'auto' }}>
            <span className="input-group-text bg-white">To</span>
            <input
              type="date"
              className="form-control"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
            />
          </div>
          <button
            className="btn btn-sm btn-outline-secondary"
            onClick={() => {
              setStartDate('');
              setEndDate('');
            }}
          >
            Clear
          </button>
          <button className="btn btn-sm btn-primary d-flex align-items-center gap-1" onClick={exportCSV}>
            <i className="bi bi-download"></i> Export CSV
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading analytics...</span>
          </div>
        </div>
      ) : (
        <>
          {/* Quick Period Summary Cards */}
          <div className="row g-3 mb-4">
            <div className="col-12 col-md-4">
              <div className="card shadow-sm border-0 h-100">
                <div className="card-body">
                  <span className="text-muted small fw-medium">Period Revenue</span>
                  <h4 className="fw-bold text-primary mt-1 mb-0">${totalPeriodSales.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</h4>
                </div>
              </div>
            </div>
            <div className="col-12 col-md-4">
              <div className="card shadow-sm border-0 h-100">
                <div className="card-body">
                  <span className="text-muted small fw-medium">Period Net Profit</span>
                  <h4 className="fw-bold text-success mt-1 mb-0">${totalPeriodProfit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</h4>
                </div>
              </div>
            </div>
            <div className="col-12 col-md-4">
              <div className="card shadow-sm border-0 h-100">
                <div className="card-body">
                  <span className="text-muted small fw-medium">Overall Profit Margin</span>
                  <h4 className="fw-bold text-info mt-1 mb-0">{profitMargin}%</h4>
                </div>
              </div>
            </div>
          </div>

          {/* Explainable Business Insights Section */}
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-header bg-white border-0 pt-3 pb-0 d-flex justify-content-between align-items-center">
              <div>
                <h6 className="fw-bold mb-0 text-dark">
                  <i className="bi bi-lightbulb text-warning me-2"></i>Explainable Business Insights & Operations Alerts
                </h6>
                <small className="text-muted">Rule-based analytical detections with explicit rationale, supporting data, and limitations.</small>
              </div>
              <span className="badge bg-light text-dark border">{insights.length} active detection{insights.length === 1 ? '' : 's'}</span>
            </div>
            <div className="card-body">
              {insights.length > 0 ? (
                <div className="row g-3">
                  {insights.map((ins) => (
                    <div key={ins.insight_id} className="col-12 col-md-6">
                      <div className={`p-3 rounded border h-100 ${
                        ins.severity === 'CRITICAL' ? 'border-danger bg-danger bg-opacity-10' :
                        ins.severity === 'WARNING' ? 'border-warning bg-warning bg-opacity-10' :
                        'border-info bg-info bg-opacity-10'
                      }`}>
                        <div className="d-flex justify-content-between align-items-center mb-2">
                          <span className={`badge ${
                            ins.severity === 'CRITICAL' ? 'bg-danger' :
                            ins.severity === 'WARNING' ? 'bg-warning text-dark' :
                            'bg-info text-dark'
                          }`}>
                            {ins.severity}
                          </span>
                          <span className="text-muted small">{ins.category.replace('_', ' ')}</span>
                        </div>
                        <h6 className="fw-bold mb-1">{ins.title}</h6>
                        <p className="small mb-2 text-dark">{ins.summary}</p>
                        
                        <div className="bg-white p-2 rounded mb-2 border small">
                          <div className="mb-1"><strong>Why this was detected:</strong> {ins.explanation}</div>
                          <div className="text-muted"><strong>Limitations:</strong> {ins.limitations}</div>
                        </div>

                        <div className="d-flex align-items-center gap-1 text-primary small">
                          <i className="bi bi-arrow-right-circle"></i>
                          <span><strong>Action:</strong> {ins.recommended_action}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted mb-0 py-2 text-center">No anomalies or stockout alerts detected for active tenant.</p>
              )}
            </div>
          </div>

          {/* Time Series Chart */}
          <div className="card shadow-sm border-0 mb-4">
            <div className="card-body">
              <h6 className="fw-bold mb-3">Temporal Revenue Trend (Monthly)</h6>
              {trends.length > 0 ? (
                <LineChart
                  x={trends.map((t) => t.month)}
                  y={trends.map((t) => t.sales)}
                  title="Monthly Revenue ($)"
                  color="#2563eb"
                  height={320}
                />
              ) : (
                <p className="text-muted text-center py-4">No transactions found for selected date range.</p>
              )}
            </div>
          </div>

          {/* Category and Region Breakdown */}
          <div className="row g-4 mb-4">
            <div className="col-12 col-lg-7">
              <div className="card shadow-sm border-0 h-100">
                <div className="card-body">
                  <h6 className="fw-bold mb-3">Sales & Profit by Category</h6>
                  {categoryData.length > 0 ? (
                    <BarChart
                      x={categoryData.map((c) => c.category)}
                      y={categoryData.map((c) => c.total_sales)}
                      color="#0284c7"
                      height={300}
                    />
                  ) : (
                    <p className="text-muted text-center py-4">No category data.</p>
                  )}
                </div>
              </div>
            </div>
            <div className="col-12 col-lg-5">
              <div className="card shadow-sm border-0 h-100">
                <div className="card-body">
                  <h6 className="fw-bold mb-3">Regional Share of Sales</h6>
                  {regionData.length > 0 ? (
                    <PieChart
                      labels={regionData.map((r) => r.region)}
                      values={regionData.map((r) => r.total_sales)}
                      height={300}
                    />
                  ) : (
                    <p className="text-muted text-center py-4">No regional data.</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Top Products and Top Customers */}
          <div className="row g-4">
            <div className="col-12 col-lg-6">
              <div className="card shadow-sm border-0 h-100">
                <div className="card-body">
                  <h6 className="fw-bold mb-3">Top Revenue Generating Products</h6>
                  {topProducts.length > 0 ? (
                    <BarChart
                      orientation="h"
                      x={topProducts.map((p) => p.total_sales)}
                      y={topProducts.map((p) => p.product_name.slice(0, 25) + '...')}
                      color="#3b82f6"
                      height={340}
                    />
                  ) : (
                    <p className="text-muted text-center py-4">No products found.</p>
                  )}
                </div>
              </div>
            </div>
            <div className="col-12 col-lg-6">
              <div className="card shadow-sm border-0 h-100">
                <div className="card-body">
                  <h6 className="fw-bold mb-3">Key Enterprise Customers</h6>
                  <div className="table-responsive">
                    <table className="table table-sm table-hover align-middle">
                      <thead className="table-light">
                        <tr>
                          <th>#</th>
                          <th>Customer</th>
                          <th className="text-end">Total Spend</th>
                        </tr>
                      </thead>
                      <tbody>
                        {topCustomers.map((cust, idx) => (
                          <tr key={idx}>
                            <td className="text-muted small">{idx + 1}</td>
                            <td className="fw-medium">{cust.customer_name}</td>
                            <td className="text-end fw-bold text-primary">
                              ${cust.total_sales.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default AnalyticsPage;
