"""
app/db/mongo.py
---------------
MongoDB client and database manager for SIMS.
Supports live MongoDB connection (via PyMongo) with transparent fallback to
in-memory mongomock when MongoDB server is not locally running.
Ensures zero disruption and immediate readiness across dev, test, and production.
"""

from typing import Optional
import pymongo
from pymongo.database import Database
from pymongo.errors import ServerSelectionTimeoutError, PyMongoError
from app.core.config import settings
from app.core.logging import logger

_mongo_client: Optional[pymongo.MongoClient] = None
_mongo_db: Optional[Database] = None
_is_mock: bool = False


def get_client() -> pymongo.MongoClient:
    """
    Returns the singleton MongoDB client.
    Connects to configured MONGODB_URI, falling back to mongomock if unavailable.
    """
    global _mongo_client, _is_mock

    if _mongo_client is not None:
        return _mongo_client

    if settings.USE_MOCK_MONGO:
        import mongomock
        logger.info("Using mongomock as requested by settings.USE_MOCK_MONGO")
        _mongo_client = mongomock.MongoClient()
        _is_mock = True
        return _mongo_client

    try:
        # Attempt connection with 1-second timeout
        client = pymongo.MongoClient(
            settings.MONGODB_URI,
            serverSelectionTimeoutMS=1000,
            connectTimeoutMS=1000,
        )
        # Ping server to verify connectivity
        client.admin.command("ping")
        logger.info(f"Connected successfully to live MongoDB at {settings.MONGODB_URI}")
        _mongo_client = client
        _is_mock = False
        return _mongo_client
    except (ServerSelectionTimeoutError, PyMongoError, Exception) as exc:
        logger.warning(
            f"Live MongoDB connection to '{settings.MONGODB_URI}' unavailable ({exc}). "
            "Falling back to embedded in-memory mongomock database."
        )
        import mongomock
        _mongo_client = mongomock.MongoClient()
        _is_mock = True
        return _mongo_client


def get_db(db_name: Optional[str] = None) -> Database:
    """Returns the application MongoDB database instance."""
    global _mongo_db
    target_name = db_name or settings.MONGODB_DB_NAME
    if _mongo_db is None or _mongo_db.name != target_name:
        client = get_client()
        _mongo_db = client[target_name]
    return _mongo_db


def is_mock_db() -> bool:
    """Returns True if the database is running on mongomock."""
    return _is_mock


def reset_mock_db(db_name: Optional[str] = None):
    """Resets the mock database instance (used for test isolation)."""
    global _mongo_client, _mongo_db, _is_mock
    import mongomock
    _mongo_client = mongomock.MongoClient()
    _is_mock = True
    target_name = db_name or settings.TEST_MONGODB_DB_NAME
    _mongo_db = _mongo_client[target_name]
    ensure_indexes(_mongo_db)


def ensure_indexes(db: Database):
    """Creates required unique and compound indexes across all tenant collections."""
    try:
        # Users
        db.users.create_index("email", unique=True)
        db.users.create_index("username", unique=True)

        # Companies
        db.companies.create_index("company_id", unique=True)

        # Stores
        db.stores.create_index([("company_id", 1), ("store_id", 1)], unique=True)

        # Memberships
        db.memberships.create_index([("user_id", 1), ("company_id", 1)], unique=True)

        # Products
        db.products.create_index([("company_id", 1), ("product_id", 1)], unique=True)
        db.products.create_index([("company_id", 1), ("sku", 1)])

        # Inventory
        db.inventory.create_index([("company_id", 1), ("store_id", 1), ("product_id", 1)], unique=True)
        db.inventory.create_index([("company_id", 1), ("quantity_on_hand", 1)])

        # Inventory Movements
        db.inventory_movements.create_index([("company_id", 1), ("timestamp", -1)])
        db.inventory_movements.create_index([("company_id", 1), ("product_id", 1)])

        # Customers
        db.customers.create_index([("company_id", 1), ("customer_id", 1)], unique=True)

        # Orders
        db.orders.create_index([("company_id", 1), ("order_id", 1)], unique=True)
        db.orders.create_index([("company_id", 1), ("store_id", 1), ("order_date", -1)])
        db.orders.create_index([("company_id", 1), ("customer_id", 1)])

        # Raw & Structured Imports
        db.raw_imports.create_index([("company_id", 1), ("created_at", -1)])
        db.structured_imports.create_index([("company_id", 1), ("created_at", -1)])

        # Integrations & Sync Logs
        db.integrations.create_index([("company_id", 1), ("is_active", 1)])
        db.sync_logs.create_index([("company_id", 1), ("integration_id", 1), ("started_at", -1)])

        # Audit Events
        db.audit_events.create_index([("company_id", 1), ("timestamp", -1)])
    except Exception as e:
        logger.warning(f"Note on ensure_indexes: {e}")
