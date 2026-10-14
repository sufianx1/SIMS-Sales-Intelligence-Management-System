"""
app/schemas/imports.py
----------------------
Pydantic contracts for Flexible CSV Import:
- Path A: Raw Dataset Preservation and Inspection
- Path B: Structured Business Import with Field Mapping Wizard
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class CsvPreviewResponse(BaseModel):
    filename: str
    total_rows: int
    detected_columns: List[str]
    sample_preview: List[Dict[str, Any]]
    suggested_mappings: Dict[str, str] = Field(default_factory=dict, description="Heuristic auto-mapping to SIMS fields")
    supported_entities: List[str] = ["orders", "products", "inventory", "customers"]


class RawImportItem(BaseModel):
    import_id: str
    company_id: int
    store_id: Optional[int] = None
    filename: str
    total_rows: int
    columns: List[str]
    imported_by: Optional[int] = None
    created_at: str


class RawDatasetDetail(BaseModel):
    import_id: str
    filename: str
    columns: List[str]
    total_rows: int
    rows: List[Dict[str, Any]]


class StructuredImportResponse(BaseModel):
    import_id: str
    success: bool
    target_entity: str
    total_processed: int
    records_created: int
    records_updated: int
    errors_count: int
    errors: List[str] = []
    duration_seconds: float = 0.0
    message: str


class ImportHistoryItem(BaseModel):
    import_id: str
    company_id: int
    store_id: Optional[int] = None
    import_type: str  # "RAW_DATASET" or "STRUCTURED_BUSINESS"
    target_entity: Optional[str] = None
    filename: str
    total_records: int
    status: str
    created_at: str


# Legacy schemas retained for backwards compatibility with tests and callers
class ImportValidationSummary(BaseModel):
    is_valid: bool
    total_rows: int
    valid_rows: int
    columns_detected: List[str] = Field(default_factory=list)
    missing_columns: List[str] = Field(default_factory=list)
    sample_preview: List[Dict[str, Any]] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)


class ImportExecutionResponse(BaseModel):
    success: bool
    total_processed: int
    customers_upserted: int
    products_upserted: int
    orders_upserted: int
    order_details_inserted: int
    message: str
    duration_seconds: float = 0.0
