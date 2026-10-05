from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.ratelimit import limiter
from app.models import User
from app.schemas.user import Token, UserCreate, UserLogin, UserOut
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(request: Request, data: UserCreate, db: Session = Depends(get_db)):
    try:
        user = auth_service.register_user(db, data)
    except auth_service.AuthError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    return Token(access_token=auth_service.token_for(user), user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
@limiter.limit("20/minute")
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    try:
        user = auth_service.authenticate(db, data.email, data.password)
    except auth_service.AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc
    return Token(access_token=auth_service.token_for(user), user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
