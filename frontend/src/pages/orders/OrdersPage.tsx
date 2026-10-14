import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { ordersApi, customersApi, productsApi, storesApi } from '../../api';
import { OrderSummary, OrderDetail, OrderCreate } from '../../types/order';
import { Customer } from '../../types/customer';
import { Product } from '../../types/product';
import { Store } from '../../types/company';

export const OrdersPage: React.FC = () => {
  const { activeCompany, hasPermission } = useAuth();

  const [orders, setOrders] = useState<OrderSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [loading, setLoading] = useState(true);

  // Filters
  const [region, setRegion] = useState('All');
  const [shipMode, setShipMode] = useState('All');
  const [search, setSearch] = useState('');

  // Selected Order for Modal
  const [selectedOrder, setSelectedOrder] = useState<OrderDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Create Order Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [customersList, setCustomersList] = useState<Customer[]>([]);
  const [productsList, setProductsList] = useState<Product[]>([]);
  const [storesList, setStoresList] = useState<Store[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // New Order Form
  const [newOrderId, setNewOrderId] = useState(`ORD-${Date.now().toString().slice(-6)}`);
  const [newOrderDate, setNewOrderDate] = useState(new Date().toISOString().split('T')[0]);
  const [newCustomerId, setNewCustomerId] = useState('');
  const [newStoreId, setNewStoreId] = useState<number | undefined>(undefined);
  const [newRegion, setNewRegion] = useState('West');
  const [newCity, setNewCity] = useState('Seattle');
  const [newState, setNewState] = useState('Washington');
  const [newShipMode, setNewShipMode] = useState('Standard Class');

  // New Order Lines
  const [lines, setLines] = useState<
    { product_id: string; quantity: number; sales: number; discount: number; profit: number }[]
  >([{ product_id: '', quantity: 1, sales: 50.0, discount: 0.0, profit: 15.0 }]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const resp = await ordersApi.list({
        region: region !== 'All' ? region : undefined,
        ship_mode: shipMode !== 'All' ? shipMode : undefined,
        search: search.trim() || undefined,
        page,
        limit,
      });
      setOrders(resp.items);
      setTotal(resp.total);
    } catch {
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeCompany) {
      fetchOrders();
    }
  }, [activeCompany, page, region, shipMode]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchOrders();
  };

  const handleViewOrder = async (orderId: string) => {
    setLoadingDetail(true);
    try {
      const detail = await ordersApi.getById(orderId);
      setSelectedOrder(detail);
    } catch {
      alert('Failed to load order line details.');
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleDeleteOrder = async (orderId: string) => {
    if (!window.confirm(`Are you sure you want to delete Order ${orderId}? This cannot be undone.`)) {
      return;
    }
    try {
      await ordersApi.delete(orderId);
      fetchOrders();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete order.');
    }
  };

  const openCreateModal = async () => {
    setCreateError(null);
    setShowCreateModal(true);
    try {
      const [cRes, pRes, sRes] = await Promise.all([
        customersApi.list({ limit: 100 }),
        productsApi.list({ limit: 100 }),
        storesApi.list(),
      ]);
      setCustomersList(cRes.items);
      setProductsList(pRes.items);
      setStoresList(sRes);
      if (cRes.items.length > 0) setNewCustomerId(cRes.items[0].customer_id);
      if (pRes.items.length > 0) {
        setLines([
          {
            product_id: pRes.items[0].product_id,
            quantity: 1,
            sales: 100.0,
            discount: 0.05,
            profit: 25.0,
          },
        ]);
      }
      if (sRes.length > 0) setNewStoreId(sRes[0].store_id);
    } catch {
      setCreateError('Could not load catalog dependencies.');
    }
  };

  const handleAddLine = () => {
    const defaultSku = productsList.length > 0 ? productsList[0].product_id : '';
    setLines([...lines, { product_id: defaultSku, quantity: 1, sales: 50.0, discount: 0.0, profit: 12.0 }]);
  };

  const handleRemoveLine = (idx: number) => {
    if (lines.length <= 1) return;
    setLines(lines.filter((_, i) => i !== idx));
  };

  const handleLineChange = (idx: number, field: string, val: any) => {
    const updated = [...lines];
    (updated[idx] as any)[field] = val;
    setLines(updated);
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setIsSubmitting(true);

    const payload: OrderCreate = {
      order_id: newOrderId.trim(),
      order_date: newOrderDate,
      customer_id: newCustomerId,
      store_id: newStoreId,
      region: newRegion,
      city: newCity,
      state: newState,
      ship_mode: newShipMode,
      lines: lines.map((l) => ({
        product_id: l.product_id,
        quantity: Number(l.quantity),
        sales: Number(l.sales),
        discount: Number(l.discount),
        profit: Number(l.profit),
      })),
    };

    try {
      await ordersApi.create(payload);
      setShowCreateModal(false);
      setPage(1);
      fetchOrders();
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || 'Failed to submit order transaction.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      {/* Title & Actions */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Orders Management</h3>
          <p className="text-muted small mb-0">
            View, search, and manage line-item transactions for <strong>{activeCompany?.company_name}</strong>
          </p>
        </div>
        {hasPermission('CREATE_ORDER') && (
          <button onClick={openCreateModal} className="btn btn-primary btn-sm d-flex align-items-center gap-1">
            <span>➕</span> Create New Order
          </button>
        )}
      </div>

      {/* Filter Toolbar */}
      <div className="card-saas p-3 mb-4">
        <form onSubmit={handleSearchSubmit} className="row g-2 align-items-center">
          <div className="col-12 col-md-4">
            <input
              type="text"
              className="form-control form-control-sm"
              placeholder="Search by Order ID or Customer Name..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="col-6 col-md-2">
            <select
              className="form-select form-select-sm"
              value={region}
              onChange={(e) => {
                setRegion(e.target.value);
                setPage(1);
              }}
            >
              <option value="All">All Regions</option>
              <option value="West">West</option>
              <option value="East">East</option>
              <option value="Central">Central</option>
              <option value="South">South</option>
            </select>
          </div>

          <div className="col-6 col-md-2">
            <select
              className="form-select form-select-sm"
              value={shipMode}
              onChange={(e) => {
                setShipMode(e.target.value);
                setPage(1);
              }}
            >
              <option value="All">All Ship Modes</option>
              <option value="Standard Class">Standard Class</option>
              <option value="Second Class">Second Class</option>
              <option value="First Class">First Class</option>
              <option value="Same Day">Same Day</option>
            </select>
          </div>

          <div className="col-12 col-md-2">
            <button type="submit" className="btn btn-secondary btn-sm w-100">
              Filter
            </button>
          </div>
        </form>
      </div>

      {/* Orders Table */}
      <div className="card-saas overflow-hidden mb-4">
        <div className="table-responsive">
          <table className="table table-saas mb-0">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Order Date</th>
                <th>Customer</th>
                <th>Store / Branch</th>
                <th>Region</th>
                <th>Items</th>
                <th className="text-end">Total Sales</th>
                <th className="text-end">Total Profit</th>
                <th className="text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={9} className="text-center py-5">
                    <div className="spinner-border spinner-border-sm text-primary me-2" role="status" />
                    Loading orders...
                  </td>
                </tr>
              ) : orders.length === 0 ? (
                <tr>
                  <td colSpan={9} className="text-center py-5 text-muted">
                    No matching orders found.
                  </td>
                </tr>
              ) : (
                orders.map((ord) => (
                  <tr key={ord.order_id}>
                    <td className="fw-semibold text-primary">{ord.order_id}</td>
                    <td>{ord.order_date}</td>
                    <td className="fw-medium text-dark">{ord.customer_name}</td>
                    <td>
                      <span className="badge bg-light text-secondary border">
                        {ord.store_name || 'All Stores'}
                      </span>
                    </td>
                    <td>{ord.region || '—'}</td>
                    <td>
                      <span className="badge bg-secondary-subtle text-secondary-emphasis">
                        {ord.line_count} line{ord.line_count > 1 ? 's' : ''} ({ord.total_quantity} units)
                      </span>
                    </td>
                    <td className="text-end fw-semibold">
                      ${ord.total_sales.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className={`text-end fw-semibold ${ord.total_profit >= 0 ? 'text-success' : 'text-danger'}`}>
                      ${ord.total_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="text-center">
                      <div className="btn-group btn-group-sm">
                        <button
                          onClick={() => handleViewOrder(ord.order_id)}
                          className="btn btn-outline-primary py-0 px-2"
                          title="View Lines"
                        >
                          View
                        </button>
                        {hasPermission('DELETE_ORDER') && (
                          <button
                            onClick={() => handleDeleteOrder(ord.order_id)}
                            className="btn btn-outline-danger py-0 px-2"
                            title="Delete"
                          >
                            ✕
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="d-flex justify-content-between align-items-center p-3 border-top bg-light">
          <small className="text-muted">
            Showing {orders.length} of {total.toLocaleString()} total orders
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

      {/* Order Detail Modal */}
      {selectedOrder && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title fw-bold">Order Details: {selectedOrder.order.order_id}</h5>
                <button type="button" className="btn-close" onClick={() => setSelectedOrder(null)} />
              </div>
              <div className="modal-body">
                <div className="row g-2 mb-3 small bg-light p-3 rounded">
                  <div className="col-4">
                    <strong>Customer:</strong> {selectedOrder.order.customer_name}
                  </div>
                  <div className="col-4">
                    <strong>Order Date:</strong> {selectedOrder.order.order_date}
                  </div>
                  <div className="col-4">
                    <strong>Ship Mode:</strong> {selectedOrder.order.ship_mode || 'Standard'}
                  </div>
                  <div className="col-4">
                    <strong>Region:</strong> {selectedOrder.order.region || '—'}
                  </div>
                  <div className="col-4">
                    <strong>Location:</strong> {selectedOrder.order.city}, {selectedOrder.order.state}
                  </div>
                  <div className="col-4">
                    <strong>Store:</strong> {selectedOrder.order.store_name || 'Primary Branch'}
                  </div>
                </div>

                <h6 className="fw-bold mb-2">Line Items ({selectedOrder.lines.length})</h6>
                <div className="table-responsive">
                  <table className="table table-sm table-bordered">
                    <thead className="table-light">
                      <tr>
                        <th>Product SKU</th>
                        <th>Product Name</th>
                        <th>Category</th>
                        <th className="text-center">Qty</th>
                        <th className="text-end">Sales</th>
                        <th className="text-end">Discount</th>
                        <th className="text-end">Profit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedOrder.lines.map((l, i) => (
                        <tr key={i}>
                          <td className="small text-muted">{l.product_id}</td>
                          <td className="fw-medium small">{l.product_name || '—'}</td>
                          <td className="small">{l.category || '—'}</td>
                          <td className="text-center">{l.quantity}</td>
                          <td className="text-end fw-semibold">${l.sales.toFixed(2)}</td>
                          <td className="text-end">{(l.discount * 100).toFixed(0)}%</td>
                          <td className={`text-end fw-semibold ${l.profit >= 0 ? 'text-success' : 'text-danger'}`}>
                            ${l.profit.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    <tfoot className="table-light">
                      <tr className="fw-bold">
                        <td colSpan={4} className="text-end">
                          Order Totals:
                        </td>
                        <td className="text-end">${selectedOrder.order.total_sales.toFixed(2)}</td>
                        <td></td>
                        <td className="text-end">${selectedOrder.order.total_profit.toFixed(2)}</td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setSelectedOrder(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Order Modal */}
      {showCreateModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-xl modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleCreateSubmit}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Create New Order Transaction</h5>
                  <button type="button" className="btn-close" onClick={() => setShowCreateModal(false)} />
                </div>
                <div className="modal-body">
                  {createError && <div className="alert alert-danger py-2 small mb-3">⚠️ {createError}</div>}

                  {/* Order Header Fields */}
                  <div className="row g-2 mb-3">
                    <div className="col-md-3">
                      <label className="form-label small fw-semibold">Order ID</label>
                      <input
                        type="text"
                        className="form-control form-control-sm"
                        value={newOrderId}
                        onChange={(e) => setNewOrderId(e.target.value)}
                        required
                      />
                    </div>
                    <div className="col-md-3">
                      <label className="form-label small fw-semibold">Order Date</label>
                      <input
                        type="date"
                        className="form-control form-control-sm"
                        value={newOrderDate}
                        onChange={(e) => setNewOrderDate(e.target.value)}
                        required
                      />
                    </div>
                    <div className="col-md-3">
                      <label className="form-label small fw-semibold">Customer</label>
                      <select
                        className="form-select form-select-sm"
                        value={newCustomerId}
                        onChange={(e) => setNewCustomerId(e.target.value)}
                        required
                      >
                        {customersList.map((c) => (
                          <option key={c.customer_id} value={c.customer_id}>
                            {c.customer_name} ({c.customer_id})
                          </option>
                        ))}
                      </select>
                    </div>
                    <div className="col-md-3">
                      <label className="form-label small fw-semibold">Store / Branch</label>
                      <select
                        className="form-select form-select-sm"
                        value={newStoreId || ''}
                        onChange={(e) => setNewStoreId(e.target.value ? Number(e.target.value) : undefined)}
                      >
                        <option value="">(None / General)</option>
                        {storesList.map((s) => (
                          <option key={s.store_id} value={s.store_id}>
                            {s.store_name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="col-md-3">
                      <label className="form-label small fw-semibold">Region</label>
                      <select
                        className="form-select form-select-sm"
                        value={newRegion}
                        onChange={(e) => setNewRegion(e.target.value)}
                      >
                        <option value="West">West</option>
                        <option value="East">East</option>
                        <option value="Central">Central</option>
                        <option value="South">South</option>
                      </select>
                    </div>
                    <div className="col-md-3">
                      <label className="form-label small fw-semibold">City</label>
                      <input
                        type="text"
                        className="form-control form-control-sm"
                        value={newCity}
                        onChange={(e) => setNewCity(e.target.value)}
                      />
                    </div>
                    <div className="col-md-3">
                      <label className="form-label small fw-semibold">State</label>
                      <input
                        type="text"
                        className="form-control form-control-sm"
                        value={newState}
                        onChange={(e) => setNewState(e.target.value)}
                      />
                    </div>
                    <div className="col-md-3">
                      <label className="form-label small fw-semibold">Ship Mode</label>
                      <select
                        className="form-select form-select-sm"
                        value={newShipMode}
                        onChange={(e) => setNewShipMode(e.target.value)}
                      >
                        <option value="Standard Class">Standard Class</option>
                        <option value="Second Class">Second Class</option>
                        <option value="First Class">First Class</option>
                        <option value="Same Day">Same Day</option>
                      </select>
                    </div>
                  </div>

                  {/* Line Items Builder */}
                  <div className="d-flex justify-content-between align-items-center mb-2 pt-2 border-top">
                    <h6 className="fw-bold mb-0">Order Line Items</h6>
                    <button type="button" onClick={handleAddLine} className="btn btn-outline-primary btn-sm py-0">
                      + Add Item
                    </button>
                  </div>

                  <div className="table-responsive">
                    <table className="table table-sm table-bordered">
                      <thead className="table-light small">
                        <tr>
                          <th>Product SKU</th>
                          <th style={{ width: '100px' }}>Quantity</th>
                          <th style={{ width: '130px' }}>Sales ($)</th>
                          <th style={{ width: '110px' }}>Discount (0-1)</th>
                          <th style={{ width: '130px' }}>Profit ($)</th>
                          <th style={{ width: '50px' }}></th>
                        </tr>
                      </thead>
                      <tbody>
                        {lines.map((line, idx) => (
                          <tr key={idx}>
                            <td>
                              <select
                                className="form-select form-select-sm"
                                value={line.product_id}
                                onChange={(e) => handleLineChange(idx, 'product_id', e.target.value)}
                                required
                              >
                                {productsList.map((p) => (
                                  <option key={p.product_id} value={p.product_id}>
                                    {p.product_name} ({p.product_id})
                                  </option>
                                ))}
                              </select>
                            </td>
                            <td>
                              <input
                                type="number"
                                className="form-control form-control-sm text-center"
                                min={1}
                                value={line.quantity}
                                onChange={(e) => handleLineChange(idx, 'quantity', e.target.value)}
                                required
                              />
                            </td>
                            <td>
                              <input
                                type="number"
                                step="0.01"
                                className="form-control form-control-sm text-end"
                                value={line.sales}
                                onChange={(e) => handleLineChange(idx, 'sales', e.target.value)}
                                required
                              />
                            </td>
                            <td>
                              <input
                                type="number"
                                step="0.01"
                                min={0}
                                max={1}
                                className="form-control form-control-sm text-end"
                                value={line.discount}
                                onChange={(e) => handleLineChange(idx, 'discount', e.target.value)}
                                required
                              />
                            </td>
                            <td>
                              <input
                                type="number"
                                step="0.01"
                                className="form-control form-control-sm text-end"
                                value={line.profit}
                                onChange={(e) => handleLineChange(idx, 'profit', e.target.value)}
                                required
                              />
                            </td>
                            <td className="text-center">
                              <button
                                type="button"
                                className="btn btn-link text-danger p-0"
                                onClick={() => handleRemoveLine(idx)}
                                disabled={lines.length <= 1}
                              >
                                ✕
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setShowCreateModal(false)}
                  >
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={isSubmitting}>
                    {isSubmitting ? 'Submitting Transaction...' : 'Commit Order to Database'}
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
