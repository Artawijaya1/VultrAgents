from sqlalchemy import Engine

from app.db.session import engine
from app.models.base import Base
from app.models import item, user  # noqa: F401


def create_tables(target_engine: Engine = engine) -> None:
    Base.metadata.create_all(bind=target_engine)


if __name__ == "__main__":
    create_tables()

