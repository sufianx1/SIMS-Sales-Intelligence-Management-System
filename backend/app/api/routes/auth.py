"""
app/api/routes/auth.py
----------------------
Authentication endpoints for user login, identity profile, and token refresh/revocation.
"""

from fastapi import APIRouter, Depends, Request, status
from app.services.auth_service import AuthService
from app.schemas.auth import LoginRequest, TokenResponse, UserProfile
from app.api.dependencies import get_current_user
from app.core.security import revoke_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def login(request: LoginRequest, req: Request):
    """
    Authenticates a user via username/email and password.
    Returns a JWT access token and permitted company memberships.
    Enforces login rate limiting.
    """
    client_ip = req.client.host if req.client else "127.0.0.1"
    identifier = (request.username or request.email or "").strip()
    profile = AuthService.authenticate_user(identifier=identifier, password=request.password, ip_address=client_ip)
    token_response = AuthService.create_token_for_profile(profile)
    return token_response


@router.get("/me", response_model=UserProfile, status_code=status.HTTP_200_OK)
def get_current_profile(current_user: UserProfile = Depends(get_current_user)):
    """
    Returns the authenticated user's profile and active company memberships.
    """
    return current_user


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(req: Request, current_user: UserProfile = Depends(get_current_user)):
    """
    Logs out the user session and revokes the active JWT token.
    """
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        revoke_token(token)
    return {"detail": "Successfully logged out"}
