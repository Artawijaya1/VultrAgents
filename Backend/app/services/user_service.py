from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, user: UserCreate) -> User:
    if user_crud.get_user_by_email(db, str(user.email)) is not None:
        raise ConflictError("A user with this email already exists.")

    try:
        return user_crud.create_user(db, user)
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError("A user with this email already exists.") from exc
