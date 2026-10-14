"""
app/services/company_service.py
-------------------------------
Business service for managing companies and stores with MongoDB.
"""

from typing import List, Optional
from fastapi import HTTPException, status
from app.db.mongo import get_db
from app.repositories.company_repo import CompanyRepository, StoreRepository
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, StoreCreate, StoreUpdate, StoreResponse


class CompanyService:

    @staticmethod
    def list_companies() -> List[CompanyResponse]:
        rows = CompanyRepository.list_all()
        return [CompanyResponse(**r) for r in rows]

    @staticmethod
    def get_company(company_id: int) -> CompanyResponse:
        row = CompanyRepository.get_by_id(company_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        return CompanyResponse(**row)

    @staticmethod
    def create_company(data: CompanyCreate) -> CompanyResponse:
        db = get_db()
        existing = db.companies.find_one({"company_name": {"$regex": f"^{data.company_name.strip()}$", "$options": "i"}})
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Company name already registered")
        comp_id = CompanyRepository.create(data.company_name)
        return CompanyResponse(company_id=comp_id, company_name=data.company_name.strip(), is_active=True)

    @staticmethod
    def update_company(company_id: int, data: CompanyUpdate) -> CompanyResponse:
        row = CompanyRepository.get_by_id(company_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Company not found")
        CompanyRepository.update(company_id, data.company_name, data.is_active)
        updated = CompanyRepository.get_by_id(company_id)
        return CompanyResponse(**updated)

    @staticmethod
    def list_stores(company_id: int) -> List[StoreResponse]:
        rows = StoreRepository.list_by_company(company_id)
        return [StoreResponse(**r) for r in rows]

    @staticmethod
    def get_store(company_id: int, store_id: int) -> StoreResponse:
        row = StoreRepository.get_by_id(store_id, company_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found in company")
        return StoreResponse(**row)

    @staticmethod
    def create_store(company_id: int, data: StoreCreate) -> StoreResponse:
        db = get_db()
        existing = db.stores.find_one({
            "company_id": company_id,
            "store_name": {"$regex": f"^{data.store_name.strip()}$", "$options": "i"}
        })
        if existing:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Store name already exists for this company")
        store_id = StoreRepository.create(company_id, data.store_name, data.location)
        return StoreResponse(
            store_id=store_id,
            company_id=company_id,
            store_name=data.store_name.strip(),
            location=data.location,
            is_active=True
        )

    @staticmethod
    def update_store(company_id: int, store_id: int, data: StoreUpdate) -> StoreResponse:
        row = StoreRepository.get_by_id(store_id, company_id)
        if not row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found in company")
        StoreRepository.update(store_id, company_id, data.store_name, data.location, data.is_active)
        updated = StoreRepository.get_by_id(store_id, company_id)
        return StoreResponse(**updated)
