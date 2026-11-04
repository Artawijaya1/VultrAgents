from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.item import Item
from app.schemas.item import ItemCreate, ItemUpdate


def get_item(db: Session, item_id: int) -> Item | None:
    return db.get(Item, item_id)


def list_items(db: Session, skip: int = 0, limit: int = 100) -> list[Item]:
    statement = select(Item).order_by(Item.id).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


def create_item(db: Session, item: ItemCreate) -> Item:
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_item(db: Session, db_item: Item, changes: ItemUpdate) -> Item:
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(db_item, field, value)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_item(db: Session, db_item: Item) -> None:
    db.delete(db_item)
    db.commit()

