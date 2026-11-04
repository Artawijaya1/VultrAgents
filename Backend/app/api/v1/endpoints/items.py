from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud import item as item_crud
from app.models.item import Item
from app.models.user import User
from app.schemas.item import ItemCreate, ItemRead, ItemUpdate

router = APIRouter()
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/", response_model=ItemRead, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: DbSession) -> Item:
    if item.owner_id is not None and db.get(User, item.owner_id) is None:
        raise HTTPException(status_code=404, detail="Owner not found.")
    return item_crud.create_item(db, item)


@router.get("/", response_model=list[ItemRead])
def read_items(
    db: DbSession,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 100,
) -> list[Item]:
    return item_crud.list_items(db, skip=skip, limit=limit)


@router.get("/{item_id}", response_model=ItemRead)
def read_item(item_id: int, db: DbSession) -> Item:
    item = item_crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found.")
    return item


@router.patch("/{item_id}", response_model=ItemRead)
def update_item(item_id: int, changes: ItemUpdate, db: DbSession) -> Item:
    item = item_crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found.")
    return item_crud.update_item(db, item, changes)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, db: DbSession) -> Response:
    item = item_crud.get_item(db, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found.")
    item_crud.delete_item(db, item)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
