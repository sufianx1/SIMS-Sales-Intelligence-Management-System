"""
app/services/auth_service.py
----------------------------
Business service handling authentication, credentials verification,
profile compilation, and JWT token issuance via MongoDB.
"""

from typing import Optional
from fastapi import HTTPException, status
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.repositories.user_repo import UserRepository
from app.schemas.auth import UserProfile, UserCompanyMembership, TokenResponse


class AuthService:

    @staticmethod
    def authenticate_user(identifier: str, password: str) -> UserProfile:
        """
        Authenticates user with username or email, and password.
        Returns full UserProfile with permitted company memberships.
        Raises 401 Unauthorized if invalid or inactive.
        """
        user = UserRepository.get_by_identifier(identifier)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        if not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated. Please contact your administrator."
            )

        if not verify_password(password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username/email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Fetch permitted memberships
        memberships_data = UserRepository.get_memberships(
            user["user_id"], is_system_admin=user["is_system_admin"]
        )
        memberships = [UserCompanyMembership(**m) for m in memberships_data]

        profile = UserProfile(
            user_id=user["user_id"],
            username=user.get("username"),
            name=user["name"],
            email=user["email"],
            is_system_admin=user["is_system_admin"],
            is_active=user["is_active"],
            companies=memberships
        )
        return profile

    @staticmethod
    def create_token_for_profile(profile: UserProfile) -> TokenResponse:
        """Generates JWT token response for an authenticated UserProfile."""
        token = create_access_token(
            subject=profile.user_id,
            extra_claims={
                "email": profile.email,
                "username": profile.username,
                "is_system_admin": profile.is_system_admin
            }
        )
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=profile
        )

    @staticmethod
    def get_profile_by_id(user_id: int) -> Optional[UserProfile]:
        """Loads UserProfile by ID."""
        user = UserRepository.get_by_id(user_id)
        if not user or not user["is_active"]:
            return None

        memberships_data = UserRepository.get_memberships(
            user["user_id"], is_system_admin=user["is_system_admin"]
        )
        memberships = [UserCompanyMembership(**m) for m in memberships_data]

        return UserProfile(
            user_id=user["user_id"],
            username=user.get("username"),
            name=user["name"],
            email=user["email"],
            is_system_admin=user["is_system_admin"],
            is_active=user["is_active"],
            companies=memberships
        )
