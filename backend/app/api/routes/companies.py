"""
app/api/routes/companies.py
---------------------------
Endpoints for Company (Tenant) administration.
"""

from typing import List
from fastapi import APIRouter, Depends, status
from app.api.dependencies import get_current_user, require_platform_admin
from app.schemas.auth import UserProfile
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("", response_model=List[CompanyResponse], status_code=status.HTTP_200_OK)
def list_companies(current_user: UserProfile = Depends(get_current_user)):
    """
    Lists companies. Platform Admins see all companies;
    standard users see only companies where they hold active memberships.
    """
    if current_user.is_system_admin:
        return CompanyService.list_companies()
    else:
        # Return member companies
        return [
            CompanyResponse(
                company_id=c.company_id,
                company_name=c.company_name,
                is_active=True
            )
            for c in current_user.companies
        ]


@router.get("/{company_id}", response_model=CompanyResponse, status_code=status.HTTP_200_OK)
def get_company(company_id: int, current_user: UserProfile = Depends(get_current_user)):
    """
    Retrieves details for a specific company.
    """
    if not current_user.is_system_admin:
        user_company_ids = [c.company_id for c in current_user.companies]
        if company_id not in user_company_ids:
            return CompanyService.get_company(company_id) # will raise 404/403
    return CompanyService.get_company(company_id)


@router.post("", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
def create_company(
    data: CompanyCreate,
    current_user: UserProfile = Depends(require_platform_admin)
):
    """
    Provisions a new Company / Tenant (Restricted strictly to Platform Administrators).
    """
    return CompanyService.create_company(data)


@router.put("/{company_id}", response_model=CompanyResponse, status_code=status.HTTP_200_OK)
def update_company(
    company_id: int,
    data: CompanyUpdate,
    current_user: UserProfile = Depends(require_platform_admin)
):
    """
    Updates company attributes or active status (Restricted to Platform Administrators).
    """
    return CompanyService.update_company(company_id, data)
