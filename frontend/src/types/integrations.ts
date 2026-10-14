export interface Integration {
  integration_id: string;
  company_id: number;
  store_id?: number | null;
  name: string;
  connector_type: 'POS_REST_API' | 'ECOMMERCE_WEBHOOK' | 'MOCK_STORE_CONNECTOR';
  is_active: boolean;
  config: Record<string, any>;
  last_sync_at?: string | null;
  sync_status: 'IDLE' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'PENDING';
  created_at: string;
}

export interface SyncExecutionResult {
  log_id: string;
  integration_id: string;
  status: 'SUCCESS' | 'PARTIAL' | 'FAILED';
  records_processed: number;
  cursor_checkpoint?: string | null;
  errors: string[];
  duration_seconds: number;
  synced_at: string;
}

export interface SyncLogItem {
  log_id: string;
  integration_id: string;
  company_id: number;
  sync_type: string;
  records_processed: number;
  errors: string[];
  status: string;
  started_at: string;
  completed_at?: string | null;
  cursor_checkpoint?: string | null;
}
