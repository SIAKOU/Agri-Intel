"""
Dashboard API endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth import get_current_verified_user
from app.models.sql.user import User

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get dashboard overview data"""
    return {
        "kpis": {
            "total_production": 1250000,
            "price_index": 125.5,
            "weather_alerts": 3,
            "countries_monitored": 15
        },
        "recent_alerts": [],
        "top_crops": [
            {"name": "Maïs", "production": 450000, "change": 5.2},
            {"name": "Riz", "production": 320000, "change": -2.1},
            {"name": "Manioc", "production": 280000, "change": 8.7}
        ],
        "weather_summary": {
            "average_temperature": 28.5,
            "rainfall_mm": 45.2,
            "drought_risk": "medium"
        }
    }


@router.get("/charts/production")
async def get_production_chart_data(
    country: str = None,
    crop: str = None,
    year: int = None,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get production chart data"""
    # Mock data for now
    return {
        "data": [
            {"country": "Nigeria", "crop": "Maïs", "production": 12000000, "year": 2023},
            {"country": "Ghana", "crop": "Cacao", "production": 800000, "year": 2023},
            {"country": "Togo", "crop": "Coton", "production": 150000, "year": 2023}
        ],
        "total": 3
    }


@router.get("/charts/prices")
async def get_price_chart_data(
    country: str = None,
    crop: str = None,
    period: str = "1M",
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get price trend chart data"""
    return {
        "data": [
            {"date": "2024-01-01", "price": 450, "crop": "Maïs"},
            {"date": "2024-02-01", "price": 475, "crop": "Maïs"},
            {"date": "2024-03-01", "price": 460, "crop": "Maïs"}
        ],
        "total": 3
    }


@router.get("/maps/production")
async def get_production_map_data(
    crop: str = None,
    year: int = None,
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Get production data for map visualization"""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "country": "Nigeria",
                    "production": 12000000,
                    "crop": "Maïs",
                    "density": 2500
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [8.6753, 9.0820]
                }
            }
        ]
    }


@router.get("/export/{format}")
async def export_dashboard_data(
    format: str,  # pdf, excel, csv
    current_user: User = Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db)
):
    """Export dashboard data in various formats"""
    # TODO: Implement data export functionality
    return {"download_url": f"/static/exports/dashboard_export.{format}"}