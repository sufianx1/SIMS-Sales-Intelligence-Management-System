"""
app/repositories/analytics_repo.py
----------------------------------
Analytical MongoDB aggregation pipelines for Dashboard, Multi-Dimensional Sales Analysis,
and Store-level vs Company-wide comparisons.
Strictly scoped to CompanyID (and optional StoreID).
"""

from typing import Optional, List, Dict, Any
from datetime import date
from pymongo.database import Database
from app.db.mongo import get_db


class AnalyticsRepository:

    @staticmethod
    def get_dashboard_metrics(company_id: int, store_id: Optional[int] = None, db: Optional[Database] = None) -> Dict[str, Any]:
        """Calculates key dashboard metrics strictly scoped to CompanyID and optional StoreID."""
        database = db if db is not None else get_db()
        match_filter: Dict[str, Any] = {"company_id": company_id}
        if store_id is not None and store_id != 0:
            match_filter["store_id"] = int(store_id)

        # 1. Total Sales, Total Profit, Total Units Sold from Orders
        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": None,
                "total_sales": {"$sum": "$total_sales"},
                "total_profit": {"$sum": "$total_profit"},
                "total_units": {"$sum": "$total_quantity"},
                "total_orders": {"$sum": 1}
            }}
        ]
        agg = list(database.orders.aggregate(pipeline))
        orders_stat = agg[0] if agg else {
            "total_sales": 0.0,
            "total_profit": 0.0,
            "total_units": 0,
            "total_orders": 0
        }

        # 2. Total Customers
        total_customers = database.customers.count_documents({"company_id": company_id})

        # 3. Total Products in Catalog
        total_products = database.products.count_documents({"company_id": company_id})

        # 4. Active Stores
        active_stores = database.stores.count_documents({"company_id": company_id, "is_active": True})

        # 5. Inventory on Hand, Low Stock, and Out of Stock
        inv_filter: Dict[str, Any] = {"company_id": company_id}
        if store_id is not None and store_id != 0:
            inv_filter["store_id"] = int(store_id)

        inv_cursor = database.inventory.find(inv_filter)
        total_inventory_units = 0
        low_stock_count = 0
        out_of_stock_count = 0
        for item in inv_cursor:
            qty = item.get("quantity_on_hand", 0)
            min_thresh = item.get("min_threshold", 5)
            total_inventory_units += qty
            if qty == 0:
                out_of_stock_count += 1
            elif qty <= min_thresh:
                low_stock_count += 1

        total_sales = round(float(orders_stat["total_sales"]), 2)
        total_profit = round(float(orders_stat["total_profit"]), 2)
        profit_margin = round((total_profit / total_sales * 100), 2) if total_sales > 0 else 0.0

        return {
            "total_sales": total_sales,
            "total_profit": total_profit,
            "profit_margin": profit_margin,
            "total_orders": int(orders_stat["total_orders"]),
            "total_units": int(orders_stat["total_units"]),
            "total_customers": int(total_customers),
            "total_products": int(total_products),
            "active_stores": int(active_stores),
            "inventory_on_hand": total_inventory_units,
            "low_stock_items": low_stock_count,
            "out_of_stock_items": out_of_stock_count
        }

    @staticmethod
    def get_sales_by_category(company_id: int, store_id: Optional[int] = None, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        match_filter: Dict[str, Any] = {"company_id": company_id}
        if store_id is not None and store_id != 0:
            match_filter["store_id"] = int(store_id)

        pipeline = [
            {"$match": match_filter},
            {"$unwind": "$lines"},
            {"$group": {
                "_id": {"$ifNull": ["$lines.category", "Uncategorized"]},
                "total_sales": {"$sum": "$lines.sales"},
                "total_profit": {"$sum": "$lines.profit"}
            }},
            {"$sort": {"total_sales": -1}}
        ]
        results = []
        for r in database.orders.aggregate(pipeline):
            results.append({
                "category": r["_id"],
                "total_sales": round(float(r["total_sales"]), 2),
                "total_profit": round(float(r["total_profit"]), 2)
            })
        return results

    @staticmethod
    def get_sales_by_region(company_id: int, store_id: Optional[int] = None, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        match_filter: Dict[str, Any] = {"company_id": company_id}
        if store_id is not None and store_id != 0:
            match_filter["store_id"] = int(store_id)

        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": {"$ifNull": ["$region", "Unknown"]},
                "total_sales": {"$sum": "$total_sales"},
                "total_profit": {"$sum": "$total_profit"}
            }},
            {"$sort": {"total_sales": -1}}
        ]
        results = []
        for r in database.orders.aggregate(pipeline):
            results.append({
                "region": r["_id"],
                "total_sales": round(float(r["total_sales"]), 2),
                "total_profit": round(float(r["total_profit"]), 2)
            })
        return results

    @staticmethod
    def get_sales_by_store(company_id: int, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        """Compares performance across stores within the authorized company."""
        database = db if db is not None else get_db()
        stores = {s["store_id"]: s["store_name"] for s in database.stores.find({"company_id": company_id})}

        pipeline = [
            {"$match": {"company_id": company_id}},
            {"$group": {
                "_id": "$store_id",
                "total_sales": {"$sum": "$total_sales"},
                "total_profit": {"$sum": "$total_profit"},
                "total_orders": {"$sum": 1}
            }},
            {"$sort": {"total_sales": -1}}
        ]
        results = []
        for r in database.orders.aggregate(pipeline):
            s_id = r["_id"]
            results.append({
                "store_id": s_id,
                "store_name": stores.get(s_id, f"Store #{s_id}" if s_id else "Online / Central"),
                "total_sales": round(float(r["total_sales"]), 2),
                "total_profit": round(float(r["total_profit"]), 2),
                "total_orders": int(r["total_orders"])
            })
        return results

    @staticmethod
    def get_top_products(company_id: int, store_id: Optional[int] = None, limit: int = 10, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        match_filter: Dict[str, Any] = {"company_id": company_id}
        if store_id is not None and store_id != 0:
            match_filter["store_id"] = int(store_id)

        pipeline = [
            {"$match": match_filter},
            {"$unwind": "$lines"},
            {"$group": {
                "_id": "$lines.product_name",
                "total_sales": {"$sum": "$lines.sales"}
            }},
            {"$sort": {"total_sales": -1}},
            {"$limit": limit}
        ]
        return [{"product_name": r["_id"] or "Unknown", "total_sales": round(float(r["total_sales"]), 2)} for r in database.orders.aggregate(pipeline)]

    @staticmethod
    def get_top_customers(company_id: int, store_id: Optional[int] = None, limit: int = 10, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        match_filter: Dict[str, Any] = {"company_id": company_id}
        if store_id is not None and store_id != 0:
            match_filter["store_id"] = int(store_id)

        pipeline = [
            {"$match": match_filter},
            {"$group": {
                "_id": "$customer_id",
                "total_sales": {"$sum": "$total_sales"}
            }},
            {"$sort": {"total_sales": -1}},
            {"$limit": limit}
        ]
        results = []
        for r in database.orders.aggregate(pipeline):
            cust_id = r["_id"]
            cust = database.customers.find_one({"company_id": company_id, "customer_id": cust_id})
            name = cust["customer_name"] if cust else cust_id
            results.append({"customer_name": name, "total_sales": round(float(r["total_sales"]), 2)})
        return results

    @staticmethod
    def get_monthly_trends(
        company_id: int,
        store_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        db: Optional[Database] = None
    ) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        match_filter: Dict[str, Any] = {"company_id": company_id}
        if store_id is not None and store_id != 0:
            match_filter["store_id"] = int(store_id)

        date_filter: Dict[str, Any] = {}
        if start_date:
            date_filter["$gte"] = str(start_date)
        if end_date:
            date_filter["$lte"] = str(end_date)
        if date_filter:
            match_filter["order_date"] = date_filter

        pipeline = [
            {"$match": match_filter},
            {"$project": {
                "month": {"$substr": ["$order_date", 0, 7]},
                "total_sales": 1,
                "total_profit": 1
            }},
            {"$group": {
                "_id": "$month",
                "sales": {"$sum": "$total_sales"},
                "profit": {"$sum": "$total_profit"}
            }},
            {"$sort": {"_id": 1}}
        ]
        results = []
        for r in database.orders.aggregate(pipeline):
            results.append({
                "month": r["_id"] or "N/A",
                "sales": round(float(r["sales"]), 2),
                "profit": round(float(r["profit"]), 2)
            })
        return results
