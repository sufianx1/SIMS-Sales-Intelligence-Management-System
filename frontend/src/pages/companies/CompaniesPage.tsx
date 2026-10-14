import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { companiesApi } from '../../api';
import { Company } from '../../types/company';

export const CompaniesPage: React.FC = () => {
  const { user } = useAuth();

  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);

  // Create Modal
  const [showModal, setShowModal] = useState(false);
  const [newCompanyName, setNewCompanyName] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchCompanies = async () => {
    setLoading(true);
    try {
      const data = await companiesApi.list();
      setCompanies(data);
    } catch {
      setCompanies([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompanies();
  }, []);

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);
    try {
      await companiesApi.create({ company_name: newCompanyName.trim() });
      setShowModal(false);
      setNewCompanyName('');
      fetchCompanies();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to provision company.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">Platform Tenant Administration</h3>
          <p className="text-muted small mb-0">
            System-wide organization registry (Platform Administrator privileged area)
          </p>
        </div>
        {user?.is_system_admin && (
          <button onClick={() => setShowModal(true)} className="btn btn-primary btn-sm d-flex align-items-center gap-1">
            <span>➕</span> Provision New Tenant
          </button>
        )}
      </div>

      <div className="card-saas overflow-hidden">
        <div className="table-responsive">
          <table className="table table-saas mb-0">
            <thead>
              <tr>
                <th>Tenant ID</th>
                <th>Company Name</th>
                <th>Status</th>
                <th>Registration Date</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={4} className="text-center py-5">
                    <div className="spinner-border spinner-border-sm text-primary me-2" role="status" />
                    Loading tenants...
                  </td>
                </tr>
              ) : (
                companies.map((c) => (
                  <tr key={c.company_id}>
                    <td className="fw-semibold text-primary">#{c.company_id}</td>
                    <td className="fw-bold text-dark">{c.company_name}</td>
                    <td>
                      <span className={`badge ${c.is_active ? 'bg-success-subtle text-success' : 'bg-danger-subtle text-danger'}`}>
                        {c.is_active ? 'Active Tenant' : 'Suspended'}
                      </span>
                    </td>
                    <td className="text-muted small">
                      {c.created_at ? new Date(c.created_at).toLocaleDateString() : 'Baseline'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-dialog-centered">
            <div className="modal-content">
              <form onSubmit={handleCreateSubmit}>
                <div className="modal-header">
                  <h5 className="modal-title fw-bold">Provision New Tenant</h5>
                  <button type="button" className="btn-close" onClick={() => setShowModal(false)} />
                </div>
                <div className="modal-body">
                  {errorMsg && <div className="alert alert-danger py-2 small mb-3">⚠️ {errorMsg}</div>}
                  <div className="mb-3">
                    <label className="form-label small fw-semibold">Company / Tenant Name</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      value={newCompanyName}
                      onChange={(e) => setNewCompanyName(e.target.value)}
                      placeholder="e.g. Acme Retailers Inc."
                      required
                      autoFocus
                    />
                  </div>
                </div>
                <div className="modal-footer">
                  <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowModal(false)}>
                    Cancel
                  </button>
                  <button type="submit" className="btn btn-primary btn-sm" disabled={isSubmitting}>
                    {isSubmitting ? 'Provisioning...' : 'Provision Tenant'}
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
