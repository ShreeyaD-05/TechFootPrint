from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from shared.database import get_db
from shared.schemas import UserCreate, UserResponse, UserWithRoleResponse, Token, ChangePasswordRequest
from services.auth.service import AuthService
from shared.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    if AuthService.get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if AuthService.get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    db_user = AuthService.create_user(db, user)
    return db_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    username = AuthService.verify_token(token)

    if username is None:
        raise credentials_exception

    user = AuthService.get_user_by_username(db, username)

    if user is None:
        raise credentials_exception

    return user

@router.get("/me", response_model=UserWithRoleResponse)
async def read_users_me(current_user = Depends(get_current_user)):
    return current_user

@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Change the currently authenticated user's password.
    Requires the correct current password for verification.
    Available to all roles.
    """
    if not AuthService.verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    current_user.hashed_password = AuthService.get_password_hash(payload.new_password)
    current_user.is_first_login = False   # clear first-login flag
    db.commit()
    return {"message": "Password changed successfully"}
