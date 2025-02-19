import logging

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.auth_service import send_registration_notification
from app.database.models import Role, User, LoginHistory

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_existing_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


# Dependency для получения сессии БД
def get_db():
    from app.database.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_login_attempt_to_db(user: User, db: Session = get_db(), ip_address: str = None):
    login = LoginHistory(user_id=user.id, ip_address=ip_address)
    db.add(login)
    try:
        db.commit()
        logger.info(f"Запись о входе для пользователя {user.id} сохранена (IP: {ip_address})")
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка сохранения записи о входе: {e}")
        raise e


def get_or_create_oauth_user(db: Session, provider: str, user_info: dict) -> User:
    """Ищет или создает пользователя на основе данных из OAuth."""
    user_email = user_info.get("email")
    user_identifier = user_info.get("sub") or user_info.get("id")
    computed_username = f"{provider}_{user_identifier}"
    user = None
    if user_email:
        user = db.query(User).filter(User.email == user_email).first()
    else:
        user = db.query(User).filter(User.username == computed_username).first()

    if not user:
        default_role = db.query(Role).filter(Role.name == "user").first()
        if not default_role:
            default_role = Role(name="user")
            db.add(default_role)
            db.commit()
            db.refresh(default_role)
        user = User(
            username=computed_username,
            email=user_email,
            provider=provider,
            role_id=default_role.id,
            hashed_password=""
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
            send_registration_notification(user, provider=provider)
        except Exception as e:
            db.rollback()
            raise e

    save_login_attempt_to_db(user, db)
    return user


def create_new_user(db: Session, username: str, email: str, password: str, provider: str = "inner") -> User:
    hashed = hash_password(password)
    default_role = db.query(Role).filter(Role.name == "user").first()
    if not default_role:
        default_role = Role(name="user")
        db.add(default_role)
        db.commit()
        db.refresh(default_role)

    new_user = User(
        username=username,
        email=email,
        hashed_password=hashed,
        provider=provider,
        role=default_role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user