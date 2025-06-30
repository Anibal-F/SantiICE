from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
# from passlib.context import CryptContext
import hashlib
from fastapi import HTTPException, status
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "santiice-ocr-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))

# Contexto de encriptación - usando hashlib temporalmente
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Base de datos simulada de usuarios
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "permissions": ["tickets", "conciliator", "config"],
        "is_active": True
    },
    "user": {
        "username": "user", 
        "hashed_password": hashlib.sha256("user123".encode()).hexdigest(),
        "role": "operator",
        "permissions": ["tickets"],
        "is_active": True
    }
}

def verify_password(plain_password, hashed_password):
    """Verificar contraseña"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

def get_password_hash(password):
    """Obtener hash de contraseña"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_user(username: str):
    """Obtener usuario de la base de datos"""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return user_dict
    return None

def authenticate_user(username: str, password: str):
    """Autenticar usuario"""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["hashed_password"]):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crear token de acceso"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verificar token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )