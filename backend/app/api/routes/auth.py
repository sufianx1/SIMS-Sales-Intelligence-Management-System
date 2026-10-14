"""
app/api/routes/auth.py
----------------------
Authentication endpoints for user login, identity profile, and token refresh/revocation.
"""

from fastapi import APIRouter, Depends, status
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(request: LoginRequest):
    """
    Authenticates a user via username/email and password.
    Returns a JWT access token and permitted company memberships.
    """
    identifier = (request.username or request.email or "").strip()
    profile = AuthService.authenticate_user(identifier=identifier, password=request.password)
    token_response = AuthService.create_token_for_profile(profile)
    return token_response


@router.get("/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
def get_current_profile(current_user: UserProfile = Depends(get_current_user)):
    """
    Returns the authenticated user's profile and active company memberships.
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: UserProfile = Depends(get_current_user)):
    """
    Logs out the user session.
    """
    return {"detail": "Successfully logged out"}
