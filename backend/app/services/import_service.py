"""
app/services/import_service.py
------------------------------
Flexible CSV Import Service supporting:
Path A: Raw dataset preservation for arbitrary CSV inspection and queries.
Path B: Structured business import with column mapping wizard into SIMS entities
        (Orders, Products, Inventory, Customers).
"""

import io
import time
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import pandas as pd
from fastapi import HTTPException, status
from app.db.mongo import get_db
from app.schemas.imports import (
    CsvPreviewResponse, RawImportItem, RawDatasetDetail,
    StructuredImportResponse, ImportHistoryItem,
    ImportValidationSummary, ImportExecutionResponse
)

# Column heuristics for automatic field mapping suggestions
COLUMN_ALIASES = {
    "order_id": ["order id", "invoice", "invoice no", "inv", "transaction id", "transaction number", "order_id"],
    "order_date": ["order date", "date", "sale date", "invoice date", "order_date"],
    "ship_date": ["ship date", "shipping date", "delivery date", "ship_date"],
    "ship_mode": ["ship mode", "shipping method", "delivery method", "ship_mode"],
    "customer_id": ["customer id", "client id", "account id", "cust id", "customer_id"],
    "customer_name": ["customer name", "client name", "account name", "customer", "customer_name"],
    "product_id": ["product id", "sku", "item code", "item id", "part number", "product_id"],
    "product_name": ["product name", "item name", "description", "title", "product", "product_name"],
    "category": ["category", "dept", "department", "product category"],
    "sub_category": ["sub category", "sub-category", "subcategory", "group"],
    "sales": ["sales", "revenue", "net amount", "total", "amount", "price total"],
    "quantity": ["quantity", "qty", "units", "units sold", "count"],
    "discount": ["discount", "disc", "rebate", "discount percentage"],
    "profit": ["profit", "margin", "net profit", "earnings"],
    "unit_cost": ["cost", "unit cost", "cogs", "buy price"],
    "unit_price": ["unit price", "retail price", "selling price", "rate"],
    "store_id": ["store", "store id", "branch", "branch id", "location id"]
}


class ImportService:

    @staticmethod
    def _read_csv(file_bytes: bytes) -> pd.DataFrame:
        """Reads CSV with robust encoding fallback."""
        for enc in ["utf-8", "windows-1252", "latin-1"]:
            try:
                df = pd.read_csv(io.BytesIO(file_bytes), encoding=enc)
                return df
            except (UnicodeDecodeError, Exception):
                continue
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to parse CSV file. Supported encodings: UTF-8, Windows-1252, Latin-1."
        )

    @classmethod
    def preview_csv(cls, file_bytes: bytes, filename: str) -> CsvPreviewResponse:
        """
        Parses CSV, identifies column names, suggests field mappings,
        and provides first 10 sample preview rows.
        """
        df = cls._read_csv(file_bytes)
        if df.empty:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded CSV file is empty.")

        # Clean column names
        detected_columns = [str(c).strip() for c in df.columns]

        # Heuristic auto-mapping
        suggested: Dict[str, str] = {}
        for col in detected_columns:
            col_norm = col.lower().replace("_", " ").strip()
            for sims_field, aliases in COLUMN_ALIASES.items():
                if col_norm in aliases or any(alias in col_norm for alias in aliases):
                    if sims_field not in suggested.values():
                        suggested[col] = sims_field
                        break

        # Generate preview rows
        preview_sample = df.head(10).fillna("").to_dict(orient="records")

        return CsvPreviewResponse(
            filename=filename,
            total_rows=len(df),
            detected_columns=detected_columns,
            sample_preview=preview_sample,
            suggested_mappings=suggested
        )

    # -----------------------------------------------------------------
    # PATH A — Raw Dataset Import & Inspection
    # -----------------------------------------------------------------
    @classmethod
    def import_raw_dataset(
        cls,
        file_bytes: bytes,
        filename: str,
        company_id: int,
        store_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> RawImportItem:
        df = cls._read_csv(file_bytes)
        now = datetime.now(timezone.utc).isoformat()
        import_id = f"RAW-{uuid.uuid4().hex[:8].upper()}"

        # Clean NaN values
        records = df.fillna("").to_dict(orient="records")
        columns = [str(c).strip() for c in df.columns]

        doc = {
            "import_id": import_id,
            "company_id": company_id,
            "store_id": store_id,
            "filename": filename,
            "total_rows": len(df),
            "columns": columns,
            "rows": records,
            "imported_by": user_id,
            "created_at": now
        }

        db = get_db()
        db.raw_imports.insert_one(doc)

        return RawImportItem(
            import_id=import_id,
            company_id=company_id,
            store_id=store_id,
            filename=filename,
            total_rows=len(df),
            columns=columns,
            imported_by=user_id,
            created_at=now
        )

    @classmethod
    def list_raw_datasets(cls, company_id: int) -> List[RawImportItem]:
        db = get_db()
        cursor = db.raw_imports.find({"company_id": company_id}).sort("created_at", -1)
        return [
            RawImportItem(
                import_id=r["import_id"],
                company_id=r["company_id"],
                store_id=r.get("store_id"),
                filename=r["filename"],
                total_rows=r["total_rows"],
                columns=r.get("columns", []),
                imported_by=r.get("imported_by"),
                created_at=r["created_at"]
            )
            for r in cursor
        ]

    @classmethod
    def get_raw_dataset(cls, company_id: int, import_id: str, search: Optional[str] = None, limit: int = 100) -> RawDatasetDetail:
        db = get_db()
        doc = db.raw_imports.find_one({"company_id": company_id, "import_id": import_id})
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Raw dataset not found.")

        rows = doc.get("rows", [])
        if search:
            s_low = search.strip().lower()
            rows = [r for r in rows if any(s_low in str(v).lower() for v in r.values())]

        return RawDatasetDetail(
            import_id=doc["import_id"],
            filename=doc["filename"],
            columns=doc.get("columns", []),
            total_rows=len(doc.get("rows", [])),
            rows=rows[:limit]
        )

    # -----------------------------------------------------------------
    # PATH B — Structured Business Import
    # -----------------------------------------------------------------
    @classmethod
    def import_structured(
        cls,
        file_bytes: bytes,
        filename: str,
        target_entity: str,
        column_mapping: Dict[str, str],
        company_id: int,
        store_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> StructuredImportResponse:
        start_time = time.time()
        df = cls._read_csv(file_bytes)
        db = get_db()

        # Invert mapping: sims_field -> source_csv_column
        # column_mapping can be: {"Order ID": "order_id"} or {"order_id": "Order ID"}
        field_to_col: Dict[str, str] = {}
        for k, v in column_mapping.items():
            if v in COLUMN_ALIASES:
                field_to_col[v] = k
            elif k in COLUMN_ALIASES:
                field_to_col[k] = v

        created_count = 0
        updated_count = 0
        errors: List[str] = []
        now = datetime.now(timezone.utc).isoformat()
        import_id = f"STRUC-{uuid.uuid4().hex[:8].upper()}"

        if target_entity == "products":
            col_id = field_to_col.get("product_id") or "Product ID"
            col_name = field_to_col.get("product_name") or "Product Name"
            col_cat = field_to_col.get("category") or "Category"
            col_sub = field_to_col.get("sub_category") or "Sub-Category"
            col_cost = field_to_col.get("unit_cost") or "Unit Cost"
            col_price = field_to_col.get("unit_price") or "Unit Price"

            for idx, row in df.iterrows():
                p_id = str(row.get(col_id, "")).strip()
                if not p_id or p_id == "nan":
                    continue
                p_name = str(row.get(col_name, p_id)).strip()
                category = str(row.get(col_cat, "General")).strip()
                sub_category = str(row.get(col_sub, "")).strip()

                try:
                    cost = float(row.get(col_cost, 0.0))
                except (ValueError, TypeError):
                    cost = 0.0
                try:
                    price = float(row.get(col_price, 0.0))
                except (ValueError, TypeError):
                    price = 0.0

                res = db.products.update_one(
                    {"company_id": company_id, "product_id": p_id},
                    {
                        "$set": {
                            "product_name": p_name,
                            "category": category,
                            "sub_category": sub_category,
                            "sku": p_id,
                            "unit_cost": cost,
                            "unit_price": price,
                            "is_active": True,
                            "last_updated": now
                        },
                        "$setOnInsert": {
                            "company_id": company_id,
                            "product_id": p_id,
                            "created_at": now
                        }
                    },
                    upsert=True
                )
                if res.upserted_id:
                    created_count += 1
                else:
                    updated_count += 1

        elif target_entity == "customers":
            col_id = field_to_col.get("customer_id") or "Customer ID"
            col_name = field_to_col.get("customer_name") or "Customer Name"
            col_seg = field_to_col.get("segment") or "Segment"

            for idx, row in df.iterrows():
                c_id = str(row.get(col_id, "")).strip()
                if not c_id or c_id == "nan":
                    continue
                c_name = str(row.get(col_name, c_id)).strip()
                seg = str(row.get(col_seg, "Consumer")).strip()

                res = db.customers.update_one(
                    {"company_id": company_id, "customer_id": c_id},
                    {
                        "$set": {
                            "customer_name": c_name,
                            "segment": seg,
                            "is_active": True
                        },
                        "$setOnInsert": {
                            "company_id": company_id,
                            "customer_id": c_id,
                            "created_at": now
                        }
                    },
                    upsert=True
                )
                if res.upserted_id:
                    created_count += 1
                else:
                    updated_count += 1

        elif target_entity == "inventory":
            col_pid = field_to_col.get("product_id") or "Product ID"
            col_qty = field_to_col.get("quantity") or "Quantity"
            target_store = store_id or 1

            for idx, row in df.iterrows():
                p_id = str(row.get(col_pid, "")).strip()
                if not p_id or p_id == "nan":
                    continue
                try:
                    qty = int(row.get(col_qty, 0))
                except (ValueError, TypeError):
                    qty = 0

                inv_id = f"{company_id}-{target_store}-{p_id}"
                res = db.inventory.update_one(
                    {"company_id": company_id, "store_id": target_store, "product_id": p_id},
                    {
                        "$set": {
                            "quantity_on_hand": qty,
                            "last_updated": now
                        },
                        "$setOnInsert": {
                            "inventory_id": inv_id,
                            "company_id": company_id,
                            "store_id": target_store,
                            "product_id": p_id,
                            "min_threshold": 5,
                            "max_threshold": 100
                        }
                    },
                    upsert=True
                )
                if res.upserted_id:
                    created_count += 1
                else:
                    updated_count += 1

        else:  # "orders" (default)
            # Legacy-compatible order import with flexible columns
            res = cls.execute_import(file_bytes, company_id=company_id, store_id=store_id, user_id=user_id)
            return StructuredImportResponse(
                import_id=import_id,
                success=res.success,
                target_entity="orders",
                total_processed=res.total_processed,
                records_created=res.orders_upserted,
                records_updated=res.customers_upserted + res.products_upserted,
                errors_count=0,
                duration_seconds=res.duration_seconds,
                message=res.message
            )

        duration = round(time.time() - start_time, 2)
        history_doc = {
            "import_id": import_id,
            "company_id": company_id,
            "store_id": store_id,
            "import_type": "STRUCTURED_BUSINESS",
            "target_entity": target_entity,
            "filename": filename,
            "total_records": len(df),
            "status": "SUCCESS",
            "imported_by": user_id,
            "created_at": now
        }
        db.structured_imports.insert_one(history_doc)

        return StructuredImportResponse(
            import_id=import_id,
            success=True,
            target_entity=target_entity,
            total_processed=len(df),
            records_created=created_count,
            records_updated=updated_count,
            errors_count=len(errors),
            errors=errors,
            duration_seconds=duration,
            message=f"Successfully imported {created_count + updated_count} {target_entity} into company ID {company_id}."
        )

    # -----------------------------------------------------------------
    # Legacy Order ETL Implementation (backward compatible for existing tests)
    # -----------------------------------------------------------------
    @classmethod
    def validate_csv(cls, file_bytes: bytes) -> ImportValidationSummary:
        df = cls._read_csv(file_bytes)
        columns = [str(c).strip() for c in df.columns]
        required = ["Order ID", "Customer ID", "Product ID", "Sales", "Quantity"]
        missing = [r for r in required if not any(r.lower() == c.lower() for c in columns)]

        errors: List[str] = []
        if missing:
            errors.append(f"Missing required columns: {', '.join(missing)}")
        if df.empty:
            errors.append("The uploaded CSV file contains no data rows.")

        preview = df.head(5).fillna("").to_dict(orient="records")
        return ImportValidationSummary(
            is_valid=len(missing) == 0 and not df.empty,
            total_rows=len(df),
            valid_rows=len(df),
            columns_detected=columns,
            missing_columns=missing,
            sample_preview=preview,
            validation_errors=errors
        )

    @classmethod
    def execute_import(
        cls,
        file_bytes: bytes,
        company_id: int,
        store_id: Optional[int] = None,
        user_id: Optional[int] = None
    ) -> ImportExecutionResponse:
        start_time = time.time()
        df = cls._read_csv(file_bytes)
        db = get_db()

        target_store = store_id or 1
        now = datetime.now(timezone.utc).isoformat()

        # Group rows by Order ID
        order_col = next((c for c in df.columns if "order" in c.lower() and "id" in c.lower()), "Order ID")
        cust_id_col = next((c for c in df.columns if "customer" in c.lower() and "id" in c.lower()), "Customer ID")
        cust_name_col = next((c for c in df.columns if "customer" in c.lower() and "name" in c.lower()), "Customer Name")
        prod_id_col = next((c for c in df.columns if "product" in c.lower() and "id" in c.lower()), "Product ID")
        prod_name_col = next((c for c in df.columns if "product" in c.lower() and "name" in c.lower()), "Product Name")
        cat_col = next((c for c in df.columns if "category" in c.lower() and "sub" not in c.lower()), "Category")
        sub_cat_col = next((c for c in df.columns if "sub" in c.lower()), "Sub-Category")
        sales_col = next((c for c in df.columns if "sale" in c.lower() or "amount" in c.lower() or "revenue" in c.lower()), "Sales")
        qty_col = next((c for c in df.columns if "qty" in c.lower() or "quantity" in c.lower()), "Quantity")
        disc_col = next((c for c in df.columns if "discount" in c.lower()), "Discount")
        prof_col = next((c for c in df.columns if "profit" in c.lower()), "Profit")
        date_col = next((c for c in df.columns if "date" in c.lower()), "Order Date")

        cust_count = 0
        prod_count = 0
        order_count = 0
        lines_count = 0

        # Group by order
        grouped = df.groupby(order_col)
        for ord_id, group in grouped:
            ord_id_str = str(ord_id).strip()
            first_row = group.iloc[0]

            # Upsert customer
            cid = str(first_row.get(cust_id_col, f"CUST-{ord_id_str}")).strip()
            cname = str(first_row.get(cust_name_col, cid)).strip()
            seg = str(first_row.get("Segment", "Consumer")).strip()
            c_res = db.customers.update_one(
                {"company_id": company_id, "customer_id": cid},
                {"$set": {"customer_name": cname, "segment": seg, "is_active": True}},
                upsert=True
            )
            if c_res.upserted_id:
                cust_count += 1

            order_lines = []
            for l_idx, (_, row) in enumerate(group.iterrows(), 1):
                pid = str(row.get(prod_id_col, f"PROD-{l_idx}")).strip()
                pname = str(row.get(prod_name_col, pid)).strip()
                cat = str(row.get(cat_col, "General")).strip()
                subcat = str(row.get(sub_cat_col, "")).strip()
                try:
                    sales = float(row.get(sales_col, 0.0))
                except (ValueError, TypeError):
                    sales = 0.0
                try:
                    qty = int(row.get(qty_col, 1))
                except (ValueError, TypeError):
                    qty = 1
                try:
                    disc = float(row.get(disc_col, 0.0))
                except (ValueError, TypeError):
                    disc = 0.0
                try:
                    profit = float(row.get(prof_col, 0.0))
                except (ValueError, TypeError):
                    profit = 0.0

                # Upsert product
                p_res = db.products.update_one(
                    {"company_id": company_id, "product_id": pid},
                    {
                        "$set": {
                            "product_name": pname,
                            "category": cat,
                            "sub_category": subcat,
                            "sku": pid,
                            "is_active": True
                        }
                    },
                    upsert=True
                )
                if p_res.upserted_id:
                    prod_count += 1

                order_lines.append({
                    "line_id": l_idx,
                    "product_id": pid,
                    "product_name": pname,
                    "category": cat,
                    "sub_category": subcat,
                    "sales": round(sales, 2),
                    "quantity": qty,
                    "discount": round(disc, 2),
                    "profit": round(profit, 2)
                })
                lines_count += 1

            # Insert/update order
            ord_date_raw = str(first_row.get(date_col, datetime.now().strftime("%Y-%m-%d"))).strip()
            # Parse date safely
            try:
                parsed_date = pd.to_datetime(ord_date_raw).strftime("%Y-%m-%d")
            except Exception:
                parsed_date = datetime.now().strftime("%Y-%m-%d")

            total_sales = sum(l["sales"] for l in order_lines)
            total_qty = sum(l["quantity"] for l in order_lines)
            total_profit = sum(l["profit"] for l in order_lines)

            o_doc = {
                "order_id": ord_id_str,
                "company_id": company_id,
                "store_id": target_store,
                "customer_id": cid,
                "order_date": parsed_date,
                "ship_date": None,
                "ship_mode": str(first_row.get("Ship Mode", "Standard Class")),
                "country": str(first_row.get("Country", "United States")),
                "city": str(first_row.get("City", "")),
                "state": str(first_row.get("State", "")),
                "postal_code": str(first_row.get("Postal Code", "")),
                "region": str(first_row.get("Region", "Central")),
                "lines": order_lines,
                "total_sales": round(total_sales, 2),
                "total_quantity": total_qty,
                "total_profit": round(total_profit, 2),
                "created_at": now
            }
            db.orders.update_one(
                {"company_id": company_id, "order_id": ord_id_str},
                {"$set": o_doc},
                upsert=True
            )
            order_count += 1

        duration = round(time.time() - start_time, 2)
        return ImportExecutionResponse(
            success=True,
            total_processed=len(df),
            customers_upserted=cust_count,
            products_upserted=prod_count,
            orders_upserted=order_count,
            order_details_inserted=lines_count,
            message=f"Successfully imported {order_count} orders ({lines_count} lines) into Store #{target_store}.",
            duration_seconds=duration
        )

    @classmethod
    def get_import_history(cls, company_id: int) -> List[ImportHistoryItem]:
        db = get_db()
        results: List[ImportHistoryItem] = []

        # Raw imports
        for r in db.raw_imports.find({"company_id": company_id}).sort("created_at", -1).limit(20):
            results.append(ImportHistoryItem(
                import_id=r["import_id"],
                company_id=r["company_id"],
                store_id=r.get("store_id"),
                import_type="RAW_DATASET",
                target_entity="raw_dataset",
                filename=r["filename"],
                total_records=r["total_rows"],
                status="STORED",
                created_at=r["created_at"]
            ))

        # Structured imports
        for s in db.structured_imports.find({"company_id": company_id}).sort("created_at", -1).limit(20):
            results.append(ImportHistoryItem(
                import_id=s["import_id"],
                company_id=s["company_id"],
                store_id=s.get("store_id"),
                import_type="STRUCTURED_BUSINESS",
                target_entity=s.get("target_entity"),
                filename=s["filename"],
                total_records=s["total_records"],
                status=s.get("status", "SUCCESS"),
                created_at=s["created_at"]
            ))

        return sorted(results, key=lambda x: x.created_at, reverse=True)
