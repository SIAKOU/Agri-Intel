"""AI Predictions API endpoints"""

from fastapi import APIRouter, Depends
from app.services.auth import get_current_verified_user
from app.models.sql.user import User

router = APIRouter()

@router.get("/yield/{country}/{crop}")
async def predict_yield(
    country: str,
    crop: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Predict crop yield"""
    return {"prediction": "Yield prediction - TODO"}

@router.get("/weather/{country}")
async def predict_weather(
    country: str,
    current_user: User = Depends(get_current_verified_user)
):
    """Predict weather patterns"""
    return {"prediction": "Weather prediction - TODO"}