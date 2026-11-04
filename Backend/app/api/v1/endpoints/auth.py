from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import bearer_scheme, get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import AuthSession, LoginRequest, RefreshRequest
from app.schemas.user import UserProfileUpdate, UserRead
from app.services import auth_service
from app.services.user_service import update_user_profile

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/login", response_model=AuthSession)
def login(request: LoginRequest) -> AuthSession:
    return auth_service.login(
        str(request.email),
        request.password.get_secret_value(),
    )


@router.post("/refresh", response_model=AuthSession)
def refresh(request: RefreshRequest) -> AuthSession:
    return auth_service.refresh_session(request.refresh_token.get_secret_value())


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> Response:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer access token is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    auth_service.logout(credentials.credentials)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserRead)
def read_current_profile(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    return user


@router.patch("/me", response_model=UserRead)
def update_current_profile(
    changes: UserProfileUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: DbSession,
) -> User:
    return update_user_profile(db, user, changes)
