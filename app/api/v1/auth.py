"""
Authentication API endpoints.
"""

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_tokens,
    verify_token,
    get_current_user
)
from app.models.user import User, UserPreferences
from app.schemas.user import (
    UserCreate, 
    UserResponse, 
    UserLogin, 
    Token,
    UserPreferencesCreate
)
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """Register a new user."""
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        is_active=True,
        is_verified=False  # Will be verified via email
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default user preferences
    preferences = UserPreferences(
        user_id=db_user.id,
        email_notifications=True,
        push_notifications=True,
        telegram_notifications=False,
        default_risk_per_trade="1%",
        max_concurrent_strategies=5,
        auto_trade_enabled=False,
        theme="dark",
        language="en",
        timezone="UTC",
        max_daily_loss="5%",
        max_position_size="10%",
        stop_loss_enabled=True,
        take_profit_enabled=True
    )
    
    db.add(preferences)
    db.commit()
    
    logger.info("User registered", user_id=db_user.id, email=db_user.email)
    
    return db_user


@router.post("/login", response_model=Token)
def login(
    user_credentials: UserLogin,
    db: Session = Depends(get_db)
) -> Any:
    """Login user and return tokens."""
    
    # Authenticate user
    user = db.query(User).filter(User.email == user_credentials.email).first()
    
    if not user or not verify_password(user_credentials.password, user.password_hash):
        logger.warning("Login failed", email=user_credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create tokens
    tokens = create_tokens(str(user.id))
    
    logger.info("User logged in", user_id=user.id, email=user.email)
    
    return tokens


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Any:
    """Refresh access token using refresh token."""
    
    try:
        user_id = verify_token(refresh_token, "refresh")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Create new tokens
        tokens = create_tokens(str(user.id))
        
        logger.info("Token refreshed", user_id=user.id)
        
        return tokens
        
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
def logout(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Logout user (client should discard tokens)."""
    
    logger.info("User logged out", user_id=current_user.id)
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> Any:
    """Get current user information."""
    return current_user


@router.post("/verify-email")
def verify_email(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """Verify user email address."""
    
    try:
        user_id = verify_token(token, "access")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        if user.is_verified:
            return {"message": "Email already verified"}
        
        user.is_verified = True
        db.commit()
        
        logger.info("Email verified", user_id=user.id, email=user.email)
        
        return {"message": "Email successfully verified"}
        
    except Exception as e:
        logger.error("Email verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )


@router.post("/forgot-password")
def forgot_password(
    email: str,
    db: Session = Depends(get_db)
) -> Any:
    """Send password reset email."""
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # TODO: Implement email sending logic
    # For now, just log the request
    logger.info("Password reset requested", email=email)
    
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/reset-password")
def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
) -> Any:
    """Reset user password."""
    
    try:
        user_id = verify_token(token, "access")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token"
            )
        
        # Update password
        user.password_hash = get_password_hash(new_password)
        db.commit()
        
        logger.info("Password reset", user_id=user.id, email=user.email)
        
        return {"message": "Password successfully reset"}
        
    except Exception as e:
        logger.error("Password reset failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
