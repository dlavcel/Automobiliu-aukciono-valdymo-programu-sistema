from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.core.deps import get_current_user, get_db
from backend.models.user import User
from backend.schemas.auth import LoginRequest, TokenResponse
from backend.schemas.user import UserCreate, UserRead
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register_user(
    payload: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    return auth_service.register_user(payload)

@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.login(payload)

@router.get("/me", response_model=UserRead)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
