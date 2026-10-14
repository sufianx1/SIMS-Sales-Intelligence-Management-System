"""
app/repositories/user_repo.py
-----------------------------
MongoDB data access repository for users, tenant memberships, and RBAC permissions.
"""

from typing import Optional, List, Dict, Any
from pymongo.database import Database
from app.db.mongo import get_db


class UserRepository:

    @staticmethod
    def get_by_identifier(identifier: str, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        """Finds user by normalized email or username."""
        database = db if db is not None else get_db()
        clean_id = identifier.strip().lower()
        user = database.users.find_one({
            "$or": [
                {"email": {"$regex": f"^{clean_id}$", "$options": "i"}},
                {"username": {"$regex": f"^{clean_id}$", "$options": "i"}}
            ]
        })
        if not user:
            return None
        return {
            "user_id": user["user_id"],
            "username": user.get("username", ""),
            "name": user["name"],
            "email": user["email"],
            "password_hash": user["password_hash"],
            "is_active": bool(user.get("is_active", True)),
            "is_system_admin": bool(user.get("is_system_admin", False))
        }

    @staticmethod
    def get_by_email(email: str, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        """Finds user by email or username."""
        return UserRepository.get_by_identifier(email, db)

    @staticmethod
    def get_by_id(user_id: int, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        """Finds user by user_id."""
        database = db if db is not None else get_db()
        user = database.users.find_one({"user_id": user_id})
        if not user:
            return None
        return {
            "user_id": user["user_id"],
            "username": user.get("username", ""),
            "name": user["name"],
            "email": user["email"],
            "password_hash": user["password_hash"],
            "is_active": bool(user.get("is_active", True)),
            "is_system_admin": bool(user.get("is_system_admin", False))
        }

    @staticmethod
    def get_memberships(user_id: int, is_system_admin: bool = False, db: Optional[Database] = None) -> List[Dict[str, Any]]:
        """
        Fetches all active company memberships, assigned stores, roles,
        and permissions for a user.
        If user is a Platform Admin, includes all active companies with full permissions.
        """
        database = db if db is not None else get_db()
        memberships: List[Dict[str, Any]] = []

        all_permissions = [
            "view_dashboard", "manage_orders", "view_orders", "manage_customers", "view_customers",
            "manage_products", "view_products", "manage_inventory", "view_inventory",
            "inventory_transfer", "inventory_adjust", "manage_stores", "view_stores",
            "view_analytics", "import_data", "manage_integrations", "manage_users"
        ]

        if is_system_admin:
            active_companies = database.companies.find({"is_active": True}).sort("company_name", 1)
            for comp in active_companies:
                comp_id = comp["company_id"]
                comp_name = comp["company_name"]
                # Check if specific user assignment exists
                assign = database.memberships.find_one({"user_id": user_id, "company_id": comp_id, "is_active": True})
                memberships.append({
                    "company_id": comp_id,
                    "company_name": comp_name,
                    "role_id": assign["role_id"] if assign else 1,
                    "role_name": assign["role_name"] if assign else "Platform Admin",
                    "store_id": assign.get("store_id") if assign else None,
                    "store_name": assign.get("store_name") if assign else None,
                    "permissions": all_permissions
                })
            return memberships

        # Standard tenant memberships
        cursor = database.memberships.find({"user_id": user_id, "is_active": True})
        for m in cursor:
            # Check company is active
            comp = database.companies.find_one({"company_id": m["company_id"]})
            if not comp or not comp.get("is_active", True):
                continue

            memberships.append({
                "company_id": m["company_id"],
                "company_name": m.get("company_name", comp["company_name"]),
                "role_id": m["role_id"],
                "role_name": m.get("role_name", "Member"),
                "store_id": m.get("store_id"),
                "store_name": m.get("store_name"),
                "permissions": m.get("permissions", [])
            })

        return sorted(memberships, key=lambda x: x["company_name"])

    @staticmethod
    def get_tenant_membership(user_id: int, company_id: int, db: Optional[Database] = None) -> Optional[Dict[str, Any]]:
        """Returns specific user membership for a tenant."""
        database = db if db is not None else get_db()
        m = database.memberships.find_one({"user_id": user_id, "company_id": company_id, "is_active": True})
        if not m:
            return None

        comp = database.companies.find_one({"company_id": company_id})
        if not comp or not comp.get("is_active", True):
            return None

        return {
            "company_id": m["company_id"],
            "company_name": m.get("company_name", comp["company_name"]),
            "role_id": m["role_id"],
            "role_name": m.get("role_name", "Member"),
            "store_id": m.get("store_id"),
            "store_name": m.get("store_name"),
            "permissions": m.get("permissions", [])
        }
