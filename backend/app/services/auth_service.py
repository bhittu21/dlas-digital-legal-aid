import datetime
from typing import Optional
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8")[:72],
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower().strip()).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    hashed = get_password_hash(user_in.password)
    user = User(
        email=user_in.email.lower().strip(),
        hashed_password=hashed,
        full_name=user_in.full_name,
        full_name_bn=user_in.full_name_bn,
        role=user_in.role if user_in.role in UserRole.ALL_ROLES else UserRole.APPLICANT,
        phone_number=user_in.phone_number,
        district=user_in.district,
        specialization=user_in.specialization,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
