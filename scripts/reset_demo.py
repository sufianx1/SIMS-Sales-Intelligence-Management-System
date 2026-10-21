#!/usr/bin/env python3
"""
scripts/reset_demo.py
---------------------
Administrative utility to reset the SIMS database to clean demo state.
Connects using active configuration (real MongoDB or mongomock) and re-seeds:
- 3 Demo Companies (Superstore, Nike, Puma)
- 6 Stores across NY, Chicago, LA, Portland, etc.
- 7 Demo Users (Platform Superadmin + Company Admin & Employee per tenant)
- Master product catalog with pricing and cost basis
- Multi-store inventory levels with low-stock alerts
- Baseline orders with line items
- Customer directories
- POS / E-Commerce integration connectors & sync audit logs

Usage:
    python scripts/reset_demo.py [--force]
"""

import sys
import os

# Add backend directory to path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.db.mongo import get_db, is_mock_db
from app.db.seed import seed_database


def reset_demo():
    print("=" * 65)
    print("SIMS - DEMO ENVIRONMENT RESET UTILITY")
    print("=" * 65)

    db = get_db()
    is_mock = is_mock_db()
    target_db_name = settings.MONGODB_DB_NAME

    print(f"Target Database Engine : {'mongomock (in-memory)' if is_mock else 'Persistent MongoDB'}")
    print(f"Target Database Name   : {target_db_name}")
    print(f"Environment Mode       : {settings.ENVIRONMENT}")
    print("-" * 65)

    if settings.ENVIRONMENT.lower() in ("production", "staging"):
        print("ERROR: Demo reset cannot be run in production or staging environments.")
        sys.exit(1)

    print("Re-seeding collections with pristine demo data...")
    seed_database(db, force=True)

    # Verification counts
    companies = db.companies.count_documents({})
    stores = db.stores.count_documents({})
    users = db.users.count_documents({})
    products = db.products.count_documents({})
    orders = db.orders.count_documents({})
    customers = db.customers.count_documents({})
    inventory = db.inventory.count_documents({})
    integrations = db.integrations.count_documents({})

    print("-" * 65)
    print(f"Companies seeded   : {companies}")
    print(f"Stores seeded      : {stores}")
    print(f"Users seeded       : {users}")
    print(f"Products seeded    : {products}")
    print(f"Inventory records  : {inventory}")
    print(f"Orders seeded      : {orders}")
    print(f"Customers seeded   : {customers}")
    print(f"Integrations seeded: {integrations}")
    print("=" * 65)
    print("SUCCESS: SIMS demo environment successfully reset.")
    print("=" * 65)


if __name__ == "__main__":
    reset_demo()
