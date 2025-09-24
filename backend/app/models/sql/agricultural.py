"""
Agricultural Data SQL Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
import uuid
import enum

from app.core.database import Base


class Country(Base):
    """Country model"""
    __tablename__ = "countries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    iso_code = Column(String(3), unique=True, nullable=False)
    region = Column(String(100), nullable=False)
    sub_region = Column(String(100), nullable=True)
    
    # Geographic data
    geometry = Column(Geometry("MULTIPOLYGON"), nullable=True)
    capital = Column(String(255), nullable=True)
    area_km2 = Column(Float, nullable=True)
    
    # Economic indicators
    gdp = Column(Float, nullable=True)
    population = Column(Integer, nullable=True)
    agricultural_land_percent = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Crop(Base):
    """Crop/Culture model"""
    __tablename__ = "crops"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    scientific_name = Column(String(255), nullable=True)
    category = Column(String(100), nullable=False)  # cereal, legume, tuber, etc.
    
    # Crop characteristics
    growth_period_days = Column(Integer, nullable=True)
    water_requirement = Column(String(50), nullable=True)  # low, medium, high
    climate_zones = Column(ARRAY(String), nullable=True)
    
    # Nutritional information
    calories_per_100g = Column(Float, nullable=True)
    protein_percent = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Production(Base):
    """Agricultural production data"""
    __tablename__ = "productions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    
    # Time period
    year = Column(Integer, nullable=False)
    season = Column(String(50), nullable=True)  # dry, wet, annual
    
    # Production metrics
    area_harvested_ha = Column(Float, nullable=True)  # hectares
    production_tonnes = Column(Float, nullable=True)
    yield_tonnes_per_ha = Column(Float, nullable=True)
    
    # Economic data
    producer_price_usd = Column(Float, nullable=True)
    total_value_usd = Column(Float, nullable=True)
    
    # Quality indicators
    data_quality = Column(String(20), default="estimated")  # official, estimated, forecast
    confidence_level = Column(Float, nullable=True)  # 0-1
    
    # Geographic precision
    region = Column(String(255), nullable=True)
    location = Column(Geometry("POINT"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    country = relationship("Country", backref="productions")
    crop = relationship("Crop", backref="productions")


class WeatherData(Base):
    """Weather and climate data"""
    __tablename__ = "weather_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False)
    
    # Location
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(255), nullable=True)
    
    # Time
    date = Column(DateTime(timezone=True), nullable=False)
    
    # Weather metrics
    temperature_celsius = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    temperature_min = Column(Float, nullable=True)
    humidity_percent = Column(Float, nullable=True)
    precipitation_mm = Column(Float, nullable=True)
    wind_speed_kmh = Column(Float, nullable=True)
    pressure_hpa = Column(Float, nullable=True)
    
    # Agricultural indices
    growing_degree_days = Column(Float, nullable=True)
    evapotranspiration_mm = Column(Float, nullable=True)
    drought_index = Column(Float, nullable=True)
    
    # Data source
    source = Column(String(100), nullable=False)  # openweather, fao, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    country = relationship("Country", backref="weather_data")


class PriceData(Base):
    """Market price data"""
    __tablename__ = "price_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=False)
    
    # Time and location
    date = Column(DateTime(timezone=True), nullable=False)
    market_name = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True)
    
    # Price information
    price_usd_per_kg = Column(Float, nullable=False)
    currency = Column(String(10), nullable=False)
    original_price = Column(Float, nullable=False)
    exchange_rate = Column(Float, nullable=True)
    
    # Market conditions
    supply_level = Column(String(20), nullable=True)  # low, normal, high
    demand_level = Column(String(20), nullable=True)
    price_trend = Column(String(20), nullable=True)  # rising, stable, falling
    
    # Data quality
    source = Column(String(100), nullable=False)
    reliability_score = Column(Float, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    country = relationship("Country", backref="prices")
    crop = relationship("Crop", backref="prices")


class Prediction(Base):
    """AI/ML Predictions"""
    __tablename__ = "predictions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=False)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=True)
    
    # Prediction details
    prediction_type = Column(String(50), nullable=False)  # yield, price, weather, etc.
    target_date = Column(DateTime(timezone=True), nullable=False)
    predicted_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)
    
    # Model information
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)  # 0-1
    
    # Additional data
    features_used = Column(JSON, nullable=True)
    prediction_range = Column(JSON, nullable=True)  # min/max estimates
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    country = relationship("Country", backref="predictions")
    crop = relationship("Crop", backref="predictions")


class Alert(Base):
    """System alerts"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    country_id = Column(UUID(as_uuid=True), ForeignKey("countries.id"), nullable=True)
    crop_id = Column(UUID(as_uuid=True), ForeignKey("crops.id"), nullable=True)
    
    # Alert information
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    alert_type = Column(String(50), nullable=False)  # weather, price, yield, etc.
    severity = Column(String(20), nullable=False)  # info, warning, critical
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    
    # Notification channels
    sent_email = Column(Boolean, default=False, nullable=False)
    sent_sms = Column(Boolean, default=False, nullable=False)
    sent_push = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    data_source = Column(JSON, nullable=True)
    trigger_conditions = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)