"""Alerts and Notifications API endpoints"""

from fastapi import APIRouter, Depends
from app.services.auth import get_current_active_user
from app.models.sql.user import User

router = APIRouter()

@router.get("/")
async def get_alerts(
    current_user: User = Depends(get_current_active_user)
):
    """Get user alerts"""
    return {"alerts": []}

@router.post("/")
async def create_alert(
    alert_data: dict,
    current_user: User = Depends(get_current_active_user)
):
    """Create new alert"""
    return {"message": "Alert created - TODO"}