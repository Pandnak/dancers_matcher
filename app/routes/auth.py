from sqlalchemy.exc import IntegrityError
from psycopg2.errors import UniqueViolation
from fastapi import APIRouter, status, HTTPException, Depends
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from models import User
from auth_handler import (get_password_hash,
                          verify_password,
                          create_access_token)
from db.session import SessionDep
from auth_handler import ACCESS_TOKEN_EXPIRE_MINUTES
from sqlmodel import select
from datetime import timedelta
from db.session import SessionDep
from db.db import engine
from auth_handler import get_current_user


app = APIRouter(prefix='/auth',tags=['auth'])

@app.post("/signup", status_code=status.HTTP_201_CREATED,
             response_model=int,
             summary = 'Добавить пользователя')
def create_user(user: User,
                session: SessionDep):
    """
    Зарегистрировать нового пользователя системы.
    
    Args:
        user (User): Данные нового пользователя
        session (Session): Сессия базы данных

    Raises:
        HTTPException: 422 если email уже зарегистрирован

    Returns:
        int: ID созданного пользователя
    """

    new_user = User(
        name=user.name,
        email=user.email,
        user_type=user.user_type,
        dancer_id=user.dancer_id,
        password=get_password_hash(user.password)
    )
    try:
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user.user_id
    except IntegrityError as e:
        assert isinstance(e.orig, UniqueViolation)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User with email {user.email} already exists"
        )


@app.post("/login", status_code=status.HTTP_200_OK,
             summary = 'Войти в систему')
def user_login(session: SessionDep, login_attempt_data: OAuth2PasswordRequestForm = Depends()):
    statement = (select(User)
                 .where(User.email == login_attempt_data.username))
    """
    Аутентификация пользователя и получение JWT токена.
    
    Args:
        login_attempt_data (OAuth2PasswordRequestForm): Данные для входа
        db_session (Session): Сессия базы данных

    Raises:
        HTTPException: 401 при неверных учетных данных

    Returns:
        dict: JWT токен доступа
    """

    existing_user = session.exec(statement).first()

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User {login_attempt_data.username} not found"
        )

    if verify_password(
            login_attempt_data.password,
            existing_user.password):
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": login_attempt_data.username},
            expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Wrong password for user {login_attempt_data.username}"
        )
    
@app.delete("/{user_id}")
def delete_user(user_id: int, 
                session: SessionDep,
                current_user = Depends(get_current_user)):
    """
    Удалить пользователя из системы по его ID.
    
    Args:
        user_id (int): Уникальный идентификатор пользователя
        session (SessionDep): Сессия базы данных

    Raises:
        HTTPException: 404 если пользователь не найден

    Returns:
        dict: Результат операции
    """
    if current_user.user_type == "DANCER" and \
            user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can't delete other users",
        )


    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    session.delete(user)
    session.commit()
    return {"ok": True}