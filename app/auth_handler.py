from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from jwt.exceptions import InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlmodel import Session, select
from db.session import get_session
from models import User

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_password_hash(password):
    """
    Генерирует хэш пароля с использованием bcrypt.
    
    Args:
        password (str): Пароль в открытом виде
        
    Returns:
        str: Хэшированная версия пароля
    """
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    """
    Проверяет соответствие пароля его хэшу.
    
    Args:
        plain_password (str): Пароль в открытом виде
        hashed_password (str): Хэшированный пароль
        
    Returns:
        bool: True если пароль совпадает, False в противном случае
    """
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Создает JWT токен доступа с указанными данными и сроком действия.
    
    Args:
        data (dict): Полезная нагрузка токена
        expires_delta (timedelta | None): Время жизни токена
        
    Returns:
        str: Закодированный JWT токен
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], 
                    db_session: Session = Depends(get_session)):
    """
    Возвращает текущего аутентифицированного пользователя на основе JWT токена.
    
    Args:
        token (str): JWT токен из заголовка Authorization
        db_session (Session): Сессия базы данных
        
    Raises:
        HTTPException: 401 если токен невалиден или пользователь не найден
        
    Returns:
        User: Объект аутентифицированного пользователя
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    # Поиск пользователя в базе данных по email
    statement = select(User).where(User.email == username)
    user = db_session.exec(statement).first()

    if user is None:
        raise credentials_exception
    return user