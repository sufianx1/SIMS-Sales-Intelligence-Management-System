import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { productsApi } from '../../api';
import { Product, ProductDetail } from '../../types/product';

export const ProductsPage: React.FC = () => {
  const { activeCompany, hasPermission } = useAuth();

  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(25);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('All');

  const [selectedProduct, setSelectedProduct] = useState<ProductDetail | null>(null);

  // Create Product Modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSku, setNewSku] = useState('');
  const [newName, setNewName] = useState('');
  const [newCat, setNewCat] = useState('Technology');
  const [newSubCat, setNewSubCat] = useState('Accessories');
  const [createError, setCreateError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const resp = await productsApi.list({
        search: search.trim() || undefined,
        category: category !== 'All' ? category : undefined,
        page,
        limit,
      });
      setProducts(resp.items);
      setTotal(resp.total);
    } catch {
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeCompany) {
      fetchProducts();
    }
  }, [activeCompany, page, category]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  const handleViewProduct = async (id: string) => {
    try {
      const detail = await productsApi.getById(id);
      setSelectedProduct(detail);
    } catch {
      alert('Could not load product transaction records.');
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    setIsSubmitting(true);
    try {
      await productsApi.create({
        product_id: newSku.trim(),
        product_name: newName.trim(),
        category: newCat,
        sub_category: newSubCat,
      });
      setShowCreateModal(false);
      setNewSku('');
      setNewName('');
      setPage(1);
      fetchProducts();
    } catch (err: any) {
      setCreateError(err.response?.data?.detail || 'Failed to create product SKU.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Products Catalog</h3>
          <p className="text-muted small mb-0">
            Catalog SKUs, inventory revenue, and units sold for <strong>{activeCompany?.company_name}</strong>
          </p>
        </div>
        {hasPermission('CREATE_PRODUCT') && (
          <button
            onClick={() => {
              setNewSku(`SKU-${Date.now().toString().slice(-6)}`);
              setShowCreateModal(true);
            }}
            className="btn btn-primary btn-sm d-flex align-items-center gap-1"
          >
            <span>➕</span> New Product SKU
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
              placeholder="Search by product name or SKU..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

          <div className="col-6 col-md-3">
            <select
              className="form-select form-select-sm"
              value={category}
              onChange={(e) => {
                setCategory(e.target.value);
                setPage(1);
              }}
            >
              <option value="All">All Categories</option>
              <option value="Technology">Technology</option>
              <option value="Furniture">Furniture</option>
              <option value="Office Supplies">Office Supplies</option>
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
                <th>SKU</th>
                <th>Product Description</th>
                <th>Category</th>
                <th>Sub-Category</th>
                <th className="text-center">Units Sold</th>
                <th className="text-end">Total Revenue</th>
                <th className="text-end">Total Profit</th>
                <th className="text-center">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={8} className="text-center py-5">
                    <div className="spinner-border spinner-border-sm text-primary me-2" role="status" />
                    Loading product catalog...
                  </td>
                </tr>
              ) : products.length === 0 ? (
                <tr>
                  <td colSpan={8} className="text-center py-5 text-muted">
                    No products found matching criteria.
                  </td>
                </tr>
              ) : (
                products.map((p) => (
                  <tr key={p.product_id}>
                    <td className="fw-semibold text-primary">{p.product_id}</td>
                    <td className="fw-medium text-dark">{p.product_name}</td>
                    <td>
                      <span className="badge bg-light text-secondary border">
                        {p.category || 'General'}
                      </span>
                    </td>
                    <td className="small text-muted">{p.sub_category || '—'}</td>
                    <td className="text-center">{p.total_quantity.toLocaleString()}</td>
                    <td className="text-end fw-semibold">
                      ${p.total_sales.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className={`text-end fw-semibold ${p.total_profit >= 0 ? 'text-success' : 'text-danger'}`}>
                      ${p.total_profit.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="text-center">
                      <button
                        onClick={() => handleViewProduct(p.product_id)}
                        className="btn btn-outline-primary btn-sm py-0 px-2"
                      >
                        Details
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
            Showing {products.length} of {total.toLocaleString()} total SKUs
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

      {/* Product Details Modal */}
      {selectedProduct && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title fw-bold">SKU Performance: {selectedProduct.product.product_name}</h5>
                <button type="button" className="btn-close" onClick={() => setSelectedProduct(null)} />
              </div>
              <div className="modal-body">
                <div className="row g-2 mb-3 bg-light p-3 rounded small">
                  <div className="col-4">
                    <strong>SKU:</strong> {selectedProduct.product.product_id}
                  </div>
                  <div className="col-4">
                    <strong>Category:</strong> {selectedProduct.product.category}
                  </div>
                  <div className="col-4">
                    <strong>Sub-Category:</strong> {selectedProduct.product.sub_category}
                  </div>
                  <div className="col-4">
                    <strong>Lifetime Revenue:</strong> ${selectedProduct.product.total_sales.toFixed(2)}
                  </div>
                  <div className="col-4">
                    <strong>Units Sold:</strong> {selectedProduct.product.total_quantity}
                  </div>
                  <div className="col-4">
                    <strong>Total Profit:</strong> ${selectedProduct.product.total_profit.toFixed(2)}
                  </div>
                </div>

                <h6 className="fw-bold mb-2">Recent Order Transactions ({selectedProduct.recent_transactions.length})</h6>
                <div className="table-responsive" style={{ maxHeight: '350px' }}>
                  <table className="table table-sm table-bordered mb-0">
                    <thead className="table-light small">
                      <tr>
                        <th>Order ID</th>
                        <th>Order Date</th>
                        <th>Customer</th>
                        <th className="text-center">Qty</th>
                        <th className="text-end">Sales</th>
                        <th className="text-end">Profit</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedProduct.recent_transactions.map((t, idx) => (
                        <tr key={idx}>
                          <td className="small text-primary">{t.order_id}</td>
                          <td className="small">{t.order_date}</td>
                          <td className="small fw-medium">{t.customer_name}</td>
                          <td className="text-center small">{t.quantity}</td>
                          <td className="text-end small fw-semibold">${t.sales.toFixed(2)}</td>
                          <td className={`text-end small fw-semibold ${t.profit >= 0 ? 'text-success' : 'text-danger'}`}>
                            ${t.profit.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setSelectedProduct(null)}>
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Product Modal */}
      {showCreateModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleCreateSubmit}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Register New Catalog SKU</h5>
                  <button type="button" className="btn-close" onClick={() => setShowCreateModal(false)} />
                </div>
                <div className="modal-body">
                  {createError && <div className="alert alert-danger py-2 small mb-3">⚠️ {createError}</div>}
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Product SKU Code</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      value={newSku}
                      onChange={(e) => setNewSku(e.target.value)}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Product Name / Description</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      value={newName}
                      onChange={(e) => setNewName(e.target.value)}
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Category</label>
                    <select
                      className="form-select form-select-sm"
                      value={newCat}
                      onChange={(e) => setNewCat(e.target.value)}
                    >
                      <option value="Technology">Technology</option>
                      <option value="Furniture">Furniture</option>
                      <option value="Office Supplies">Office Supplies</option>
                    </select>
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Sub-Category</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      value={newSubCat}
                      onChange={(e) => setNewSubCat(e.target.value)}
                      placeholder="e.g. Phones, Chairs, Storage"
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowCreateModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={isSubmitting}>
                    {isSubmitting ? 'Registering...' : 'Register Product SKU'}
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
