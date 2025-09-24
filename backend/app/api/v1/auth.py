"""
Authentication API endpoints
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.core.config import get_settings
from app.core.database import get_db
from app.services.auth import AuthService, get_current_user, get_current_active_user
from app.models.schemas.auth import (
    UserCreate, UserLogin, UserLoginResponse, UserResponse,
    Token, PasswordReset, PasswordResetConfirm, PasswordChange,
    EmailVerification, TokenData
)
from app.models.sql.user import User

settings = get_settings()
router = APIRouter()
bearer_scheme = HTTPBearer()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    
    # Check if user already exists
    existing_user = await AuthService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_user = await AuthService.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    user_dict = user_data.model_dump()
    user = await AuthService.create_user(db, user_dict)
    
    # TODO: Send verification email
    # background_tasks.add_task(send_verification_email, user.email, user.id)
    
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserLoginResponse)
async def login_user(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return tokens"""
    
    # Authenticate user
    user = await AuthService.authenticate_user(
        db, user_credentials.username, user_credentials.password
    )
    
    if not user:
        # Update failed login attempts
        await AuthService.update_failed_login_attempts(db, user_credentials.username)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    if user_credentials.remember_me:
        access_token_expires = timedelta(days=7)  # Extended for remember me
    
    token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value,
    }
    
    access_token = AuthService.create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    refresh_token = AuthService.create_refresh_token(data=token_data)
    
    return UserLoginResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=int(access_token_expires.total_seconds())
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    # Verify refresh token
    try:
        token_data = AuthService.verify_token(credentials.credentials, token_type="refresh")
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = await AuthService.get_user_by_id(db, token_data.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new tokens
    new_token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value,
    }
    
    access_token = AuthService.create_access_token(data=new_token_data)
    refresh_token = AuthService.create_refresh_token(data=new_token_data)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_active_user)
):
    """Logout user (invalidate tokens)"""
    # TODO: Implement token blacklisting in Redis
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: dict,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user profile"""
    
    # Update allowed fields
    allowed_fields = [
        "full_name", "phone_number", "organization", "country", 
        "bio", "language", "timezone", "theme"
    ]
    
    for field, value in user_update.items():
        if field in allowed_fields and value is not None:
            setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    
    # Verify current password
    if not AuthService.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Hash new password
    new_hashed_password = AuthService.hash_password(password_data.new_password)
    current_user.hashed_password = new_hashed_password
    current_user.password_changed_at = func.now()
    
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset"""
    
    user = await AuthService.get_user_by_email(db, password_reset.email)
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link has been sent"}
    
    # TODO: Generate reset token and send email
    # background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with token"""
    
    # TODO: Verify reset token and update password
    # This would involve:
    # 1. Verify the token is valid and not expired
    # 2. Get the user associated with the token
    # 3. Update the password
    # 4. Invalidate the reset token
    
    return {"message": "Password reset successfully"}


@router.post("/verify-email")
async def verify_email(
    verification: EmailVerification,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email with token"""
    
    # TODO: Verify email verification token
    # This would involve:
    # 1. Verify the token is valid and not expired
    # 2. Get the user associated with the token
    # 3. Mark email as verified
    # 4. Activate the account if needed
    
    return {"message": "Email verified successfully"}


@router.post("/resend-verification")
async def resend_verification_email(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Resend email verification"""
    
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # TODO: Send verification email
    # background_tasks.add_task(send_verification_email, current_user.email, current_user.id)
    
    return {"message": "Verification email sent"}


@router.get("/sessions")
async def get_active_sessions(
    current_user: User = Depends(get_current_active_user)
):
    """Get user's active sessions"""
    
    # TODO: Implement session tracking in Redis
    return {"sessions": []}


@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Revoke a specific session"""
    
    # TODO: Implement session revocation
    return {"message": f"Session {session_id} revoked"}