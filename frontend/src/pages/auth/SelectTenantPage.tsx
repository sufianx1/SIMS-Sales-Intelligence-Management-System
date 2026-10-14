import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { CompanyMembership } from '../../types/auth';

export const SelectTenantPage: React.FC = () => {
  const { user, setActiveCompany } = useAuth();
  const navigate = useNavigate();

  const handleSelect = (company: CompanyMembership) => {
    setActiveCompany(company);
    navigate('/dashboard');
  };

  return (
    <div className="min-vh-100 d-flex align-items-center justify-content-center bg-light px-3 py-5">
      <div className="card border-0 shadow-sm p-4 p-md-5" style={{ maxWidth: '520px', width: '100%', borderRadius: '12px' }}>
        <div className="text-center mb-4">
          <div className="fs-2 mb-1">🏢</div>
          <h4 className="fw-bold text-dark mb-1">Select Organization</h4>
          <p className="text-muted small">Choose the active company tenant for your session</p>
        </div>

        <div className="list-group gap-2">
          {user?.companies.map((comp) => (
            <button
              key={comp.company_id}
              onClick={() => handleSelect(comp)}
              className="list-group-item list-group-item-action d-flex justify-content-between align-items-center p-3 rounded border"
            >
              <div>
                <div className="fw-semibold text-dark">{comp.company_name}</div>
                <small className="text-muted">
                  Role: <strong>{comp.role_name}</strong>
                  {comp.store_name && ` • Store: ${comp.store_name}`}
                </small>
              </div>
              <span className="badge bg-primary rounded-pill">Select →</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
