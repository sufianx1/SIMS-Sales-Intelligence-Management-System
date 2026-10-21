"""
app/api/routes/imports.py
-------------------------
FastAPI route handlers for Flexible CSV Import:
- Preview & Column Mapping Detection
- Path A: Raw Dataset Import & Exploration
- Path B: Structured Business Import (Orders, Products, Inventory, Customers)
- Import Audit History & Statistics
"""

from typing import Optional, List, Dict
import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException, status
from app.api.dependencies import get_current_user, get_tenant_context, require_permission
from app.core.config import settings
from app.schemas.auth import UserProfile, TenantContext
from app.schemas.imports import (
    CsvPreviewResponse, RawImportItem, RawDatasetDetail,
    StructuredImportResponse, ImportHistoryItem,
    ImportValidationSummary, ImportExecutionResponse
)
from app.services.import_service import ImportService

router = APIRouter(prefix="/imports", tags=["Data Import"])


async def read_and_validate_csv(file: UploadFile) -> bytes:
    """
    Validates CSV file extension, enforces MAX_UPLOAD_SIZE_BYTES to prevent memory exhaustion,
    and returns file content bytes.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported.")

    max_size = settings.MAX_UPLOAD_SIZE_BYTES
    content = await file.read(max_size + 1)
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {max_size // (1024 * 1024)}MB."
        )
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")

    return content


@router.post("/preview", response_model=CsvPreviewResponse, status_code=status.HTTP_200_OK)
async def preview_csv_file(
    file: UploadFile = File(...),
    context: TenantContext = Depends(require_permission("import_data"))
):
    """
    Uploads a CSV file to inspect headers, data types, detected columns,
    and automatic field mapping suggestions before executing an import.
    """
    content = await read_and_validate_csv(file)
    return ImportService.preview_csv(content, file.filename)


# ---------------------------------------------------------------------
# PATH A — Raw Dataset Import & Inspection
# ---------------------------------------------------------------------
@router.post("/raw", response_model=RawImportItem, status_code=status.HTTP_201_CREATED)
async def import_raw_dataset(
    file: UploadFile = File(...),
    store_id: Optional[int] = Form(None),
    current_user: UserProfile = Depends(get_current_user),
    context: TenantContext = Depends(require_permission("import_data"))
):
    """
    Path A: Preserves source CSV columns and rows exactly as uploaded
    for independent inspection and dataset queries.
    """
    content = await read_and_validate_csv(file)
    target_store = store_id or context.store_id
    return ImportService.import_raw_dataset(
        file_bytes=content,
        filename=file.filename,
        company_id=context.company_id,
        store_id=target_store,
        user_id=current_user.user_id
    )


@router.get("/raw", response_model=List[RawImportItem], status_code=status.HTTP_200_OK)
def list_raw_datasets(
    context: TenantContext = Depends(require_permission("import_data"))
):
    """
    Lists all raw datasets imported for the active tenant.
    """
    return ImportService.list_raw_datasets(context.company_id)


@router.get("/raw/{import_id}", response_model=RawDatasetDetail, status_code=status.HTTP_200_OK)
def get_raw_dataset_detail(
    import_id: str,
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    context: TenantContext = Depends(require_permission("import_data"))
):
    """
    Retrieves preserved raw dataset columns and rows with search filtering.
    """
    return ImportService.get_raw_dataset(
        company_id=context.company_id,
        import_id=import_id,
        search=search,
        limit=limit
    )


# ---------------------------------------------------------------------
# PATH B — Structured Business Import
# ---------------------------------------------------------------------
@router.post("/structured", response_model=StructuredImportResponse, status_code=status.HTTP_200_OK)
async def import_structured_data(
    file: UploadFile = File(...),
    target_entity: str = Form("orders", description="Entity type: orders, products, inventory, customers"),
    column_mapping_json: Optional[str] = Form(None, description="JSON string mapping SIMS fields to CSV column names"),
    column_mappings: Optional[str] = Form(None, description="Alternative field name for mapping JSON"),
    store_id: Optional[int] = Form(None),
    current_user: UserProfile = Depends(get_current_user),
    context: TenantContext = Depends(require_permission("import_data"))
):
    """
    Path B: Maps validated columns into structured SIMS entities
    (Orders, Products, Inventory, or Customers) with validation and deduplication.
    """
    content = await read_and_validate_csv(file)
    raw_mapping = column_mapping_json or column_mappings or "{}"
    try:
        mapping: Dict[str, str] = json.loads(raw_mapping) if raw_mapping else {}
    except Exception:
        mapping = {}

    target_store = store_id or context.store_id

    return ImportService.import_structured(
        file_bytes=content,
        filename=file.filename,
        target_entity=target_entity.strip().lower(),
        column_mapping=mapping,
        company_id=context.company_id,
        store_id=target_store,
        user_id=current_user.user_id
    )


@router.get("/history", response_model=List[ImportHistoryItem], status_code=status.HTTP_200_OK)
def get_import_history(
    context: TenantContext = Depends(require_permission("import_data"))
):
    """
    Returns audit history of all data imports for the active company.
    """
    return ImportService.get_import_history(context.company_id)


# ---------------------------------------------------------------------
# Legacy routes (kept for backwards compatibility)
# ---------------------------------------------------------------------
@router.post("/validate", response_model=ImportValidationSummary, status_code=status.HTTP_200_OK)
async def validate_import_file(
    file: UploadFile = File(...),
    context: TenantContext = Depends(require_permission("import_data"))
):
    content = await read_and_validate_csv(file)
    return ImportService.validate_csv(content)


@router.post("/execute", response_model=ImportExecutionResponse, status_code=status.HTTP_200_OK)
async def execute_sales_import(
    file: UploadFile = File(...),
    store_id: Optional[int] = Form(None),
    current_user: UserProfile = Depends(get_current_user),
    context: TenantContext = Depends(require_permission("import_data"))
):
    content = await read_and_validate_csv(file)
    target_store = store_id or context.store_id
    if target_store:
        from app.db.mongo import get_db
        st = get_db().stores.find_one({"company_id": context.company_id, "store_id": int(target_store)})
        if not st:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Store ID {target_store} does not belong to active company."
            )

    return ImportService.execute_import(
        file_bytes=content,
        company_id=context.company_id,
        store_id=target_store,
        user_id=current_user.user_id
    )
