import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { customersApi } from '../../api';
import { Customer, CustomerDetail } from '../../types/customer';

export const CustomersPage: React.FC = () => {
  const { activeCompany, hasPermission } = useAuth();

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [segment, setSegment] = useState('All');

  const [selectedCustomer, setSelectedCustomer] = useState<CustomerDetail | null>(null);

  // Create Customer Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCustId, setNewCustId] = useState('');
  const [newCustName, setNewCustName] = useState('');
  const [newSegment, setNewSegment] = useState('Consumer');
  const [createError, setCreateError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const resp = await customersApi.list({
        search: search.trim() || undefined,
        segment: segment !== 'All' ? segment : undefined,
        page,
        limit,
      });
      setCustomers(resp.items);
      setTotal(resp.total);
    } catch {
      setCustomers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeCompany) {
      fetchCustomers();
    }
  }, [activeCompany, page, segment]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchCustomers();
  };

  const handleViewCustomer = async (id: string) => {
    try {
      const detail = await customersApi.getById(id);
      setSelectedCustomer(detail);
    } catch {
      alert('Could not load customer purchase history.');
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setIsSubmitting(true);
    try {
      await customersApi.create({
        customer_id: newCustId.trim(),
        customer_name: newCustName.trim(),
        segment: newSegment,
      });
      setShowCreateModal(false);
      setNewCustId('');
      setNewCustName('');
      setPage(1);
      fetchCustomers();
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || 'Failed to create customer.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Customers Directory</h3>
          <p className="text-muted small mb-0">
            Registered customer accounts & lifetime purchase value for <strong>{activeCompany?.company_name}</strong>
          </p>
        </div>
        {hasPermission('CREATE_CUSTOMER') && (
          <button
            onClick={() => {
              setNewCustId(`CUST-${Date.now().toString().slice(-5)}`);
              setShowCreateModal(true);
            }}
            className="btn btn-primary btn-sm d-flex align-items-center gap-1"
          >
            <span>➕</span> New Customer
          </button>
        )}
      </div>

      {/* Filter Toolbar */}
      <div className="card-saas p-3 mb-4">
        <form onSubmit={handleSearchSubmit} className="row g-2 align-items-center">
          <div className="col-12 col-md-6">
            <input
              type="text"
              className="form-control form-control-sm"
              placeholder="Search by customer name or code..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="col-6 col-md-3">
            <select
              className="form-select form-select-sm"
              value={segment}
              onChange={(e) => {
                setSegment(e.target.value);
                setPage(1);
              }}
            >
              <option value="All">All Segments</option>
              <option value="Consumer">Consumer</option>
              <option value="Corporate">Corporate</option>
              <option value="Home Office">Home Office</option>
            </select>
          </div>

          <div className="col-6 col-md-3">
            <button type="submit" className="btn btn-secondary btn-sm w-100">
              Filter
            </button>
          </div>
        </form>
      </div>

      {/* Table */}
      <div className="card-saas overflow-hidden mb-4">
        <div className="table-responsive">
          <table className="table table-saas mb-0">
            <thead>
              <tr>
                <th>Customer ID</th>
                <th>Customer Name</th>
                <th>Segment</th>
                <th className="text-center">Total Orders</th>
                <th className="text-end">Lifetime Revenue</th>
                <th className="text-end">Lifetime Profit</th>
                <th className="text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-5">
                    <div className="spinner-border spinner-border-sm text-primary me-2" role="status" />
                    Loading customers...
                  </td>
                </tr>
              ) : customers.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-5 text-muted">
                    No customers found matching criteria.
                  </td>
                </tr>
              ) : (
                customers.map((c) => (
                  <tr key={c.customer_id}>
                    <td className="fw-semibold text-primary">{c.customer_id}</td>
                    <td className="fw-medium text-dark">{c.customer_name}</td>
                    <td>
                      <span className="badge bg-light text-secondary border">
                        {c.segment || 'Consumer'}
                      </span>
                    </td>
                    <td className="text-center">{c.total_orders.toLocaleString()}</td>
                    <td className="text-end fw-semibold">
                      ${c.total_sales.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className={`text-end fw-semibold ${c.total_profit >= 0 ? 'text-success' : 'text-danger'}`}>
                      ${c.total_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="text-center">
                      <button
                        onClick={() => handleViewCustomer(c.customer_id)}
                        className="btn btn-outline-primary btn-sm py-0 px-2"
                      >
                        History
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="d-flex justify-content-between align-items-center p-3 border-top bg-light">
          <small className="text-muted">
            Showing {customers.length} of {total.toLocaleString()} total customers
          </small>
          <div className="d-flex gap-1">
            <button
              onClick={() => setPage((p) => Math.max(p - 1, 1))}
              disabled={page <= 1 || loading}
              className="btn btn-outline-secondary btn-sm"
            >
              Previous
            </button>
            <span className="btn btn-sm btn-light disabled px-3">
              {page} / {totalPages || 1}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(p + 1, totalPages))}
              disabled={page >= totalPages || loading}
              className="btn btn-outline-secondary btn-sm"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Customer History Modal */}
      {selectedCustomer && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title fw-bold">Customer Profile: {selectedCustomer.customer.customer_name}</h5>
                <button type="button" className="btn-close" onClick={() => setSelectedCustomer(null)} />
              </div>
              <div className="modal-body">
                <div className="row g-2 mb-3 bg-light p-3 rounded small">
                  <div className="col-4">
                    <strong>Customer ID:</strong> {selectedCustomer.customer.customer_id}
                  </div>
                  <div className="col-4">
                    <strong>Segment:</strong> {selectedCustomer.customer.segment}
                  </div>
                  <div className="col-4">
                    <strong>Total Orders:</strong> {selectedCustomer.customer.total_orders}
                  </div>
                  <div className="col-6">
                    <strong>Lifetime Sales:</strong> ${selectedCustomer.customer.total_sales.toFixed(2)}
                  </div>
                  <div className="col-6">
                    <strong>Lifetime Profit:</strong> ${selectedCustomer.customer.total_profit.toFixed(2)}
                  </div>
                </div>

                <h6 className="fw-bold mb-2">Purchase History ({selectedCustomer.recent_orders.length} items)</h6>
                <div className="table-responsive" style={{ maxHeight: '350px' }}>
                  <table className="table table-sm table-bordered mb-0">
                    <thead className="table-light small">
                      <tr>
                        <th>Order ID</th>
                        <th>Order Date</th>
                        <th>Product Description</th>
                        <th>Category</th>
                        <th className="text-center">Qty</th>
                        <th className="text-end">Sales</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedCustomer.recent_orders.map((ord, i) => (
                        <tr key={i}>
                          <td className="small text-primary">{ord.order_id}</td>
                          <td className="small">{ord.order_date}</td>
                          <td className="small fw-medium">{ord.product_name}</td>
                          <td className="small">{ord.category}</td>
                          <td className="text-center small">{ord.quantity}</td>
                          <td className="text-end small fw-semibold">${ord.sales.toFixed(2)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setSelectedCustomer(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Customer Modal */}
      {showCreateModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleCreateSubmit}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Register New Customer</h5>
                  <button type="button" className="btn-close" onClick={() => setShowCreateModal(false)} />
                </div>
                <div className="modal-body">
                  {createError && <div className="alert alert-danger py-2 small mb-3">⚠️ {createError}</div>}
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Customer ID / Code</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      value={newCustId}
                      onChange={(e) => setNewCustId(e.target.value)}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Full Customer Name</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      value={newCustName}
                      onChange={(e) => setNewCustName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Market Segment</label>
                    <select
                      className="form-select form-select-sm"
                      value={newSegment}
                      onChange={(e) => setNewSegment(e.target.value)}
                    >
                      <option value="Consumer">Consumer</option>
                      <option value="Corporate">Corporate</option>
                      <option value="Home Office">Home Office</option>
                    </select>
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowCreateModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={isSubmitting}>
                    {isSubmitting ? 'Registering...' : 'Register Customer'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
