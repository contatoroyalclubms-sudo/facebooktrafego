from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, ConfigDict, field_serializer
from uuid import UUID as PyUUID
import uuid
from datetime import datetime
from typing import Optional

from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    facebook_access_token = Column(Text)
    facebook_ad_account_id = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    campaigns = relationship("Campaign", back_populates="user")

class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    facebook_access_token: Optional[str] = None
    facebook_ad_account_id: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDB(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: PyUUID
    created_at: datetime
    updated_at: datetime
    
    @field_serializer('id')
    def serialize_id(self, value: PyUUID) -> str:
        return str(value)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str  # Já como string
    email: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    facebook_ad_account_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
