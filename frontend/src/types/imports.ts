export interface CsvPreview {
  filename: string;
  total_rows: number;
  detected_columns: string[];
  suggested_mappings: Record<string, string>;
  preview_rows: Record<string, any>[];
}

export interface RawDatasetItem {
  dataset_id: string;
  company_id: number;
  store_id?: number | null;
  filename: string;
  row_count: number;
  column_names: string[];
  uploaded_by: number;
  uploaded_at: string;
}

export interface StructuredImportResult {
  import_id: string;
  target_entity: string;
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  errors: string[];
  duration_seconds: number;
  imported_at: string;
}

export interface ImportHistory {
  import_id: string;
  company_id: number;
  import_type: string;
  target_entity?: string | null;
  filename: string;
  total_rows: number;
  successful_rows: number;
  failed_rows: number;
  status: string;
  user_id: number;
  created_at: string;
}
