from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.token import SupabaseIdentity
from app.schemas.user import UserProfileUpdate, UserRead, UserUpdate
from app.services.user_service import update_user_profile

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
AdminIdentity = Annotated[SupabaseIdentity, Depends(require_admin)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/", response_model=list[UserRead])
def read_users(
    db: DbSession,
    _: AdminIdentity,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[User]:
    return user_crud.list_users(db, skip=skip, limit=limit)


@router.get("/me", response_model=UserRead)
def read_current_user(user: CurrentUser) -> User:
    return user


@router.patch("/me", response_model=UserRead)
def update_current_user(
    changes: UserProfileUpdate,
    user: CurrentUser,
    db: DbSession,
) -> User:
    return update_user_profile(db, user, changes)


@router.get("/{user_id}", response_model=UserRead)
def read_user(user_id: int, db: DbSession, _: AdminIdentity) -> User:
    user = user_crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    changes: UserUpdate,
    db: DbSession,
    _: AdminIdentity,
) -> User:
    user = user_crud.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return user_crud.update_user(db, user, changes)
