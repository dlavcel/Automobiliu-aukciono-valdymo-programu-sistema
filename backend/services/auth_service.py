from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.security import create_access_token, get_password_hash, verify_password
from backend.models.user import User
from backend.schemas.auth import LoginRequest, TokenResponse
from backend.schemas.user import UserCreate

class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, payload: UserCreate) -> User:
        self._validate_password(payload.password)
        self._ensure_email_not_registered(payload.email)

        user = User(
            email=payload.email,
            password_hash=get_password_hash(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone=payload.phone,
            is_active=True,
            is_admin=False,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, payload: LoginRequest) -> TokenResponse:
        user = self._get_user_by_email(payload.email)

        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Incorrect email or password")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Inactive user")

        access_token = create_access_token(subject=user.id)
        return TokenResponse(access_token=access_token)

    def _get_user_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def _ensure_email_not_registered(self, email: str) -> None:
        if self._get_user_by_email(email):
            raise HTTPException(status_code=400, detail="Email already registered")

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
