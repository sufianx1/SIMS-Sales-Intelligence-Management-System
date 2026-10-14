import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

export const LoginPage: React.FC = () => {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  React.useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);

    try {
      await login({ email: email.trim(), password });
      navigate('/dashboard');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Authentication failed. Please verify your credentials.';
      setErrorMsg(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const setDemoAccount = (identifier: string) => {
    setEmail(identifier);
    setPassword('Demo12345!');
    setErrorMsg(null);
  };

  return (
    <div className="min-vh-100 d-flex align-items-center justify-content-center bg-light px-3 py-5">
      <div className="card border-0 shadow-sm p-4 p-md-5" style={{ maxWidth: '480px', width: '100%', borderRadius: '12px' }}>
        <div className="text-center mb-4">
          <div className="fs-1 mb-2">🚀</div>
          <h4 className="fw-bold text-dark mb-1">SIMS Platform</h4>
          <p className="text-muted small">Sales Intelligence & Multi-Tenant Management</p>
        </div>

        {errorMsg && (
          <div className="alert alert-danger py-2 px-3 small d-flex align-items-center mb-3" role="alert">
            <span className="me-2">⚠️</span>
            <div>{errorMsg}</div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="mb-3">
            <label className="form-label small fw-semibold text-secondary">Username or Work Email</label>
            <input
              type="text"
              className="form-control"
              placeholder="e.g. superstore.admin or admin@superstore.sims.local"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoFocus
            />
          </div>

          <div className="mb-4">
            <div className="d-flex justify-content-between align-items-center mb-1">
              <label className="form-label small fw-semibold text-secondary mb-0">Password</label>
              <button
                type="button"
                className="btn btn-link btn-sm text-decoration-none p-0 text-muted"
                style={{ fontSize: '0.8rem' }}
                onClick={() => setShowPassword(!showPassword)}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>
            <input
              type={showPassword ? 'text' : 'password'}
              className="form-control"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary w-100 py-2 fw-medium d-flex justify-content-center align-items-center gap-2"
            disabled={isSubmitting}
          >
            {isSubmitting && <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true" />}
            {isSubmitting ? 'Authenticating...' : 'Sign In to SIMS'}
          </button>
        </form>

        {/* Demo Credentials Quick-Select (Section 18 Specification) */}
        <div className="mt-4 pt-3 border-top">
          <div className="text-muted small fw-semibold mb-2 text-center" style={{ fontSize: '0.75rem' }}>
            DEMO TEST ACCOUNTS (PASSWORD: <code>Demo12345!</code>)
          </div>
          <div className="d-flex flex-wrap gap-1 justify-content-center mb-2">
            <button
              type="button"
              className="btn btn-outline-dark btn-sm py-1 px-2"
              style={{ fontSize: '0.72rem' }}
              onClick={() => setDemoAccount('superadmin')}
            >
              👑 Platform Admin
            </button>
          </div>
          <div className="d-flex flex-wrap gap-1 justify-content-center">
            <button
              type="button"
              className="btn btn-outline-primary btn-sm py-1 px-2"
              style={{ fontSize: '0.72rem' }}
              onClick={() => setDemoAccount('superstore.admin')}
            >
              🏬 Superstore Admin
            </button>
            <button
              type="button"
              className="btn btn-outline-primary btn-sm py-1 px-2"
              style={{ fontSize: '0.72rem' }}
              onClick={() => setDemoAccount('superstore.employee')}
            >
              👤 Superstore Emp
            </button>
            <button
              type="button"
              className="btn btn-outline-danger btn-sm py-1 px-2"
              style={{ fontSize: '0.72rem' }}
              onClick={() => setDemoAccount('nike.admin')}
            >
              👟 Nike Admin
            </button>
            <button
              type="button"
              className="btn btn-outline-danger btn-sm py-1 px-2"
              style={{ fontSize: '0.72rem' }}
              onClick={() => setDemoAccount('nike.employee')}
            >
              👤 Nike Emp
            </button>
            <button
              type="button"
              className="btn btn-outline-success btn-sm py-1 px-2"
              style={{ fontSize: '0.72rem' }}
              onClick={() => setDemoAccount('puma.admin')}
            >
              🐆 Puma Admin
            </button>
            <button
              type="button"
              className="btn btn-outline-success btn-sm py-1 px-2"
              style={{ fontSize: '0.72rem' }}
              onClick={() => setDemoAccount('puma.employee')}
            >
              👤 Puma Emp
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
