# app/auth_router.py
import logging
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.database.models import LoginHistory

logger = logging.getLogger(__name__)

history_router = APIRouter()


class History(BaseModel):
    user_id: str
    username: str
    login_time: datetime

    class Config:
        orm_mode = True


import logging
from fastapi import HTTPException, Header, Depends
from sqlalchemy.orm import Session
from app.jwt_utils import get_payload
from app.database.db_service import get_db
from app.database.models import User

logger = logging.getLogger(__name__)


def get_current_user(access_token: str = Query(...), db: Session = Depends(get_db)) -> User:
    if not access_token:
        raise HTTPException(status_code=401, detail="Отсутствует access token")

    try:
        payload = get_payload(access_token)
    except Exception as e:
        logger.error("Ошибка декодирования токена: %s", e)
        raise HTTPException(status_code=401, detail="Неверный или просроченный токен")

    try:
        user_id = payload.get("sub")
        logger.debug("user id from token: %s", user_id)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Неверный идентификатор пользователя в токене")

    user_id = int(user_id)
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return user


@history_router.get("/history", response_model=list[History])
def get_login_history_for_current_user(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
        limit: int = Query(10, ge=1),
        offset: int = Query(0, ge=0)
):
    query = (
        db.query(LoginHistory)
        .join(User)
        .filter(LoginHistory.user_id == current_user.id)
        .order_by(LoginHistory.login_time.desc())
    )
    history_entries = query.limit(limit).offset(offset).all()
    return [
        History(
            user_id=str(entry.user_id),
            username=entry.user.username,
            login_time=entry.login_time
        )
        for entry in history_entries
    ]
