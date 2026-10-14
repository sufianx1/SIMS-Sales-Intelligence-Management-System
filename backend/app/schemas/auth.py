"""
app/schemas/auth.py
-------------------
Authentication and authorization request and response schemas.
"""

from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: str = Field(min_length=1, description="User password")


class UserCompanyMembership(BaseModel):
    company_id: int
    company_name: str
    role_id: int
    role_name: str
    store_id: Optional[int] = None
    store_name: Optional[str] = None
    permissions: List[str] = []


class UserProfile(BaseModel):
    user_id: int
    name: str
    email: str
    username: Optional[str] = None
    is_system_admin: bool
    is_active: bool
    companies: List[UserCompanyMembership] = []


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile


class TenantContext(BaseModel):
    user_id: int
    email: str
    is_system_admin: bool
    company_id: int
    company_name: str
    role_id: int
    role_name: str
    store_id: Optional[int] = None
    permissions: List[str] = []

    def has_permission(self, permission: str) -> bool:
        """Returns True if platform admin or explicitly granted in permissions."""
        if self.is_system_admin:
            return True
        p_lower = permission.lower().strip()
        perms_lower = [p.lower().strip() for p in self.permissions]
        if p_lower in perms_lower:
            return True
        # If user has manage_X, they have create_X, update_X, delete_X, view_X
        for prefix in ["create_", "update_", "delete_", "view_"]:
            if p_lower.startswith(prefix):
                entity = p_lower[len(prefix):]
                if f"manage_{entity}" in perms_lower or f"manage_{entity}s" in perms_lower:
                    return True
        return False
