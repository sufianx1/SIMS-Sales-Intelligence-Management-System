import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { storesApi, importsApi } from '../../api';
import { Store } from '../../types/company';
import { CsvPreview, RawDatasetItem, ImportHistory, StructuredImportResult } from '../../types/imports';

export const ImportPage: React.FC = () => {
  const { activeCompany, hasPermission } = useAuth();

  const [activeTab, setActiveTab] = useState<'structured' | 'raw' | 'history'>('structured');
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<number | undefined>(undefined);

  // File states
  const [file, setFile] = useState<File | null>(null);
  const [previewData, setPreviewData] = useState<CsvPreview | null>(null);
  const [targetEntity, setTargetEntity] = useState<string>('orders');
  const [columnMappings, setColumnMappings] = useState<Record<string, string>>({});

  // Loading & feedback
  const [previewing, setPreviewing] = useState<boolean>(false);
  const [executing, setExecuting] = useState<boolean>(false);
  const [structuredResult, setStructuredResult] = useState<StructuredImportResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Path A Raw state
  const [rawFile, setRawFile] = useState<File | null>(null);
  const [rawDatasets, setRawDatasets] = useState<RawDatasetItem[]>([]);
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [datasetDetail, setDatasetDetail] = useState<{
    dataset_id: string;
    filename: string;
    row_count: number;
    column_names: string[];
    rows: Record<string, any>[];
  } | null>(null);
  const [rawSearchQuery, setRawSearchQuery] = useState<string>('');

  // History state
  const [history, setHistory] = useState<ImportHistory[]>([]);

  useEffect(() => {
    storesApi.list().then((res) => {
      setStores(res);
      if (res.length > 0) {
        setSelectedStoreId(res[0].store_id);
      }
    }).catch(console.error);

    loadRawDatasets();
    loadHistory();
  }, [activeCompany]);

  const loadRawDatasets = async () => {
    try {
      const data = await importsApi.listRawDatasets();
      setRawDatasets(data);
    } catch (err: any) {
      console.error('Failed to load raw datasets', err);
    }
  };

  const loadHistory = async () => {
    try {
      const data = await importsApi.getHistory();
      setHistory(data);
    } catch (err: any) {
      console.error('Failed to load import history', err);
    }
  };

  // Preview file for Path B
  const handlePreviewFile = async (selectedFile: File) => {
    setFile(selectedFile);
    setPreviewData(null);
    setStructuredResult(null);
    setErrorMsg(null);
    setPreviewing(true);

    try {
      const p = await importsApi.preview(selectedFile);
      setPreviewData(p);
      setColumnMappings(p.suggested_mappings || {});
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to inspect CSV file structure.');
    } finally {
      setPreviewing(false);
    }
  };

  const handleStructuredImport = async () => {
    if (!file) return;
    setExecuting(true);
    setErrorMsg(null);
    setStructuredResult(null);

    try {
      const res = await importsApi.structuredImport(file, targetEntity, columnMappings, selectedStoreId);
      setStructuredResult(res);
      setSuccessMsg(`Structured business import completed! Successfully processed ${res.successful_rows} / ${res.total_rows} records.`);
      loadHistory();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to execute structured import.');
    } finally {
      setExecuting(false);
    }
  };

  const handleRawImport = async () => {
    if (!rawFile) return;
    setExecuting(true);
    setErrorMsg(null);

    try {
      const res = await importsApi.rawImport(rawFile, selectedStoreId);
      setSuccessMsg(`Raw dataset '${res.filename}' ingested with ${res.row_count} preserved records.`);
      setRawFile(null);
      loadRawDatasets();
      loadHistory();
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to ingest raw dataset.');
    } finally {
      setExecuting(false);
    }
  };

  const handleExploreDataset = async (datasetId: string) => {
    setSelectedDatasetId(datasetId);
    try {
      const detail = await importsApi.getRawDatasetDetail(datasetId, { query: rawSearchQuery || undefined });
      setDatasetDetail(detail);
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to load dataset details.');
    }
  };

  // Predefined target fields depending on target entity
  const getStandardFields = () => {
    switch (targetEntity) {
      case 'ORDERS':
        return ['order_id', 'order_date', 'customer_id', 'customer_name', 'product_id', 'product_name', 'quantity', 'sales', 'discount', 'profit', 'store_id'];
      case 'PRODUCTS':
        return ['product_id', 'product_name', 'category', 'sub_category', 'unit_cost', 'unit_price', 'sku'];
      case 'INVENTORY':
        return ['product_id', 'quantity_on_hand', 'min_threshold', 'store_id'];
      case 'CUSTOMERS':
        return ['customer_id', 'customer_name', 'segment', 'city', 'state', 'country'];
      default:
        return ['order_id', 'product_id', 'quantity', 'sales'];
    }
  };

  return (
    <div className="container-fluid p-4">
      {/* Header */}
      <div className="mb-4">
        <h2 className="h4 fw-bold text-dark mb-1">📥 Flexible Multi-Tenant Data Ingestion</h2>
        <p className="text-muted small mb-0">
          Support for variable column headers, raw dataset preservation (Path A), and structured entity normalization (Path B) for{' '}
          <strong>{activeCompany?.company_name}</strong>.
        </p>
      </div>

      {successMsg && (
        <div className="alert alert-success alert-dismissible fade show" role="alert">
          {successMsg}
          <button type="button" className="btn-close" onClick={() => setSuccessMsg(null)}></button>
        </div>
      )}

      {errorMsg && (
        <div className="alert alert-danger alert-dismissible fade show" role="alert">
          {errorMsg}
          <button type="button" className="btn-close" onClick={() => setErrorMsg(null)}></button>
        </div>
      )}

      {/* Tabs */}
      <ul className="nav nav-tabs mb-4">
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === 'structured' ? 'active fw-bold' : ''}`}
            onClick={() => setActiveTab('structured')}
          >
            ⚡ Path B: Structured Business Import
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === 'raw' ? 'active fw-bold' : ''}`}
            onClick={() => setActiveTab('raw')}
          >
            📂 Path A: Raw Dataset Exploration ({rawDatasets.length})
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === 'history' ? 'active fw-bold' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            📜 Import Audit Trail ({history.length})
          </button>
        </li>
      </ul>

      {/* TAB 1: Structured Business Import */}
      {activeTab === 'structured' && (
        <div className="row g-4">
          <div className="col-12 col-lg-5">
            <div className="card shadow-sm border-0 mb-4">
              <div className="card-header bg-white py-3">
                <h5 className="h6 fw-bold mb-0">1. Upload & Destination Setup</h5>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <label className="form-label small fw-bold">Select CSV File</label>
                  <input
                    type="file"
                    accept=".csv"
                    className="form-control"
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        handlePreviewFile(e.target.files[0]);
                      }
                    }}
                  />
                  <small className="text-muted">Supports Superstore, Retail POS, or customized export files.</small>
                </div>

                <div className="mb-3">
                  <label className="form-label small fw-bold">Target Business Entity</label>
                  <select
                    className="form-select"
                    value={targetEntity}
                    onChange={(e) => setTargetEntity(e.target.value)}
                  >
                    <option value="orders">Orders & Sales Line Items</option>
                    <option value="products">Product Catalog</option>
                    <option value="inventory">Inventory Levels</option>
                    <option value="customers">Customer Directory</option>
                  </select>
                </div>

                <div className="mb-3">
                  <label className="form-label small fw-bold">Default Destination Store</label>
                  <select
                    className="form-select"
                    value={selectedStoreId || ''}
                    onChange={(e) => setSelectedStoreId(parseInt(e.target.value, 10))}
                  >
                    {stores.map((s) => (
                      <option key={s.store_id} value={s.store_id}>
                        {s.store_name} ({s.location || 'Store'})
                      </option>
                    ))}
                  </select>
                  <small className="text-muted">Applied if the CSV does not contain a specific store column.</small>
                </div>

                {previewData && (
                  <button
                    className="btn btn-primary w-100 mt-2"
                    disabled={executing}
                    onClick={handleStructuredImport}
                  >
                    {executing ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2" />
                        Normalizing & Importing...
                      </>
                    ) : (
                      '🚀 Execute Structured Import'
                    )}
                  </button>
                )}
              </div>
            </div>

            {structuredResult && (
              <div className="card shadow-sm border-0 bg-success-subtle border-success">
                <div className="card-body">
                  <h6 className="fw-bold text-success mb-2">Import Results Summary</h6>
                  <div className="small">
                    <div><strong>Target:</strong> {structuredResult.target_entity}</div>
                    <div><strong>Rows Processed:</strong> {structuredResult.total_rows}</div>
                    <div><strong>Successful:</strong> {structuredResult.successful_rows}</div>
                    <div><strong>Failed:</strong> {structuredResult.failed_rows}</div>
                    <div><strong>Elapsed Time:</strong> {structuredResult.duration_seconds}s</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="col-12 col-lg-7">
            <div className="card shadow-sm border-0">
              <div className="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                <h5 className="h6 fw-bold mb-0">2. Field Mapping & Transformation Preview</h5>
                {previewData && (
                  <span className="badge bg-primary">
                    {previewData.total_rows} Rows Detected
                  </span>
                )}
              </div>
              <div className="card-body">
                {previewing ? (
                  <div className="text-center py-5 text-muted">
                    <div className="spinner-border text-primary me-2" role="status" />
                    Inspecting CSV headers and schema...
                  </div>
                ) : !previewData ? (
                  <div className="text-center py-5 text-muted">
                    Upload a CSV file on the left to preview detected columns and configure mappings.
                  </div>
                ) : (
                  <>
                    <h6 className="small fw-bold text-uppercase text-muted mb-2">Column Mapping Configuration</h6>
                    <div className="table-responsive mb-4" style={{ maxHeight: '280px', overflowY: 'auto' }}>
                      <table className="table table-sm table-bordered align-middle">
                        <thead className="table-light">
                          <tr>
                            <th>Standard SIMS Field</th>
                            <th>Detected Source Column in CSV</th>
                          </tr>
                        </thead>
                        <tbody>
                          {getStandardFields().map((field) => (
                            <tr key={field}>
                              <td className="fw-semibold font-monospace small">{field}</td>
                              <td>
                                <select
                                  className="form-select form-select-sm"
                                  value={columnMappings[field] || ''}
                                  onChange={(e) => {
                                    setColumnMappings({
                                      ...columnMappings,
                                      [field]: e.target.value,
                                    });
                                  }}
                                >
                                  <option value="">— Unmapped —</option>
                                  {previewData.detected_columns.map((col) => (
                                    <option key={col} value={col}>
                                      {col}
                                    </option>
                                  ))}
                                </select>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>

                    <h6 className="small fw-bold text-uppercase text-muted mb-2">First 5 Source Rows (Sample Preview)</h6>
                    <div className="table-responsive" style={{ maxHeight: '220px', overflowY: 'auto' }}>
                      <table className="table table-sm table-striped small mb-0">
                        <thead>
                          <tr>
                            {previewData.detected_columns.map((c) => (
                              <th key={c} className="text-nowrap">{c}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {previewData.preview_rows.map((row, idx) => (
                            <tr key={idx}>
                              {previewData.detected_columns.map((c) => (
                                <td key={c} className="text-nowrap">{row[c] !== undefined ? String(row[c]) : ''}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: Raw Dataset Exploration (Path A) */}
      {activeTab === 'raw' && (
        <div className="row g-4">
          <div className="col-12 col-lg-4">
            <div className="card shadow-sm border-0 mb-4">
              <div className="card-header bg-white py-3">
                <h5 className="h6 fw-bold mb-0">Ingest Raw Dataset (Preserve All Columns)</h5>
              </div>
              <div className="card-body">
                <p className="text-muted small">
                  Path A preserves unfamiliar columns and original data verbatim without schema coercion, enabling search and investigation.
                </p>
                <div className="mb-3">
                  <input
                    type="file"
                    accept=".csv"
                    className="form-control"
                    onChange={(e) => {
                      if (e.target.files && e.target.files.length > 0) {
                        setRawFile(e.target.files[0]);
                      }
                    }}
                  />
                </div>
                <button
                  className="btn btn-outline-primary w-100"
                  disabled={!rawFile || executing}
                  onClick={handleRawImport}
                >
                  {executing ? 'Ingesting...' : '📥 Ingest Raw Dataset'}
                </button>
              </div>
            </div>

            <div className="card shadow-sm border-0">
              <div className="card-header bg-white py-3">
                <h5 className="h6 fw-bold mb-0">Saved Datasets ({rawDatasets.length})</h5>
              </div>
              <div className="card-body p-0">
                {rawDatasets.length === 0 ? (
                  <div className="p-4 text-center text-muted small">
                    No raw datasets ingested yet.
                  </div>
                ) : (
                  <div className="list-group list-group-flush">
                    {rawDatasets.map((ds) => (
                      <button
                        key={ds.dataset_id}
                        className={`list-group-item list-group-item-action ${selectedDatasetId === ds.dataset_id ? 'active' : ''}`}
                        onClick={() => handleExploreDataset(ds.dataset_id)}
                      >
                        <div className="d-flex justify-content-between align-items-center mb-1">
                          <strong className="text-truncate">{ds.filename}</strong>
                          <span className="badge bg-secondary">{ds.row_count} rows</span>
                        </div>
                        <small className="d-block text-truncate" style={{ opacity: 0.8 }}>
                          {ds.column_names.join(', ')}
                        </small>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="col-12 col-lg-8">
            <div className="card shadow-sm border-0">
              <div className="card-header bg-white py-3 d-flex justify-content-between align-items-center">
                <h5 className="h6 fw-bold mb-0">
                  {datasetDetail ? `Exploring: ${datasetDetail.filename}` : 'Dataset Records Explorer'}
                </h5>
                {datasetDetail && (
                  <span className="badge bg-info text-dark">
                    {datasetDetail.row_count} Total Rows
                  </span>
                )}
              </div>
              <div className="card-body">
                {datasetDetail ? (
                  <>
                    <div className="input-group input-group-sm mb-3">
                      <input
                        type="text"
                        className="form-control"
                        placeholder="Search across all preserved columns..."
                        value={rawSearchQuery}
                        onChange={(e) => setRawSearchQuery(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleExploreDataset(datasetDetail.dataset_id);
                        }}
                      />
                      <button
                        className="btn btn-outline-secondary"
                        onClick={() => handleExploreDataset(datasetDetail.dataset_id)}
                      >
                        Search
                      </button>
                    </div>

                    <div className="table-responsive" style={{ maxHeight: '500px', overflowY: 'auto' }}>
                      <table className="table table-sm table-striped small mb-0">
                        <thead className="table-light sticky-top">
                          <tr>
                            {datasetDetail.column_names.map((col) => (
                              <th key={col} className="text-nowrap">{col}</th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {datasetDetail.rows.map((r, i) => (
                            <tr key={i}>
                              {datasetDetail.column_names.map((col) => (
                                <td key={col} className="text-nowrap">{r[col] !== undefined ? String(r[col]) : ''}</td>
                              ))}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-5 text-muted">
                    Select a dataset on the left to view and search its raw rows.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: Import Audit Trail */}
      {activeTab === 'history' && (
        <div className="card shadow-sm border-0">
          <div className="table-responsive">
            <table className="table table-hover align-middle mb-0">
              <thead className="table-light">
                <tr>
                  <th>Import ID</th>
                  <th>Timestamp</th>
                  <th>Type</th>
                  <th>Target Entity</th>
                  <th>Source Filename</th>
                  <th className="text-end">Total Rows</th>
                  <th className="text-end">Successful</th>
                  <th className="text-end">Failed</th>
                  <th className="text-center">Status</th>
                </tr>
              </thead>
              <tbody>
                {history.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-4 text-muted">
                      No import operations recorded yet.
                    </td>
                  </tr>
                ) : (
                  history.map((h) => (
                    <tr key={h.import_id}>
                      <td><code>{h.import_id}</code></td>
                      <td className="small text-muted">{new Date(h.created_at).toLocaleString()}</td>
                      <td>
                        <span className={`badge ${h.import_type === 'STRUCTURED_BUSINESS' ? 'bg-primary' : 'bg-secondary'}`}>
                          {h.import_type}
                        </span>
                      </td>
                      <td>{h.target_entity || '—'}</td>
                      <td className="fw-medium">{h.filename}</td>
                      <td className="text-end fw-bold">{h.total_rows}</td>
                      <td className="text-end text-success fw-bold">{h.successful_rows}</td>
                      <td className="text-end text-danger fw-bold">{h.failed_rows}</td>
                      <td className="text-center">
                        <span className={`badge ${h.status === 'SUCCESS' ? 'bg-success' : 'bg-warning text-dark'}`}>
                          {h.status}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
