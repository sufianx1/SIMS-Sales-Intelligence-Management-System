"""
app/repositories/company_repo.py
--------------------------------
MongoDB repository for Companies (tenants) and Stores.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pymongo.database import Database
from app.db.mongo import get_db


class CompanyRepository:

    @staticmethod
    def list_all(db: Optional[Database] = None) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        cursor = database.companies.find({}).sort("company_name", 1)
        results = []
        for r in cursor:
            # Count stores and active status
            store_count = database.stores.count_documents({"company_id": r["company_id"]})
            results.append({
                "company_id": r["company_id"],
                "company_name": r["company_name"],
                "code": r.get("code", ""),
                "is_active": bool(r.get("is_active", True)),
                "created_at": r.get("created_at", ""),
                "store_count": store_count,
                "settings": r.get("settings", {})
            })
        return results

    @staticmethod
    def get_by_id(company_id: int, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        database = db if db is not None else get_db()
        r = database.companies.find_one({"company_id": company_id})
        if not r:
            return None
        return {
            "company_id": r["company_id"],
            "company_name": r["company_name"],
            "code": r.get("code", ""),
            "is_active": bool(r.get("is_active", True)),
            "created_at": r.get("created_at", ""),
            "settings": r.get("settings", {})
        }

    @staticmethod
    def create(company_name: str, db: Optional[Database] = None) -> int:
        database = db if db is not None else get_db()
        # Find next available integer ID
        last = database.companies.find_one(sort=[("company_id", -1)])
        next_id = (last["company_id"] + 1) if last else 1
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "company_id": next_id,
            "company_name": company_name.strip(),
            "code": company_name.strip()[:3].upper(),
            "is_active": True,
            "created_at": now,
            "settings": {"currency": "USD"}
        }
        database.companies.insert_one(doc)
        return next_id

    @staticmethod
    def update(company_id: int, company_name: Optional[str] = None, is_active: Optional[bool] = None, db: Optional[Database] = None):
        database = db if db is not None else get_db()
        updates = {}
        if company_name is not None:
            updates["company_name"] = company_name.strip()
        if is_active is not None:
            updates["is_active"] = bool(is_active)
        if updates:
            database.companies.update_one({"company_id": company_id}, {"$set": updates})


class StoreRepository:

    @staticmethod
    def list_by_company(company_id: int, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        cursor = database.stores.find({"company_id": company_id}).sort("store_id", 1)
        return [
            {
                "store_id": r["store_id"],
                "company_id": r["company_id"],
                "store_name": r["store_name"],
                "code": r.get("code", ""),
                "location": r.get("location", ""),
                "city": r.get("city", ""),
                "state": r.get("state", ""),
                "is_active": bool(r.get("is_active", True)),
                "created_at": r.get("created_at", "")
            }
            for r in cursor
        ]

    @staticmethod
    def get_by_id(store_id: int, company_id: int, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        database = db if db is not None else get_db()
        r = database.stores.find_one({"store_id": store_id, "company_id": company_id})
        if not r:
            return None
        return {
            "store_id": r["store_id"],
            "company_id": r["company_id"],
            "store_name": r["store_name"],
            "code": r.get("code", ""),
            "location": r.get("location", ""),
            "city": r.get("city", ""),
            "state": r.get("state", ""),
            "is_active": bool(r.get("is_active", True)),
            "created_at": r.get("created_at", "")
        }

    @staticmethod
    def create(company_id: int, store_name: str, location: Optional[str] = None, city: Optional[str] = None, state: Optional[str] = None, db: Optional[Database] = None) -> int:
        database = db if db is not None else get_db()
        last = database.stores.find_one(sort=[("store_id", -1)])
        next_id = (last["store_id"] + 1) if last else 1
        now = datetime.now(timezone.utc).isoformat()
        doc = {
            "store_id": next_id,
            "company_id": company_id,
            "store_name": store_name.strip(),
            "code": f"STR-{next_id:02d}",
            "location": location or "",
            "city": city or "",
            "state": state or "",
            "is_active": True,
            "created_at": now
        }
        database.stores.insert_one(doc)
        return next_id

    @staticmethod
    def update(store_id: int, company_id: int, store_name: Optional[str] = None, location: Optional[str] = None, is_active: Optional[bool] = None, db: Optional[Database] = None):
        database = db if db is not None else get_db()
        updates = {}
        if store_name is not None:
            updates["store_name"] = store_name.strip()
        if location is not None:
            updates["location"] = location.strip()
        if is_active is not None:
            updates["is_active"] = bool(is_active)
        if updates:
            database.stores.update_one({"store_id": store_id, "company_id": company_id}, {"$set": updates})
