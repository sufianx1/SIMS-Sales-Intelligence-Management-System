"""
app/api/router.py
-----------------
Aggregates all API v1 domain sub-routers into a unified APIRouter instance.
"""

from fastapi import APIRouter
from app.api.routes import (
    health, auth, companies, stores, customers, products, orders,
    inventory, dashboard, analytics, imports, integrations
)

api_router = APIRouter()

# Core system routes
api_router.include_router(health.router)
api_router.include_router(auth.router)

# Multi-tenant and operational business routes
api_router.include_router(companies.router)
api_router.include_router(stores.router)
api_router.include_router(customers.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(inventory.router)

# Analytics, reporting, integrations, and ETL data import routes
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
api_router.include_router(imports.router)
api_router.include_router(integrations.router)
