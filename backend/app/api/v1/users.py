"""
User management API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth import get_current_active_user, require_admin
from app.models.schemas.auth import UserResponse, UserListResponse
from app.models.sql.user import User

router = APIRouter()


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all users (admin only)"""
    # TODO: Implement user pagination and filtering
    return {"users": [], "total": 0, "page": page, "per_page": per_page, "pages": 0}


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user by ID"""
    # TODO: Implement get user by ID
    return UserResponse.model_validate(current_user)


@router.get("/stats/overview")
async def get_user_stats(
    current_user: User = Depends(require_admin)
):
    """Get user statistics (admin only)"""
    # TODO: Implement user statistics
    return {
        "total_users": 0,
        "active_users": 0,
        "verified_users": 0,
        "users_by_role": {},
        "users_by_country": {},
        "recent_registrations": []
    }