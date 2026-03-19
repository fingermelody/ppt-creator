"""
安全模块
JWT 认证、密码哈希等
"""

from datetime import datetime, timedelta
from typing import Optional, Any
import bcrypt
from jose import jwt, JWTError
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

# Bearer token 安全方案
security = HTTPBearer(auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """创建 JWT 访问令牌"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码 JWT 访问令牌"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """从 JWT 令牌获取当前用户ID
    
    如果没有提供认证信息，返回默认用户 ID（用于演示/开发）
    """
    # 默认用户 ID（用于匿名访问）
    DEFAULT_USER_ID = "anonymous-user-001"
    
    if credentials is None:
        # 允许匿名访问，返回默认用户 ID
        return DEFAULT_USER_ID
    
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        # Token 无效，返回默认用户 ID
        return DEFAULT_USER_ID
    
    user_id: str = payload.get("sub")
    if user_id is None:
        return DEFAULT_USER_ID
    
    return user_id


async def get_optional_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[str]:
    """可选的用户ID获取（允许匿名访问）"""
    if credentials is None:
        return None
    
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        return None
    
    return payload.get("sub")
