from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import item as item_crud
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


def get_owned_item(db: Session, item_id: int, owner_id: int) -> Item:
    item = item_crud.get_item(db, item_id)
    if item is None or item.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Item not found.")
    return item


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: DbSession, current_user: CurrentUser) -> Item:
    if item.owner_id is not None and item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Items can only be created for your account.")
    return item_crud.create_item(
        db,
        item.model_copy(update={"owner_id": current_user.id}),
    )


@router.get("/", response_model=list[ItemRead])
def read_items(
    db: DbSession,
    current_user: CurrentUser,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[Item]:
    return item_crud.list_items(
        db,
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
    )


@router.get("/{item_id}", response_model=ItemRead)
def read_item(item_id: int, db: DbSession, current_user: CurrentUser) -> Item:
    return get_owned_item(db, item_id, current_user.id)


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(
    item_id: int,
    changes: ItemUpdate,
    db: DbSession,
    current_user: CurrentUser,
) -> Item:
    item = get_owned_item(db, item_id, current_user.id)
    return item_crud.update_item(db, item, changes)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: DbSession, current_user: CurrentUser) -> Response:
    item = get_owned_item(db, item_id, current_user.id)
    item_crud.delete_item(db, item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
