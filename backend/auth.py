from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import TokenData
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CustomHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request):
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        parts = authorization.split()
        if len(parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        scheme, credentials = parts
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)

security = CustomHTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    username = verify_token(token)
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_verified_user(current_user: User = Depends(get_current_active_user)):
    if not current_user.is_verified:
        raise HTTPException(status_code=400, detail="User not verified")
    return current_user

def require_admin(current_user: User = Depends(get_current_verified_user)):
    if current_user.user_type not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def require_superadmin(current_user: User = Depends(get_current_verified_user)):
    if current_user.user_type != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def check_tool_access(current_user: User, tool_id: str, db: Session):
    """Check if current user has access to a specific tool"""
    from models import Tool, ToolAccessRequest
    
    # Superadmins ALWAYS have access to all tools regardless of assignment
    if current_user.user_type == "superadmin":
        return True
    
    # Regular admins only have access to assigned tools
    if current_user.user_type == "admin":
        tool = db.query(Tool).filter(Tool.id == tool_id).first()
        if tool and tool.assigned_admin_id == current_user.id:
            return True
    
    return False

def require_tool_access(tool_id: str):
    """Decorator to require tool access for admin operations"""
    def decorator(current_user: User = Depends(get_current_verified_user), db: Session = Depends(get_db)):
        if not check_tool_access(current_user, tool_id, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this tool. Please request access from a superadmin."
            )
        return current_user
    return decorator

def get_token_optional(authorization: str = Header(None)):
    if not authorization:
        return None
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            return None
        return token
    except ValueError:
        return None

def get_current_user_optional(token: str = Depends(get_token_optional)):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
    except JWTError:
        return None
    
    db = next(get_db())
    user = get_user(db, username=token_data.username)
    if user is None:
        return None
    return user