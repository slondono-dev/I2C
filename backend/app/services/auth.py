from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.user import UserCreate


class AuthError(Exception):
    pass


def register_user(db: Session, data: UserCreate) -> User:
    email = data.email.lower()
    if db.execute(select(User).where(User.email == email)).scalar_one_or_none():
        raise AuthError("email already registered")
    user = User(name=data.name, email=email, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise AuthError("invalid credentials")
    return user


def token_for(user: User) -> str:
    return create_access_token(user.id)
