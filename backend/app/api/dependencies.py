"""
app/api/dependencies.py
-----------------------
FastAPI security and authorization dependencies.
Enforces user authentication, tenant context verification, and RBAC guards via MongoDB.
"""

from typing import Optional, Callable
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_access_token
from app.db.mongo import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserProfile, TenantContext
from app.services.auth_service import AuthService

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme)
) -> UserProfile:
    """
    Validates Bearer token and returns active UserProfile.
    Raises 401 Unauthorized if token is missing, invalid, or expired.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is required",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token contains invalid subject",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user ID format in token")

    profile = AuthService.get_profile_by_id(user_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found or deactivated")

    return profile


async def get_tenant_context(
    current_user: UserProfile = Depends(get_current_user),
    x_company_id: Optional[str] = Header(None, alias="X-Company-ID")
) -> TenantContext:
    """
    Resolves and verifies active tenant context from the X-Company-ID header.
    Never trusts client input blindly: verifies membership and active role in database.
    """
    if not x_company_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Company-ID header is required for tenant-scoped operations."
        )

    try:
        company_id = int(x_company_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Company-ID header must be an integer identifier."
        )

    db = get_db()
    comp = db.companies.find_one({"company_id": company_id})
    if not comp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company with ID {company_id} does not exist."
        )

    company_name = comp["company_name"]
    is_comp_active = bool(comp.get("is_active", True))
    if not is_comp_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Company '{company_name}' is currently deactivated."
        )

    all_perms = [
        "view_dashboard", "manage_orders", "view_orders", "manage_customers", "view_customers",
        "manage_products", "view_products", "manage_inventory", "view_inventory",
        "inventory_transfer", "inventory_adjust", "manage_stores", "view_stores",
        "view_analytics", "import_data", "manage_integrations", "manage_users"
    ]

    # Platform Administrator cross-tenant bypass
    if current_user.is_system_admin:
        return TenantContext(
            user_id=current_user.user_id,
            email=current_user.email,
            is_system_admin=True,
            company_id=company_id,
            company_name=company_name,
            role_id=1,
            role_name="Platform Admin",
            store_id=None,
            permissions=all_perms
        )

    # Standard user: inspect tenant membership
    membership = UserRepository.get_tenant_membership(current_user.user_id, company_id, db=db)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User does not have active membership in company ID {company_id}."
        )

    return TenantContext(
        user_id=current_user.user_id,
        email=current_user.email,
        is_system_admin=False,
        company_id=membership["company_id"],
        company_name=membership["company_name"],
        role_id=membership["role_id"],
        role_name=membership["role_name"],
        store_id=membership.get("store_id"),
        permissions=membership.get("permissions", [])
    )


def require_permission(permission_name: str) -> Callable:
    """
    Factory dependency creating a guard that enforces a specific permission
    within the active tenant context.
    """
    async def permission_checker(context: TenantContext = Depends(get_tenant_context)) -> TenantContext:
        if not context.has_permission(permission_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Action requires '{permission_name}' privilege."
            )
        return context

    return permission_checker


async def require_platform_admin(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    """
    Guard that restricts endpoint strictly to Platform Administrators.
    """
    if not current_user.is_system_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Platform Administrator privileges required."
        )
    return current_user
