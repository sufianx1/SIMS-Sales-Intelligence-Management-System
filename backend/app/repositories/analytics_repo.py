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
        total_orders = int(orders_stat["total_orders"])
        average_order_value = round((total_sales / total_orders), 2) if total_orders > 0 else 0.0

        return {
            "total_sales": total_sales,
            "total_profit": total_profit,
            "profit_margin": profit_margin,
            "total_orders": total_orders,
            "average_order_value": average_order_value,
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
    def get_profit_by_category(company_id: int, store_id: Optional[int] = None, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        """Calculates category profit sorted by total profit."""
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
            {"$sort": {"total_profit": -1}}
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

    @staticmethod
    def get_explainable_insights(company_id: int, store_id: Optional[int] = None, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        """
        Generates deterministic, rule-based explainable business insights strictly scoped to the active tenant.
        Each insight provides:
        - Why it was generated (explanation)
        - The underlying supporting records/metrics (supporting_data)
        - Inherent limitations of the calculation (limitations)
        - Practical next step (recommended_action)
        """
        database = db if db is not None else get_db()
        insights = []

        # 1. Stockout & Low Stock Risks (Inventory Alerts)
        inv_filter: Dict[str, Any] = {"company_id": company_id}
        if store_id is not None and store_id != 0:
            inv_filter["store_id"] = int(store_id)

        stores_map = {s["store_id"]: s.get("store_name", f"Store {s['store_id']}") for s in database.stores.find({"company_id": company_id})}
        prods_map = {p["product_id"]: p.get("product_name", p["product_id"]) for p in database.products.find({"company_id": company_id})}

        critical_stock = list(database.inventory.find({**inv_filter, "quantity_on_hand": 0}).limit(3))
        for item in critical_stock:
            pid = item.get("product_id", "")
            sid = item.get("store_id", 0)
            pname = prods_map.get(pid, pid)
            sname = stores_map.get(sid, f"Store {sid}")
            insights.append({
                "insight_id": f"INS-STOCK-CRIT-{pid}-{sid}",
                "category": "INVENTORY_ALERT",
                "severity": "CRITICAL",
                "title": f"Stockout Alert: {pname}",
                "summary": f"{pname} is completely out of stock at {sname}.",
                "explanation": f"Quantity on hand reached 0 at {sname}, creating fulfillment delays and lost sales opportunities.",
                "supporting_data": {
                    "product_id": pid,
                    "product_name": pname,
                    "store_id": sid,
                    "store_name": sname,
                    "quantity_on_hand": 0,
                    "min_threshold": item.get("min_threshold", 5)
                },
                "limitations": "Evaluates current recorded stock snapshot; does not account for purchase orders in transit.",
                "recommended_action": "Execute an immediate inter-store stock transfer or issue a supplier restocking receipt."
            })

        low_stock = list(database.inventory.find({
            **inv_filter,
            "quantity_on_hand": {"$gt": 0},
            "$expr": {"$lte": ["$quantity_on_hand", "$min_threshold"]}
        }).limit(3))
        for item in low_stock:
            pid = item.get("product_id", "")
            sid = item.get("store_id", 0)
            pname = prods_map.get(pid, pid)
            sname = stores_map.get(sid, f"Store {sid}")
            qty = item.get("quantity_on_hand", 0)
            thresh = item.get("min_threshold", 5)
            insights.append({
                "insight_id": f"INS-STOCK-LOW-{pid}-{sid}",
                "category": "INVENTORY_ALERT",
                "severity": "WARNING",
                "title": f"Low Stock Warning: {pname}",
                "summary": f"{pname} stock ({qty} units) is at or below minimum threshold ({thresh} units).",
                "explanation": f"Inventory level is {qty} units which is at or below the safety stock threshold of {thresh} units.",
                "supporting_data": {
                    "product_id": pid,
                    "product_name": pname,
                    "store_id": sid,
                    "store_name": sname,
                    "quantity_on_hand": qty,
                    "min_threshold": thresh
                },
                "limitations": "Safety stock threshold is static; does not incorporate lead-time variability.",
                "recommended_action": f"Reorder additional stock from supplier or rebalance from branches with surplus."
            })

        # 2. Category Profit Margin & Performance
        cat_sales = AnalyticsRepository.get_sales_by_category(company_id, store_id, db=database)
        cat_profit = AnalyticsRepository.get_profit_by_category(company_id, store_id, db=database)
        profit_map = {c["category"]: c["total_profit"] for c in cat_profit}

        for c in cat_sales:
            cat_name = c["category"]
            c_sales = float(c["total_sales"])
            c_profit = float(profit_map.get(cat_name, 0.0))
            c_margin = round((c_profit / c_sales * 100), 1) if c_sales > 0 else 0.0

            if c_margin < 15.0 and c_sales > 0:
                insights.append({
                    "insight_id": f"INS-CAT-MARGIN-{cat_name.replace(' ', '_')}",
                    "category": "CATEGORY_PERFORMANCE",
                    "severity": "WARNING",
                    "title": f"Underperforming Margin: {cat_name}",
                    "summary": f"{cat_name} margin is {c_margin}%, below the 15% target.",
                    "explanation": f"The '{cat_name}' product category achieved ${c_sales:,.2f} in revenue but only generated ${c_profit:,.2f} in profit, resulting in a low margin of {c_margin}%.",
                    "supporting_data": {
                        "category": cat_name,
                        "total_sales": c_sales,
                        "total_profit": c_profit,
                        "profit_margin_pct": c_margin,
                        "benchmark_target_pct": 15.0
                    },
                    "limitations": "Aggregated from settled orders only; excludes uncaptured discounts or returns.",
                    "recommended_action": "Negotiate lower wholesale vendor costs or review high-discount promotion policies."
                })

        # 3. Revenue Concentration Risk
        top_prods = AnalyticsRepository.get_top_products(company_id, store_id, limit=3, db=database)
        kpis = AnalyticsRepository.get_dashboard_metrics(company_id, store_id, db=database)
        total_sales = float(kpis.get("total_sales", 0.0))

        if total_sales > 0 and top_prods:
            top_sku = top_prods[0]
            top_sku_sales = float(top_sku.get("total_sales", 0.0))
            pct_contrib = round((top_sku_sales / total_sales * 100), 1)
            if pct_contrib >= 30.0:
                insights.append({
                    "insight_id": "INS-CONCENTRATION-TOP-SKU",
                    "category": "CONCENTRATION_RISK",
                    "severity": "INFO",
                    "title": f"Revenue Concentration: {top_sku['product_name'][:30]}",
                    "summary": f"Top SKU contributes {pct_contrib}% of total company revenue.",
                    "explanation": f"A single product ('{top_sku['product_name']}') generated ${top_sku_sales:,.2f} out of ${total_sales:,.2f} total sales ({pct_contrib}%).",
                    "supporting_data": {
                        "product_name": top_sku["product_name"],
                        "product_sales": top_sku_sales,
                        "total_sales": total_sales,
                        "contribution_pct": pct_contrib
                    },
                    "limitations": "Evaluates sales volume across available order history.",
                    "recommended_action": "Expand promotional focus across secondary SKUs to mitigate revenue concentration."
                })

        # 4. Overall Operational Health Summary (if no critical alerts)
        if not insights:
            insights.append({
                "insight_id": "INS-HEALTH-NOMINAL",
                "category": "OPERATIONAL_HEALTH",
                "severity": "INFO",
                "title": "Operations Nominal",
                "summary": "All inventory levels, category margins, and store operations within normal parameters.",
                "explanation": "No critical stockouts or severe margin anomalies detected for the active tenant scope.",
                "supporting_data": {
                    "total_orders": kpis.get("total_orders", 0),
                    "total_sales": total_sales,
                    "profit_margin": kpis.get("profit_margin", 0.0)
                },
                "limitations": "Based on current database records and configured alert thresholds.",
                "recommended_action": "Continue regular monitoring and periodic inventory cycle counts."
            })

        return insights
