from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.token import SupabaseIdentity
from app.schemas.user import UserProfileUpdate, UserUpdate


def sync_supabase_user(db: Session, identity: SupabaseIdentity) -> User:
    if identity.email is None:
        raise ConflictError("The Supabase account must have a verified email address.")

    auth_user_id = identity.id
    user = user_crud.get_user_by_auth_id(db, auth_user_id)
    if user is None:
        full_name = identity.user_metadata.get("full_name")
        user = User(
            auth_user_id=auth_user_id,
            email=str(identity.email),
            full_name=(
                full_name.strip()[:200]
                if isinstance(full_name, str) and full_name.strip()
                else None
            ),
        )
        db.add(user)
    else:
        user.email = str(identity.email)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        concurrent_user = user_crud.get_user_by_auth_id(db, auth_user_id)
        if concurrent_user is not None:
            return concurrent_user
        raise ConflictError(
            "This email is already linked to another profile. Contact an administrator."
        ) from exc

    return user


def update_user_profile(
    db: Session,
    user: User,
    changes: UserProfileUpdate,
) -> User:
    admin_changes = UserUpdate(**changes.model_dump(exclude_unset=True))
    return user_crud.update_user(db, user, admin_changes)
