from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from .auth import authenticate_user, create_access_token, verify_token, get_user, ACCESS_TOKEN_EXPIRE_MINUTES
from .models import UserLogin, Token, User

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Endpoint de login"""
    user = authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "role": user["role"],
            "permissions": user["permissions"]
        }
    }

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Obtener usuario actual desde el token"""
    username = verify_token(credentials.credentials)
    user = get_user(username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

@router.get("/me", response_model=User)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    """Obtener información del usuario actual"""
    return {
        "username": current_user["username"],
        "role": current_user["role"],
        "permissions": current_user["permissions"],
        "is_active": current_user["is_active"]
    }

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Cerrar sesión"""
    return {"message": "Sesión cerrada exitosamente"}

# Exportar get_current_user para uso en otras rutas
__all__ = ["router", "get_current_user"]