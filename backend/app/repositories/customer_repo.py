"""
app/repositories/customer_repo.py
---------------------------------
MongoDB repository for Customer entity operations, strictly scoped to CompanyID.
"""

from typing import Optional, List, Dict, Any, Tuple
from pymongo.database import Database
from app.db.mongo import get_db


class CustomerRepository:

    @staticmethod
    def list(
        company_id: int,
        search: Optional[str] = None,
        segment: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
        db: Optional[Database] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        database = db if db is not None else get_db()
        filter_doc: Dict[str, Any] = {"company_id": company_id}

        if search:
            regex = {"$regex": search.strip(), "$options": "i"}
            filter_doc["$or"] = [{"customer_name": regex}, {"customer_id": regex}]

        if segment and segment != "All":
            filter_doc["segment"] = segment.strip()

        total = database.customers.count_documents(filter_doc)
        cursor = database.customers.find(filter_doc).skip(offset).limit(limit)

        items = []
        for c in cursor:
            # Aggregate orders for this customer in this company
            pipeline = [
                {"$match": {"company_id": company_id, "customer_id": c["customer_id"]}},
                {"$group": {
                    "_id": None,
                    "total_orders": {"$sum": 1},
                    "total_sales": {"$sum": "$total_sales"},
                    "total_profit": {"$sum": "$total_profit"}
                }}
            ]
            agg = list(database.orders.aggregate(pipeline))
            stats = agg[0] if agg else {"total_orders": 0, "total_sales": 0.0, "total_profit": 0.0}

            items.append({
                "customer_id": c["customer_id"],
                "customer_name": c["customer_name"],
                "segment": c.get("segment", "Consumer"),
                "company_id": c["company_id"],
                "total_orders": stats["total_orders"],
                "total_sales": round(float(stats.get("total_sales", 0.0)), 2),
                "total_profit": round(float(stats.get("total_profit", 0.0)), 2)
            })

        return items, total

    @staticmethod
    def get_by_id(company_id: int, customer_id: str, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        database = db if db is not None else get_db()
        c = database.customers.find_one({"company_id": company_id, "customer_id": customer_id.strip()})
        if not c:
            return None

        pipeline = [
            {"$match": {"company_id": company_id, "customer_id": customer_id.strip()}},
            {"$group": {
                "_id": None,
                "total_orders": {"$sum": 1},
                "total_sales": {"$sum": "$total_sales"},
                "total_profit": {"$sum": "$total_profit"}
            }}
        ]
        agg = list(database.orders.aggregate(pipeline))
        stats = agg[0] if agg else {"total_orders": 0, "total_sales": 0.0, "total_profit": 0.0}

        return {
            "customer_id": c["customer_id"],
            "customer_name": c["customer_name"],
            "segment": c.get("segment", "Consumer"),
            "company_id": c["company_id"],
            "total_orders": stats["total_orders"],
            "total_sales": round(float(stats.get("total_sales", 0.0)), 2),
            "total_profit": round(float(stats.get("total_profit", 0.0)), 2)
        }

    @staticmethod
    def get_order_history(company_id: int, customer_id: str, limit: int = 50, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        cursor = database.orders.find(
            {"company_id": company_id, "customer_id": customer_id.strip()}
        ).sort("order_date", -1).limit(limit)

        results = []
        for o in cursor:
            for line in o.get("lines", []):
                results.append({
                    "order_id": o["order_id"],
                    "order_date": o.get("order_date", ""),
                    "product_name": line.get("product_name", ""),
                    "category": line.get("category", ""),
                    "sales": round(float(line.get("sales", 0.0)), 2),
                    "quantity": int(line.get("quantity", 1)),
                    "profit": round(float(line.get("profit", 0.0)), 2)
                })
        return results

    @staticmethod
    def create(company_id: int, customer_id: str, customer_name: str, segment: Optional[str] = None, db: Optional[Database] = None):
        database = db if db is not None else get_db()
        doc = {
            "customer_id": customer_id.strip(),
            "customer_name": customer_name.strip(),
            "segment": segment or "Consumer",
            "company_id": company_id,
            "is_active": True
        }
        database.customers.update_one(
            {"company_id": company_id, "customer_id": customer_id.strip()},
            {"$set": doc},
            upsert=True
        )

    @staticmethod
    def update(company_id: int, customer_id: str, customer_name: Optional[str] = None, segment: Optional[str] = None, db: Optional[Database] = None):
        database = db if db is not None else get_db()
        updates = {}
        if customer_name is not None:
            updates["customer_name"] = customer_name.strip()
        if segment is not None:
            updates["segment"] = segment.strip()
        if updates:
            database.customers.update_one(
                {"company_id": company_id, "customer_id": customer_id.strip()},
                {"$set": updates}
            )
