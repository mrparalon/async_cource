from datetime import datetime, timedelta
from enum import StrEnum, auto
from typing import Annotated, TypeAlias
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import Session

from src.database import get_db
from src.events import send_event

from .models import User

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    access_token: str
    token_type: str


class Role(StrEnum):
    user = auto()
    admin = auto()


class UserCreatePayload(BaseModel):
    username: str
    email: EmailStr
    role: Role


class UserSchema(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: Role

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    user_id: UUID


class UserPatchRolePayload(BaseModel):
    role: Role


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()


DbDep: TypeAlias = Annotated[Session, Depends(get_db)]


def get_user(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == str(user_id)).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta if expires_delta else datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(db: DbDep, token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: UUID = UUID(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = get_user(db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user


async def send_auth_event(name: str, payload: dict):
    data = {
        "name": name,
        "payload": payload,
    }
    await send_event("auth", data)


@router.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreatePayload, db: DbDep) -> UserSchema:
    db_user = User(
        id=str(uuid4()),
        username=user.username,
        role=user.role,
        email=user.email,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    user_schema = UserSchema.model_validate(db_user)
    await send_auth_event("user.created", user_schema.dict())

    return user_schema


@router.patch("/users/{user_id}")
async def assign_role_to_user(
    db: DbDep, user_id: UUID, payload: UserPatchRolePayload, current_user: Annotated[User, Depends(get_current_user)]
) -> UserSchema:
    if current_user.role != Role.admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = db.query(User).filter(User.id == str(user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    previous_role = user.role
    user.role = payload.role.value
    db.commit()
    db.refresh(user)
    await send_auth_event(
        "role.chaged",
        {
            "user_id": user.id,
            "previous_role": previous_role,
            "new_role": user.role,
        },
    )
    return UserSchema.model_validate(user)


@router.post("/token")
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbDep) -> Token:
    user = get_user_by_username(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.id}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/users/me/")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserSchema:
    return UserSchema.model_validate(current_user)
