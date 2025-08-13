from sqlalchemy import Column, String, Decimal, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(255), nullable=False)
    objective = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    daily_budget = Column(Decimal(10, 2))
    total_budget = Column(Decimal(10, 2))
    config_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="campaigns")
    metrics = relationship("CampaignMetrics", back_populates="campaign")

class CampaignMetrics(Base):
    __tablename__ = "campaign_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(String(255), ForeignKey("campaigns.campaign_id"))
    date_start = Column(DateTime(timezone=True), nullable=False, index=True)
    date_stop = Column(DateTime(timezone=True), nullable=False)
    impressions = Column(Decimal(15, 0), default=0)
    clicks = Column(Decimal(15, 0), default=0)
    conversions = Column(Decimal(15, 0), default=0)
    spend = Column(Decimal(10, 2), default=0)
    cpm = Column(Decimal(10, 4), default=0)
    ctr = Column(Decimal(10, 4), default=0)
    roas = Column(Decimal(10, 4), default=0)
    frequency = Column(Decimal(10, 4), default=0)
    reach = Column(Decimal(15, 0), default=0)
    cost_per_conversion = Column(Decimal(10, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    campaign = relationship("Campaign", back_populates="metrics")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    campaign_id = Column(String(255), index=True)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSONB)
    is_read = Column(Boolean, default=False, index=True)
    action_taken = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    resolved_at = Column(DateTime(timezone=True))

    user = relationship("User")

class Optimization(Base):
    __tablename__ = "optimizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(String(255), nullable=False, index=True)
    optimization_type = Column(String(100), nullable=False)
    action_type = Column(String(100), nullable=False)
    old_value = Column(Decimal(15, 4))
    new_value = Column(Decimal(15, 4))
    reason = Column(Text)
    performance_before = Column(JSONB)
    performance_after = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

class AIInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    insight_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    data = Column(JSONB)
    confidence_score = Column(Decimal(3, 2))
    is_applied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    context = Column(JSONB)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User")
