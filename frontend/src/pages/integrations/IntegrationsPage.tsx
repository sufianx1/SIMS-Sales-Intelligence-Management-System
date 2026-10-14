import React, { useEffect, useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { integrationsApi } from '../../api';
import { Integration, SyncExecutionResult, SyncLogItem } from '../../types/integrations';

export const IntegrationsPage: React.FC = () => {
  const { activeCompany, hasPermission } = useAuth();

  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [logs, setLogs] = useState<SyncLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [syncingId, setSyncingId] = useState<string | null>(null);
  const [lastSyncResult, setLastSyncResult] = useState<SyncExecutionResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadIntegrations = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await integrationsApi.list();
      setIntegrations(data);
      if (data.length > 0 && !selectedIntegration) {
        setSelectedIntegration(data[0]);
        loadLogs(data[0].integration_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch integrations.');
    } finally {
      setLoading(false);
    }
  };

  const loadLogs = async (integrationId: string) => {
    try {
      const logData = await integrationsApi.getLogs(integrationId);
      setLogs(logData);
    } catch (err: any) {
      console.error('Failed to load logs', err);
    }
  };

  useEffect(() => {
    loadIntegrations();
  }, [activeCompany]);

  const handleToggle = async (integration: Integration) => {
    try {
      const updated = await integrationsApi.toggle(integration.integration_id, !integration.is_active);
      setIntegrations((prev) =>
        prev.map((i) => (i.integration_id === updated.integration_id ? updated : i))
      );
      if (selectedIntegration?.integration_id === updated.integration_id) {
        setSelectedIntegration(updated);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to toggle integration status.');
    }
  };

  const handleTriggerSync = async (integrationId: string) => {
    setSyncingId(integrationId);
    setError(null);
    setLastSyncResult(null);
    try {
      const res = await integrationsApi.triggerSync(integrationId);
      setLastSyncResult(res);
      // Reload logs and integration state
      await loadIntegrations();
      await loadLogs(integrationId);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to execute integration synchronization.');
    } finally {
      setSyncingId(null);
    }
  };

  return (
    <div className="container-fluid p-4">
      {/* Header */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="h4 fw-bold text-dark mb-1">🔗 External Business System Connectors</h2>
          <p className="text-muted small mb-0">
            Real-time synchronization pipelines with POS terminals, E-commerce platforms, and external databases for{' '}
            <strong>{activeCompany?.company_name}</strong>.
          </p>
        </div>
      </div>

      {lastSyncResult && (
        <div className="alert alert-success alert-dismissible fade show" role="alert">
          <div className="d-flex align-items-center gap-2">
            <span className="fs-5">✅</span>
            <div>
              <strong>Sync Complete ({lastSyncResult.status}):</strong> Ingested {lastSyncResult.records_processed} records in{' '}
              {lastSyncResult.duration_seconds}s. Cursor checkpoint advanced to{' '}
              <code>{lastSyncResult.cursor_checkpoint}</code>.
            </div>
          </div>
          <button type="button" className="btn-close" onClick={() => setLastSyncResult(null)}></button>
        </div>
      )}

      {error && (
        <div className="alert alert-danger alert-dismissible fade show" role="alert">
          {error}
          <button type="button" className="btn-close" onClick={() => setError(null)}></button>
        </div>
      )}

      <div className="row g-4">
        {/* Left Column: Connectors Cards */}
        <div className="col-12 col-lg-7">
          <div className="d-flex justify-content-between align-items-center mb-3">
            <h5 className="h6 fw-bold text-uppercase text-muted mb-0">Configured Connectors ({integrations.length})</h5>
          </div>

          {loading ? (
            <div className="text-center py-5 text-muted">
              <div className="spinner-border text-primary me-2" role="status" />
              Loading connectors...
            </div>
          ) : integrations.length === 0 ? (
            <div className="card shadow-sm border-0 p-4 text-center text-muted">
              No business connectors configured for this tenant.
            </div>
          ) : (
            <div className="d-flex flex-column gap-3">
              {integrations.map((item) => {
                const isSelected = selectedIntegration?.integration_id === item.integration_id;
                const isSyncing = syncingId === item.integration_id;

                return (
                  <div
                    key={item.integration_id}
                    className={`card shadow-sm border-2 ${isSelected ? 'border-primary' : 'border-0'} cursor-pointer`}
                    onClick={() => {
                      setSelectedIntegration(item);
                      loadLogs(item.integration_id);
                    }}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="card-body p-4">
                      <div className="d-flex justify-content-between align-items-start mb-2">
                        <div>
                          <div className="d-flex align-items-center gap-2">
                            <h5 className="h6 fw-bold mb-0 text-dark">{item.name}</h5>
                            {item.is_active ? (
                              <span className="badge bg-success-subtle text-success border border-success-subtle">
                                Enabled
                              </span>
                            ) : (
                              <span className="badge bg-secondary-subtle text-secondary border">Disabled</span>
                            )}
                          </div>
                          <small className="text-muted">Connector ID: <code>{item.integration_id}</code></small>
                        </div>

                        <div className="d-flex align-items-center gap-2">
                          {hasPermission('manage_integrations') && (
                            <button
                              className="btn btn-sm btn-outline-secondary"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleToggle(item);
                              }}
                            >
                              {item.is_active ? 'Disable' : 'Enable'}
                            </button>
                          )}

                          {hasPermission('manage_integrations') && (
                            <button
                              className="btn btn-sm btn-primary d-flex align-items-center gap-1"
                              disabled={!item.is_active || isSyncing}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleTriggerSync(item.integration_id);
                              }}
                            >
                              {isSyncing ? (
                                <>
                                  <span className="spinner-border spinner-border-sm" />
                                  Syncing...
                                </>
                              ) : (
                                <>
                                  <span>⚡</span> Trigger Sync
                                </>
                              )}
                            </button>
                          )}
                        </div>
                      </div>

                      <div className="row g-2 mt-2 pt-2 border-top small">
                        <div className="col-sm-4">
                          <span className="text-muted d-block">Type:</span>
                          <span className="fw-medium"><code>{item.connector_type}</code></span>
                        </div>
                        <div className="col-sm-4">
                          <span className="text-muted d-block">Last Sync:</span>
                          <span className="fw-medium">
                            {item.last_sync_at ? new Date(item.last_sync_at).toLocaleString() : 'Never Synced'}
                          </span>
                        </div>
                        <div className="col-sm-4">
                          <span className="text-muted d-block">Health / Status:</span>
                          <span className={`badge ${item.sync_status === 'SUCCESS' ? 'bg-success' : 'bg-warning text-dark'}`}>
                            {item.sync_status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Connector Details & Audit Logs */}
        <div className="col-12 col-lg-5">
          <div className="card shadow-sm border-0 sticky-top" style={{ top: '1rem' }}>
            <div className="card-header bg-white py-3">
              <h5 className="h6 fw-bold mb-0">
                {selectedIntegration ? `📜 Audit Logs: ${selectedIntegration.name}` : 'Connector Details'}
              </h5>
            </div>
            <div className="card-body p-3">
              {selectedIntegration ? (
                <>
                  <div className="bg-light p-3 rounded mb-3 small">
                    <div className="fw-bold text-dark mb-1">Configuration Parameters:</div>
                    <pre className="mb-0 text-muted" style={{ fontSize: '0.78rem' }}>
                      {JSON.stringify(selectedIntegration.config, null, 2)}
                    </pre>
                  </div>

                  <h6 className="fw-bold small text-uppercase text-muted mb-2">Sync Execution History</h6>
                  {logs.length === 0 ? (
                    <div className="text-center py-4 text-muted small">
                      No synchronization runs recorded for this connector yet.
                    </div>
                  ) : (
                    <div className="d-flex flex-column gap-2" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                      {logs.map((log) => (
                        <div key={log.log_id} className="p-2 border rounded small bg-white">
                          <div className="d-flex justify-content-between align-items-center mb-1">
                            <span className="fw-semibold"><code>{log.log_id}</code></span>
                            <span className={`badge ${log.status === 'SUCCESS' ? 'bg-success' : 'bg-danger'}`}>
                              {log.status}
                            </span>
                          </div>
                          <div className="d-flex justify-content-between text-muted" style={{ fontSize: '0.75rem' }}>
                            <span>Records: <strong>{log.records_processed}</strong></span>
                            <span>{new Date(log.started_at).toLocaleTimeString()}</span>
                          </div>
                          {log.cursor_checkpoint && (
                            <div className="text-muted mt-1" style={{ fontSize: '0.72rem' }}>
                              Checkpoint: <code>{log.cursor_checkpoint}</code>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-5 text-muted small">
                  Select a connector on the left to view configuration and audit logs.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
