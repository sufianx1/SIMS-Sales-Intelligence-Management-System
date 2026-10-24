import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { inventoryApi, storesApi, productsApi } from '../../api';
import { InventoryItem, InventoryMovement, InventoryAlert, RebalanceRecommendation } from '../../types/inventory';
import { Store } from '../../types/company';

export const InventoryPage: React.FC = () => {
  const { activeCompany, hasPermission } = useAuth();

  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [movements, setMovements] = useState<InventoryMovement[]>([]);
  const [alerts, setAlerts] = useState<InventoryAlert[]>([]);
  const [recommendations, setRecommendations] = useState<RebalanceRecommendation[]>([]);
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStore, setSelectedStore] = useState<string>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'stock' | 'movements' | 'alerts' | 'recommendations'>('stock');
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Modals state
  const [showAdjustModal, setShowAdjustModal] = useState<boolean>(false);
  const [showReceiveModal, setShowReceiveModal] = useState<boolean>(false);
  const [showTransferModal, setShowTransferModal] = useState<boolean>(false);

  // Form states
  const [formStoreId, setFormStoreId] = useState<number>(0);
  const [formProductId, setFormProductId] = useState<string>('');
  const [formQuantity, setFormQuantity] = useState<number>(1);
  const [formReason, setFormReason] = useState<string>('');
  const [formToStoreId, setFormToStoreId] = useState<number>(0);

  const fetchStores = async () => {
    try {
      const s = await storesApi.list();
      setStores(s);
      if (s.length > 0 && !formStoreId) {
        setFormStoreId(s[0].store_id);
        if (s.length > 1) {
          setFormToStoreId(s[1].store_id);
        }
      }
    } catch (err: any) {
      console.error('Failed to load stores', err);
    }
  };

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const storeIdNum = selectedStore === 'all' ? undefined : parseInt(selectedStore, 10);
      const [inv, mov, alt, recs] = await Promise.all([
        inventoryApi.list({
          store_id: storeIdNum,
          category: categoryFilter || undefined,
          search: searchQuery || undefined,
        }),
        inventoryApi.listMovements({ store_id: storeIdNum, limit: 50 }),
        inventoryApi.getAlerts({ store_id: storeIdNum }),
        inventoryApi.getRebalanceRecommendations({ store_id: storeIdNum }),
      ]);
      setInventory(inv);
      setMovements(mov);
      setAlerts(alt);
      setRecommendations(recs);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch inventory data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStores();
  }, [activeCompany]);

  useEffect(() => {
    loadData();
  }, [activeCompany, selectedStore, categoryFilter, searchQuery]);

  const handleAdjustSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    try {
      await inventoryApi.adjust({
        store_id: formStoreId,
        product_id: formProductId,
        quantity: formQuantity,
        reason: formReason,
      });
      setActionSuccess('Stock adjustment successfully recorded in audit log.');
      setShowAdjustModal(false);
      resetForms();
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to adjust stock.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReceiveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    try {
      await inventoryApi.receive({
        store_id: formStoreId,
        product_id: formProductId,
        quantity: Math.abs(formQuantity),
        reason: formReason,
      });
      setActionSuccess('Incoming purchase receipt processed and stock incremented.');
      setShowReceiveModal(false);
      resetForms();
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to receive stock.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTransferSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;
    if (formStoreId === formToStoreId) {
      setError('Origin and destination stores must be different.');
      return;
    }
    setSubmitting(true);
    try {
      await inventoryApi.transfer({
        from_store_id: formStoreId,
        to_store_id: formToStoreId,
        product_id: formProductId,
        quantity: Math.abs(formQuantity),
        reason: formReason,
      });
      setActionSuccess('Inter-store stock transfer executed with bilateral movement logs.');
      setShowTransferModal(false);
      resetForms();
      loadData();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to transfer stock.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReviewRecommendation = (rec: RebalanceRecommendation) => {
    setFormStoreId(rec.from_store_id);
    setFormToStoreId(rec.to_store_id);
    setFormProductId(rec.product_id);
    setFormQuantity(rec.recommended_transfer_qty);
    setFormReason(`Inter-store rebalancing: Transfer ${rec.recommended_transfer_qty} units from ${rec.from_store_name} to alleviate shortage at ${rec.to_store_name}`);
    setShowTransferModal(true);
  };

  const resetForms = () => {
    setFormQuantity(1);
    setFormReason('');
    setFormProductId('');
  };

  const totalValuation = inventory.reduce((sum, item) => sum + item.valuation, 0);
  const totalUnits = inventory.reduce((sum, item) => sum + item.quantity_on_hand, 0);
  const lowStockCount = inventory.filter((item) => item.status === 'LOW_STOCK').length;
  const outOfStockCount = inventory.filter((item) => item.status === 'OUT_OF_STOCK').length;

  const categories = Array.from(new Set(inventory.map((i) => i.category))).filter(Boolean);

  return (
    <div className="container-fluid p-4">
      {/* Page Header */}
      <div className="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
        <div>
          <h2 className="h4 fw-bold text-dark mb-1">📦 Multi-Store Inventory Management</h2>
          <p className="text-muted small mb-0">
            Real-time multi-location stock levels, traceable inter-store transfers, and valuation for{' '}
            <strong>{activeCompany?.company_name}</strong>.
          </p>
        </div>

        <div className="d-flex flex-wrap gap-2">
          {hasPermission('inventory_adjust') && (
            <>
              <button
                className="btn btn-primary btn-sm d-flex align-items-center gap-1"
                onClick={() => {
                  if (inventory.length > 0 && !formProductId) setFormProductId(inventory[0].product_id);
                  setShowReceiveModal(true);
                }}
              >
                <span>➕</span> Receive Stock
              </button>
              <button
                className="btn btn-outline-secondary btn-sm d-flex align-items-center gap-1"
                onClick={() => {
                  if (inventory.length > 0 && !formProductId) setFormProductId(inventory[0].product_id);
                  setShowAdjustModal(true);
                }}
              >
                <span>✏️</span> Adjust Stock
              </button>
            </>
          )}

          {hasPermission('inventory_transfer') && stores.length > 1 && (
            <button
              className="btn btn-outline-info btn-sm d-flex align-items-center gap-1"
              onClick={() => {
                if (inventory.length > 0 && !formProductId) setFormProductId(inventory[0].product_id);
                setShowTransferModal(true);
              }}
            >
              <span>🔄</span> Inter-Store Transfer
            </button>
          )}

          <a
            href={inventoryApi.exportCsvUrl(selectedStore === 'all' ? undefined : parseInt(selectedStore, 10))}
            className="btn btn-outline-success btn-sm d-flex align-items-center gap-1"
            download
          >
            <span>📥</span> Export CSV
          </a>
        </div>
      </div>

      {actionSuccess && (
        <div className="alert alert-success alert-dismissible fade show" role="alert">
          {actionSuccess}
          <button type="button" className="btn-close" onClick={() => setActionSuccess(null)}></button>
        </div>
      )}

      {error && (
        <div className="alert alert-danger alert-dismissible fade show" role="alert">
          {error}
          <button type="button" className="btn-close" onClick={() => setError(null)}></button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="row g-3 mb-4">
        <div className="col-12 col-sm-6 col-xl-3">
          <div className="card shadow-sm border-0 border-start border-primary border-4 h-100">
            <div className="card-body">
              <span className="text-muted small text-uppercase fw-semibold">Total Stock Units</span>
              <h3 className="fw-bold mt-1 mb-0">{totalUnits.toLocaleString()}</h3>
              <small className="text-muted">Across {selectedStore === 'all' ? 'All Stores' : 'Filtered Store'}</small>
            </div>
          </div>
        </div>
        <div className="col-12 col-sm-6 col-xl-3">
          <div className="card shadow-sm border-0 border-start border-success border-4 h-100">
            <div className="card-body">
              <span className="text-muted small text-uppercase fw-semibold">Inventory Valuation</span>
              <h3 className="fw-bold mt-1 mb-0 text-success">${totalValuation.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</h3>
              <small className="text-muted">Calculated on unit cost basis</small>
            </div>
          </div>
        </div>
        <div className="col-12 col-sm-6 col-xl-3">
          <div className="card shadow-sm border-0 border-start border-warning border-4 h-100">
            <div className="card-body">
              <span className="text-muted small text-uppercase fw-semibold">Low-Stock Alerts</span>
              <h3 className="fw-bold mt-1 mb-0 text-warning">{lowStockCount}</h3>
              <small className="text-muted">At or below reorder threshold</small>
            </div>
          </div>
        </div>
        <div className="col-12 col-sm-6 col-xl-3">
          <div className="card shadow-sm border-0 border-start border-danger border-4 h-100">
            <div className="card-body">
              <span className="text-muted small text-uppercase fw-semibold">Out of Stock</span>
              <h3 className="fw-bold mt-1 mb-0 text-danger">{outOfStockCount}</h3>
              <small className="text-muted">Zero units remaining on hand</small>
            </div>
          </div>
        </div>
      </div>

      {/* Rebalance Recommendation Banner */}
      {recommendations.length > 0 && hasPermission('inventory_transfer') && (
        <div className="alert alert-primary border-primary-subtle shadow-sm d-flex flex-wrap align-items-center justify-content-between mb-4">
          <div className="d-flex align-items-center mb-2 mb-md-0">
            <span className="fs-3 me-3">⚡</span>
            <div>
              <strong className="d-block text-dark">
                Inter-Store Rebalancing Recommendations Available ({recommendations.length})
              </strong>
              <small className="text-muted">
                SIMS detected deterministic opportunities to rebalance stock from branches with surplus to branches experiencing shortage.
              </small>
            </div>
          </div>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => setActiveTab('recommendations')}
          >
            Review Recommendations ({recommendations.length}) &rarr;
          </button>
        </div>
      )}

      {/* Filter Toolbar */}
      <div className="card shadow-sm border-0 mb-4">
        <div className="card-body p-3">
          <div className="row g-2 align-items-center">
            <div className="col-12 col-md-4">
              <label className="form-label small text-muted mb-1">Store / Location</label>
              <select
                className="form-select form-select-sm"
                value={selectedStore}
                onChange={(e) => setSelectedStore(e.target.value)}
                disabled={Boolean(activeCompany?.store_id)}
              >
                <option value="all">🏢 All Stores (Consolidated)</option>
                {stores.map((s) => (
                  <option key={s.store_id} value={s.store_id.toString()}>
                    📍 {s.store_name} ({s.location || s.city || 'Store'})
                  </option>
                ))}
              </select>
            </div>

            <div className="col-12 col-md-3">
              <label className="form-label small text-muted mb-1">Category</label>
              <select
                className="form-select form-select-sm"
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
              >
                <option value="">All Categories</option>
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div className="col-12 col-md-5">
              <label className="form-label small text-muted mb-1">Search Products or SKU</label>
              <div className="input-group input-group-sm">
                <input
                  type="text"
                  className="form-control"
                  placeholder="Search by product name, SKU, or ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
                {searchQuery && (
                  <button className="btn btn-outline-secondary" onClick={() => setSearchQuery('')}>
                    Clear
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <ul className="nav nav-tabs mb-3">
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === 'stock' ? 'active fw-bold' : ''}`}
            onClick={() => setActiveTab('stock')}
          >
            📊 Current Stock Levels ({inventory.length})
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === 'movements' ? 'active fw-bold' : ''}`}
            onClick={() => setActiveTab('movements')}
          >
            🔄 Audit Movement Logs ({movements.length})
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === 'alerts' ? 'active fw-bold text-danger' : ''}`}
            onClick={() => setActiveTab('alerts')}
          >
            ⚠️ Low & Out of Stock Alerts ({alerts.length})
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === 'recommendations' ? 'active fw-bold text-primary' : ''}`}
            onClick={() => setActiveTab('recommendations')}
          >
            ⚡ Rebalancing Proposals ({recommendations.length})
          </button>
        </li>
      </ul>

      {/* Tab 1: Current Stock Levels */}
      {activeTab === 'stock' && (
        <div className="card shadow-sm border-0">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Store</th>
                  <th>Product</th>
                  <th>SKU</th>
                  <th>Category</th>
                  <th className="text-end">On Hand</th>
                  <th className="text-end">Min Threshold</th>
                  <th className="text-end">Unit Cost</th>
                  <th className="text-end">Unit Price</th>
                  <th className="text-end">Valuation</th>
                  <th className="text-center">Status</th>
                  <th className="text-end">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={11} className="text-center py-4 text-muted">
                      <div className="spinner-border spinner-border-sm me-2 text-primary" />
                      Loading inventory records...
                    </td>
                  </tr>
                ) : inventory.length === 0 ? (
                  <tr>
                    <td colSpan={11} className="text-center py-4 text-muted">
                      No inventory records found matching your filters.
                    </td>
                  </tr>
                ) : (
                  inventory.map((item) => (
                    <tr key={item.inventory_id}>
                      <td className="fw-medium">{item.store_name}</td>
                      <td>
                        <div className="fw-semibold">{item.product_name}</div>
                        <small className="text-muted">{item.product_id}</small>
                      </td>
                      <td><code>{item.sku}</code></td>
                      <td><span className="badge bg-light text-dark border">{item.category}</span></td>
                      <td className="text-end fw-bold">{item.quantity_on_hand}</td>
                      <td className="text-end text-muted">{item.min_threshold}</td>
                      <td className="text-end">${item.unit_cost.toFixed(2)}</td>
                      <td className="text-end">${item.unit_price.toFixed(2)}</td>
                      <td className="text-end fw-semibold text-success">${item.valuation.toFixed(2)}</td>
                      <td className="text-center">
                        {item.status === 'IN_STOCK' && <span className="badge bg-success-subtle text-success border border-success-subtle">In Stock</span>}
                        {item.status === 'LOW_STOCK' && <span className="badge bg-warning-subtle text-warning border border-warning-subtle">Low Stock</span>}
                        {item.status === 'OUT_OF_STOCK' && <span className="badge bg-danger-subtle text-danger border border-danger-subtle">Out of Stock</span>}
                      </td>
                      <td className="text-end">
                        {hasPermission('inventory_adjust') && (
                          <button
                            className="btn btn-outline-secondary btn-sm py-0 px-2"
                            onClick={() => {
                              setFormStoreId(item.store_id);
                              setFormProductId(item.product_id);
                              setShowAdjustModal(true);
                            }}
                          >
                            Adjust
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Movement Logs */}
      {activeTab === 'movements' && (
        <div className="card shadow-sm border-0">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Movement ID</th>
                  <th>Timestamp</th>
                  <th>Type</th>
                  <th>Product</th>
                  <th>From Store</th>
                  <th>To Store</th>
                  <th className="text-end">Quantity</th>
                  <th>Reason / Justification</th>
                </tr>
              </thead>
              <tbody>
                {movements.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-4 text-muted">
                      No inventory movements recorded yet.
                    </td>
                  </tr>
                ) : (
                  movements.map((m) => (
                    <tr key={m.movement_id}>
                      <td><code>{m.movement_id}</code></td>
                      <td className="small text-muted">{new Date(m.timestamp).toLocaleString()}</td>
                      <td>
                        {m.movement_type === 'RECEIPT' && <span className="badge bg-success">RECEIPT</span>}
                        {m.movement_type === 'TRANSFER' && <span className="badge bg-info text-dark">TRANSFER</span>}
                        {m.movement_type === 'ADJUSTMENT' && <span className="badge bg-secondary">ADJUSTMENT</span>}
                      </td>
                      <td>
                        <div className="fw-semibold">{m.product_name}</div>
                        <small className="text-muted">{m.product_id}</small>
                      </td>
                      <td>{m.from_store_name || '—'}</td>
                      <td>{m.to_store_name || '—'}</td>
                      <td className={`text-end fw-bold ${m.quantity >= 0 ? 'text-success' : 'text-danger'}`}>
                        {m.quantity > 0 ? `+${m.quantity}` : m.quantity}
                      </td>
                      <td>{m.reason}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Alerts */}
      {activeTab === 'alerts' && (
        <div className="card shadow-sm border-0">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Product Name</th>
                  <th>Store</th>
                  <th className="text-end">Current Stock</th>
                  <th className="text-end">Min Threshold</th>
                  <th className="text-center">Severity</th>
                  <th className="text-end">Action</th>
                </tr>
              </thead>
              <tbody>
                {alerts.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-4 text-success fw-medium">
                      ✅ All inventory items are adequately stocked above minimum thresholds!
                    </td>
                  </tr>
                ) : (
                  alerts.map((alt) => (
                    <tr key={`${alt.store_id}-${alt.product_id}`}>
                      <td>
                        <div className="fw-bold">{alt.product_name}</div>
                        <small className="text-muted">{alt.product_id}</small>
                      </td>
                      <td>{alt.store_name}</td>
                      <td className="text-end fw-bold text-danger">{alt.quantity_on_hand}</td>
                      <td className="text-end text-muted">{alt.min_threshold}</td>
                      <td className="text-center">
                        {(alt.severity === 'CRITICAL' || alt.status === 'OUT_OF_STOCK' || alt.quantity_on_hand === 0) ? (
                          <span className="badge bg-danger">Critical: Out of Stock</span>
                        ) : (
                          <span className="badge bg-warning text-dark">Warning: Low Stock</span>
                        )}
                      </td>
                      <td className="text-end">
                        <div className="btn-group btn-group-sm">
                          {(() => {
                            const rec = recommendations.find(
                              (r) => r.product_id === alt.product_id && r.to_store_id === alt.store_id
                            );
                            if (rec && hasPermission('inventory_transfer')) {
                              return (
                                <button
                                  className="btn btn-sm btn-outline-primary py-0 px-2"
                                  title={`Rebalance ${rec.recommended_transfer_qty} units from ${rec.from_store_name}`}
                                  onClick={() => handleReviewRecommendation(rec)}
                                >
                                  ⚡ Rebalance ({rec.recommended_transfer_qty})
                                </button>
                              );
                            }
                            return null;
                          })()}
                          <button
                            className="btn btn-sm btn-primary py-0 px-2"
                            onClick={() => {
                              setFormStoreId(alt.store_id);
                              setFormProductId(alt.product_id);
                              setShowReceiveModal(true);
                            }}
                          >
                            Restock
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: Rebalancing Proposals */}
      {activeTab === 'recommendations' && (
        <div className="space-y-4">
          <div className="card shadow-sm border-0 mb-3 bg-light">
            <div className="card-body p-3">
              <h6 className="fw-bold mb-1 text-dark">🧠 Deterministic Inventory Rebalancing Engine</h6>
              <p className="text-muted small mb-0">
                Identifies branches facing imminent stockout or low-stock deficits alongside branches within the same
                company that hold verified surplus beyond their own safety thresholds. All proposals require human review
                and preserve a complete bilateral movement audit trail upon execution.
              </p>
            </div>
          </div>

          {recommendations.length === 0 ? (
            <div className="card shadow-sm border-0 p-5 text-center">
              <span className="fs-1 text-success mb-2">✅</span>
              <h5 className="fw-bold text-success mb-1">No Inter-Store Imbalances Detected</h5>
              <p className="text-muted small mb-0">
                All inventory across authorized stores is currently balanced above safety stock thresholds,
                or no surplus branch is currently available to transfer stock without violating safety limits.
              </p>
            </div>
          ) : (
            recommendations.map((rec) => (
              <div key={rec.recommendation_id} className="card shadow-sm border-0 mb-3 border-start border-primary border-4">
                <div className="card-body p-4">
                  <div className="d-flex flex-wrap justify-content-between align-items-center mb-3 gap-2">
                    <div>
                      <span className="badge bg-primary-subtle text-primary border border-primary-subtle me-2">
                        Proposal #{rec.recommendation_id}
                      </span>
                      <span className="badge bg-secondary-subtle text-secondary border">
                        {rec.category}
                      </span>
                      <h5 className="fw-bold text-dark mt-2 mb-0">{rec.summary}</h5>
                      <small className="text-muted">Product: <strong>{rec.product_name}</strong> (SKU: <code>{rec.sku}</code>)</small>
                    </div>

                    {hasPermission('inventory_transfer') && (
                      <button
                        className="btn btn-primary px-3 py-2 fw-semibold"
                        onClick={() => handleReviewRecommendation(rec)}
                      >
                        ⚡ Review & Execute Transfer ({rec.recommended_transfer_qty} units)
                      </button>
                    )}
                  </div>

                  {/* Metrics Comparison Row */}
                  <div className="row g-3 p-3 bg-light rounded-3 mb-3">
                    <div className="col-12 col-md-5">
                      <div className="p-2 border rounded bg-white">
                        <span className="text-danger fw-bold small text-uppercase d-block mb-1">
                          📍 Recipient Store (Shortage)
                        </span>
                        <div className="fw-bold text-dark">{rec.to_store_name}</div>
                        <div className="small text-muted mt-1">
                          Current on hand: <strong className="text-danger">{rec.to_current_qty}</strong> / Min safety: {rec.to_min_threshold}
                        </div>
                        <div className="small text-danger fw-semibold">
                          Deficit: {rec.deficit_qty} unit(s) below safety stock
                        </div>
                        <div className="small text-success mt-1 fw-bold">
                          &rarr; Projected after transfer: {rec.projected_to_qty} units (Meets safety threshold)
                        </div>
                      </div>
                    </div>

                    <div className="col-12 col-md-2 d-flex flex-column align-items-center justify-content-center text-center">
                      <span className="badge bg-primary fs-6 px-3 py-2 mb-1">
                        &rarr; {rec.recommended_transfer_qty} Units &rarr;
                      </span>
                      <small className="text-muted">Proposed Rebalance</small>
                    </div>

                    <div className="col-12 col-md-5">
                      <div className="p-2 border rounded bg-white">
                        <span className="text-success fw-bold small text-uppercase d-block mb-1">
                          🏢 Donor Store (Surplus)
                        </span>
                        <div className="fw-bold text-dark">{rec.from_store_name}</div>
                        <div className="small text-muted mt-1">
                          Current on hand: <strong className="text-dark">{rec.from_current_qty}</strong> / Min safety: {rec.from_min_threshold}
                        </div>
                        <div className="small text-success fw-semibold">
                          Available surplus: {rec.available_surplus_qty} unit(s) above safety stock
                        </div>
                        <div className="small text-muted mt-1">
                          &rarr; Projected after transfer: {rec.projected_from_qty} units (Safely above {rec.from_min_threshold})
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Explainability Accordion Details */}
                  <div className="small text-muted">
                    <div className="mb-1">
                      <strong className="text-dark">Operational Context:</strong> {rec.explanation}
                    </div>
                    <div className="mb-1">
                      <strong className="text-dark">Business Impact:</strong> {rec.why_it_matters}
                    </div>
                    <div className="mb-1">
                      <strong className="text-dark">Deterministic Formula:</strong> <code>{rec.supporting_calculation}</code>
                    </div>
                    <div>
                      <strong className="text-secondary">Audit Note:</strong> {rec.limitations}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* MODAL: Adjust Stock */}
      {showAdjustModal && (
        <div className="modal show d-block" tabIndex={-1} style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <form onSubmit={handleAdjustSubmit}>
                <div className="modal-header">
                  <h5 className="modal-title">✏️ Adjust Inventory Stock</h5>
                  <button type="button" className="btn-close" onClick={() => setShowAdjustModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label small fw-bold">Store</label>
                    <select
                      className="form-select"
                      value={formStoreId}
                      onChange={(e) => setFormStoreId(parseInt(e.target.value, 10))}
                      required
                    >
                      {stores.map((s) => (
                        <option key={s.store_id} value={s.store_id}>
                          {s.store_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-bold">Product</label>
                    <select
                      className="form-select"
                      value={formProductId}
                      onChange={(e) => setFormProductId(e.target.value)}
                      required
                    >
                      {inventory.map((i) => (
                        <option key={i.product_id} value={i.product_id}>
                          {i.product_name} ({i.product_id})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-bold">Quantity Change (+ or -)</label>
                    <input
                      type="number"
                      className="form-control"
                      value={formQuantity}
                      onChange={(e) => setFormQuantity(parseInt(e.target.value, 10) || 0)}
                      required
                    />
                    <small className="text-muted">Use positive for found stock, negative for damage/loss.</small>
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-bold">Justification Reason</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. Annual physical count variance, damaged display unit"
                      value={formReason}
                      onChange={(e) => setFormReason(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowAdjustModal(false)} disabled={submitting}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                        Recording...
                      </>
                    ) : (
                      'Record Adjustment'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Receive Stock */}
      {showReceiveModal && (
        <div className="modal show d-block" tabIndex={-1} style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <form onSubmit={handleReceiveSubmit}>
                <div className="modal-header">
                  <h5 className="modal-title">➕ Receive Supplier Stock</h5>
                  <button type="button" className="btn-close" onClick={() => setShowReceiveModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label small fw-bold">Receiving Store</label>
                    <select
                      className="form-select"
                      value={formStoreId}
                      onChange={(e) => setFormStoreId(parseInt(e.target.value, 10))}
                      required
                    >
                      {stores.map((s) => (
                        <option key={s.store_id} value={s.store_id}>
                          {s.store_name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-bold">Product</label>
                    <select
                      className="form-select"
                      value={formProductId}
                      onChange={(e) => setFormProductId(e.target.value)}
                      required
                    >
                      {inventory.map((i) => (
                        <option key={i.product_id} value={i.product_id}>
                          {i.product_name} ({i.product_id})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-bold">Quantity Received</label>
                    <input
                      type="number"
                      className="form-control"
                      min={1}
                      value={formQuantity}
                      onChange={(e) => setFormQuantity(parseInt(e.target.value, 10) || 1)}
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-bold">Supplier PO / Shipment Details</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. PO-9842 Supplier Delivery"
                      value={formReason}
                      onChange={(e) => setFormReason(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowReceiveModal(false)} disabled={submitting}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-success" disabled={submitting}>
                    {submitting ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                        Receiving...
                      </>
                    ) : (
                      'Receive Stock'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* MODAL: Inter-Store Transfer */}
      {showTransferModal && (
        <div className="modal show d-block" tabIndex={-1} style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <form onSubmit={handleTransferSubmit}>
                <div className="modal-header">
                  <h5 className="modal-title">🔄 Inter-Store Inventory Transfer</h5>
                  <button type="button" className="btn-close" onClick={() => setShowTransferModal(false)}></button>
                </div>
                <div className="modal-body">
                  <div className="row g-2 mb-3">
                    <div className="col-6">
                      <label className="form-label small fw-bold">Origin Store (From)</label>
                      <select
                        className="form-select"
                        value={formStoreId}
                        onChange={(e) => setFormStoreId(parseInt(e.target.value, 10))}
                        required
                      >
                        {stores.map((s) => (
                          <option key={s.store_id} value={s.store_id}>
                            {s.store_name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div className="col-6">
                      <label className="form-label small fw-bold">Destination Store (To)</label>
                      <select
                        className="form-select"
                        value={formToStoreId}
                        onChange={(e) => setFormToStoreId(parseInt(e.target.value, 10))}
                        required
                      >
                        {stores.map((s) => (
                          <option key={s.store_id} value={s.store_id}>
                            {s.store_name}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-bold">Product</label>
                    <select
                      className="form-select"
                      value={formProductId}
                      onChange={(e) => setFormProductId(e.target.value)}
                      required
                    >
                      {inventory.map((i) => (
                        <option key={i.product_id} value={i.product_id}>
                          {i.product_name} ({i.product_id})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-bold">Units to Transfer</label>
                    <input
                      type="number"
                      className="form-control"
                      min={1}
                      value={formQuantity}
                      onChange={(e) => setFormQuantity(parseInt(e.target.value, 10) || 1)}
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label className="form-label small fw-bold">Transfer Requisition Reason</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="e.g. Stock rebalance for weekend promotional demand"
                      value={formReason}
                      onChange={(e) => setFormReason(e.target.value)}
                      required
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary" onClick={() => setShowTransferModal(false)} disabled={submitting}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-info text-dark fw-semibold" disabled={submitting}>
                    {submitting ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true" />
                        Executing Transfer...
                      </>
                    ) : (
                      'Execute Transfer'
                    )}
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
