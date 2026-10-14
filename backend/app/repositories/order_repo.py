"""
app/repositories/order_repo.py
------------------------------
MongoDB repository for Orders and line items, strictly scoped to CompanyID.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import date
from pymongo.database import Database
from app.db.mongo import get_db


class OrderRepository:

    @staticmethod
    def list(
        company_id: int,
        store_id: Optional[int] = None,
        customer_id: Optional[str] = None,
        region: Optional[str] = None,
        ship_mode: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 50,
        db: Optional[Database] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        database = db if db is not None else get_db()
        filter_doc: Dict[str, Any] = {"company_id": company_id}

        if store_id is not None and store_id != 0:
            filter_doc["store_id"] = int(store_id)

        if customer_id and customer_id != "All":
            filter_doc["customer_id"] = customer_id.strip()

        if region and region != "All":
            filter_doc["region"] = region.strip()

        if ship_mode and ship_mode != "All":
            filter_doc["ship_mode"] = ship_mode.strip()

        date_filter: Dict[str, Any] = {}
        if start_date:
            date_filter["$gte"] = str(start_date)
        if end_date:
            date_filter["$lte"] = str(end_date)
        if date_filter:
            filter_doc["order_date"] = date_filter

        if search:
            regex = {"$regex": search.strip(), "$options": "i"}
            filter_doc["$or"] = [{"order_id": regex}, {"customer_id": regex}]

        total = database.orders.count_documents(filter_doc)
        cursor = database.orders.find(filter_doc).sort("order_date", -1).skip(offset).limit(limit)

        items = []
        for o in cursor:
            # Look up customer name
            cust = database.customers.find_one({"company_id": company_id, "customer_id": o["customer_id"]})
            cust_name = cust["customer_name"] if cust else o.get("customer_name", o["customer_id"])

            # Look up store name
            st = database.stores.find_one({"company_id": company_id, "store_id": o.get("store_id")})
            store_name = st["store_name"] if st else None

            lines = o.get("lines", [])
            total_sales = o.get("total_sales")
            if total_sales is None:
                total_sales = sum(float(l.get("sales", 0.0)) for l in lines)
            total_qty = o.get("total_quantity")
            if total_qty is None:
                total_qty = sum(int(l.get("quantity", 1)) for l in lines)
            total_profit = o.get("total_profit")
            if total_profit is None:
                total_profit = sum(float(l.get("profit", 0.0)) for l in lines)

            items.append({
                "order_id": o["order_id"],
                "order_date": o.get("order_date", ""),
                "ship_date": o.get("ship_date"),
                "ship_mode": o.get("ship_mode"),
                "customer_id": o["customer_id"],
                "customer_name": cust_name,
                "company_id": o["company_id"],
                "store_id": o.get("store_id"),
                "store_name": store_name,
                "country": o.get("country", "United States"),
                "city": o.get("city", ""),
                "state": o.get("state", ""),
                "region": o.get("region", ""),
                "total_sales": round(float(total_sales), 2),
                "total_quantity": int(total_qty),
                "total_profit": round(float(total_profit), 2),
                "line_count": len(lines)
            })

        return items, total

    @staticmethod
    def get_by_id(company_id: int, order_id: str, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        database = db if db is not None else get_db()
        o = database.orders.find_one({"company_id": company_id, "order_id": order_id.strip()})
        if not o:
            return None

        cust = database.customers.find_one({"company_id": company_id, "customer_id": o["customer_id"]})
        cust_name = cust["customer_name"] if cust else o.get("customer_name", o["customer_id"])

        st = database.stores.find_one({"company_id": company_id, "store_id": o.get("store_id")})
        store_name = st["store_name"] if st else None

        lines = o.get("lines", [])
        total_sales = o.get("total_sales") or sum(float(l.get("sales", 0.0)) for l in lines)
        total_qty = o.get("total_quantity") or sum(int(l.get("quantity", 1)) for l in lines)
        total_profit = o.get("total_profit") or sum(float(l.get("profit", 0.0)) for l in lines)

        return {
            "order_id": o["order_id"],
            "order_date": o.get("order_date", ""),
            "ship_date": o.get("ship_date"),
            "ship_mode": o.get("ship_mode"),
            "customer_id": o["customer_id"],
            "customer_name": cust_name,
            "company_id": o["company_id"],
            "store_id": o.get("store_id"),
            "store_name": store_name,
            "country": o.get("country", "United States"),
            "city": o.get("city", ""),
            "state": o.get("state", ""),
            "region": o.get("region", ""),
            "total_sales": round(float(total_sales), 2),
            "total_quantity": int(total_qty),
            "total_profit": round(float(total_profit), 2),
            "line_count": len(lines)
        }

    @staticmethod
    def get_lines(order_id: str, company_id: Optional[int] = None, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        database = db if db is not None else get_db()
        query: Dict[str, Any] = {"order_id": order_id.strip()}
        if company_id is not None:
            query["company_id"] = company_id
        o = database.orders.find_one(query)
        if not o:
            return []

        results = []
        for idx, line in enumerate(o.get("lines", []), start=1):
            results.append({
                "order_detail_id": line.get("line_id", idx),
                "order_id": o["order_id"],
                "product_id": line["product_id"],
                "product_name": line.get("product_name", ""),
                "category": line.get("category", ""),
                "sub_category": line.get("sub_category", ""),
                "sales": round(float(line.get("sales", 0.0)), 2),
                "quantity": int(line.get("quantity", 1)),
                "discount": round(float(line.get("discount", 0.0)), 2),
                "profit": round(float(line.get("profit", 0.0)), 2)
            })
        return results

    @staticmethod
    def create_order(
        company_id: int,
        order_id: str,
        order_date: Any,
        ship_date: Optional[Any],
        ship_mode: Optional[str],
        customer_id: str,
        store_id: Optional[int],
        country: Optional[str] = "United States",
        city: Optional[str] = None,
        state: Optional[str] = None,
        postal_code: Optional[str] = None,
        region: Optional[str] = None,
        lines: Optional[List[Dict[str, Any]]] = None,
        db: Optional[Database] = None
    ):
        database = db if db is not None else get_db()
        lines_list = lines or []
        tot_sales = sum(float(l.get("sales", 0.0)) for l in lines_list)
        tot_qty = sum(int(l.get("quantity", 1)) for l in lines_list)
        tot_profit = sum(float(l.get("profit", 0.0)) for l in lines_list)

        doc = {
            "order_id": order_id.strip(),
            "company_id": company_id,
            "order_date": str(order_date),
            "ship_date": str(ship_date) if ship_date else None,
            "ship_mode": ship_mode,
            "customer_id": customer_id.strip(),
            "store_id": int(store_id) if store_id else None,
            "country": country or "United States",
            "city": city or "",
            "state": state or "",
            "postal_code": postal_code or "",
            "region": region or "",
            "lines": lines_list,
            "total_sales": round(tot_sales, 2),
            "total_quantity": tot_qty,
            "total_profit": round(tot_profit, 2)
        }
        database.orders.update_one(
            {"company_id": company_id, "order_id": order_id.strip()},
            {"$set": doc},
            upsert=True
        )

    @staticmethod
    def update(
        company_id: int,
        order_id: str,
        ship_date: Optional[Any] = None,
        ship_mode: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        region: Optional[str] = None,
        db: Optional[Database] = None
    ):
        database = db if db is not None else get_db()
        updates = {}
        if ship_date is not None:
            updates["ship_date"] = str(ship_date)
        if ship_mode is not None:
            updates["ship_mode"] = ship_mode
        if city is not None:
            updates["city"] = city
        if state is not None:
            updates["state"] = state
        if region is not None:
            updates["region"] = region

        if updates:
            database.orders.update_one(
                {"company_id": company_id, "order_id": order_id.strip()},
                {"$set": updates}
            )

    @staticmethod
    def delete(company_id: int, order_id: str, db: Optional[Database] = None):
        database = db if db is not None else get_db()
        database.orders.delete_one({"company_id": company_id, "order_id": order_id.strip()})
