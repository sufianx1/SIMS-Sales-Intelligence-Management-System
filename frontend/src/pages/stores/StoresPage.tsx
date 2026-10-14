import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { storesApi } from '../../api';
import { Store } from '../../types/company';

export const StoresPage: React.FC = () => {
  const { activeCompany, hasPermission } = useAuth();

  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);

  // Create Modal
  const [showModal, setShowModal] = useState(false);
  const [newStoreName, setNewStoreName] = useState('');
  const [newLocation, setNewLocation] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchStores = async () => {
    setLoading(true);
    try {
      const data = await storesApi.list();
      setStores(data);
    } catch {
      setStores([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (activeCompany) {
      fetchStores();
    }
  }, [activeCompany]);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);
    try {
      await storesApi.create({
        store_name: newStoreName.trim(),
        location: newLocation.trim() || undefined,
      });
      setShowModal(false);
      setNewStoreName('');
      setNewLocation('');
      fetchStores();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to create store.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Company Stores & Outlets</h3>
          <p className="text-muted small mb-0">
            Physical branches and retail fulfillment points for <strong>{activeCompany?.company_name}</strong>
          </p>
        </div>
        {hasPermission('MANAGE_STORES') && (
          <button onClick={() => setShowModal(true)} className="btn btn-primary btn-sm d-flex align-items-center gap-1">
            <span>➕</span> Add New Store
          </button>
        )}
      </div>

      <div className="row g-3">
        {loading ? (
          <div className="col-12 text-center py-5">
            <div className="spinner-border spinner-border-sm text-primary me-2" role="status" />
            Loading stores...
          </div>
        ) : stores.length === 0 ? (
          <div className="col-12">
            <div className="card-saas p-5 text-center text-muted">No stores registered for this company.</div>
          </div>
        ) : (
          stores.map((s) => (
            <div key={s.store_id} className="col-12 col-md-6 col-lg-4">
              <div className="card-saas p-4 h-100">
                <div className="d-flex justify-content-between align-items-start mb-2">
                  <h5 className="fw-bold mb-0 text-dark">{s.store_name}</h5>
                  <span className={`badge ${s.is_active ? 'bg-success-subtle text-success' : 'bg-danger-subtle text-danger'}`}>
                    {s.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="text-muted small mb-3">Store ID: #{s.store_id}</div>
                <div className="small">
                  <strong>Location:</strong> {s.location || 'Headquarters / Main Outlet'}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {showModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleCreateSubmit}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Add Company Store</h5>
                  <button type="button" className="btn-close" onClick={() => setShowModal(false)} />
                </div>
                <div className="modal-body">
                  {errorMsg && <div className="alert alert-danger py-2 small mb-3">⚠️ {errorMsg}</div>}
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Store / Outlet Name</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      value={newStoreName}
                      onChange={(e) => setNewStoreName(e.target.value)}
                      placeholder="e.g. Downtown Flagship Store"
                      required
                    />
                  </div>
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Physical Location / Address</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      value={newLocation}
                      onChange={(e) => setNewLocation(e.target.value)}
                      placeholder="e.g. 500 Market St, San Francisco, CA"
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={isSubmitting}>
                    {isSubmitting ? 'Adding...' : 'Add Store'}
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
