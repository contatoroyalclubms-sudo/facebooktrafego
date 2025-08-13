from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime, timedelta
import json
import asyncio

from app.core.database import get_sync_db
from app.models.campaign import Campaign, CampaignMetrics, Alert
from app.models.user import User
from app.services.auth_service import get_current_user
from app.core.cache import cache

router = APIRouter()

class DashboardStats(BaseModel):
    total_campaigns: int
    active_campaigns: int
    total_spend_today: float
    total_impressions_today: int
    total_clicks_today: int
    total_conversions_today: int
    alerts_count: int
    performance_trend: str

class RecentAlert(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    created_at: datetime
    is_read: bool

class CampaignSummary(BaseModel):
    campaign_id: str
    name: str
    status: str
    spend_today: float
    impressions_today: int
    clicks_today: int
    ctr_today: float

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.active_connections.remove(connection)

manager = ConnectionManager()

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    cache_key = f"dashboard_stats_{current_user.id}"
    cached_stats = await cache.get(cache_key)
    if cached_stats:
        return DashboardStats(**cached_stats)
    
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).all()
    campaign_ids = [c.campaign_id for c in campaigns]
    
    total_campaigns = len(campaigns)
    active_campaigns = len([c for c in campaigns if c.status == 'ACTIVE'])
    
    today_metrics = db.query(CampaignMetrics).filter(
        CampaignMetrics.campaign_id.in_(campaign_ids),
        CampaignMetrics.date_start >= today_start,
        CampaignMetrics.date_stop <= today_end
    ).all()
    
    total_spend_today = sum(m.spend for m in today_metrics)
    total_impressions_today = sum(m.impressions for m in today_metrics)
    total_clicks_today = sum(m.clicks for m in today_metrics)
    total_conversions_today = sum(m.conversions for m in today_metrics)
    
    alerts_count = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False
    ).count()
    
    yesterday = today - timedelta(days=1)
    yesterday_start = datetime.combine(yesterday, datetime.min.time())
    yesterday_end = datetime.combine(yesterday, datetime.max.time())
    
    yesterday_metrics = db.query(CampaignMetrics).filter(
        CampaignMetrics.campaign_id.in_(campaign_ids),
        CampaignMetrics.date_start >= yesterday_start,
        CampaignMetrics.date_stop <= yesterday_end
    ).all()
    
    yesterday_spend = sum(m.spend for m in yesterday_metrics)
    
    if yesterday_spend > 0:
        spend_change = ((total_spend_today - yesterday_spend) / yesterday_spend) * 100
        if spend_change > 10:
            performance_trend = "up"
        elif spend_change < -10:
            performance_trend = "down"
        else:
            performance_trend = "stable"
    else:
        performance_trend = "stable"
    
    stats = DashboardStats(
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        total_spend_today=float(total_spend_today),
        total_impressions_today=int(total_impressions_today),
        total_clicks_today=int(total_clicks_today),
        total_conversions_today=int(total_conversions_today),
        alerts_count=alerts_count,
        performance_trend=performance_trend
    )
    
    await cache.set(cache_key, stats.dict(), expire=300)
    
    return stats

@router.get("/alerts", response_model=List[RecentAlert])
async def get_recent_alerts(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    alerts = db.query(Alert).filter(
        Alert.user_id == current_user.id
    ).order_by(Alert.created_at.desc()).limit(limit).all()
    
    return [
        RecentAlert(
            id=str(alert.id),
            title=alert.title,
            message=alert.message,
            severity=alert.severity,
            created_at=alert.created_at,
            is_read=alert.is_read
        )
        for alert in alerts
    ]

@router.get("/campaigns/summary", response_model=List[CampaignSummary])
async def get_campaigns_summary(
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    today = datetime.now().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    campaigns = db.query(Campaign).filter(
        Campaign.user_id == current_user.id
    ).order_by(Campaign.created_at.desc()).limit(limit).all()
    
    campaign_summaries = []
    
    for campaign in campaigns:
        today_metrics = db.query(CampaignMetrics).filter(
            CampaignMetrics.campaign_id == campaign.campaign_id,
            CampaignMetrics.date_start >= today_start,
            CampaignMetrics.date_stop <= today_end
        ).all()
        
        spend_today = sum(m.spend for m in today_metrics)
        impressions_today = sum(m.impressions for m in today_metrics)
        clicks_today = sum(m.clicks for m in today_metrics)
        
        ctr_today = (clicks_today / impressions_today * 100) if impressions_today > 0 else 0
        
        campaign_summaries.append(CampaignSummary(
            campaign_id=campaign.campaign_id,
            name=campaign.name,
            status=campaign.status,
            spend_today=float(spend_today),
            impressions_today=int(impressions_today),
            clicks_today=int(clicks_today),
            ctr_today=round(ctr_today, 2)
        ))
    
    return campaign_summaries

@router.post("/alerts/{alert_id}/mark-read")
async def mark_alert_read(
    alert_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id
    ).first()
    
    if not alert:
        return {"error": "Alert not found"}
    
    alert.is_read = True
    db.commit()
    
    return {"message": "Alert marked as read"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await asyncio.sleep(30)
            
            update_data = {
                "type": "stats_update",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "active_campaigns": 5,  # This would come from real data
                    "total_spend_today": 1250.50,
                    "alerts_count": 2
                }
            }
            
            await manager.send_personal_message(json.dumps(update_data), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.get("/performance/realtime")
async def get_realtime_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).all()
    campaign_ids = [c.campaign_id for c in campaigns]
    
    recent_metrics = db.query(CampaignMetrics).filter(
        CampaignMetrics.campaign_id.in_(campaign_ids),
        CampaignMetrics.created_at >= one_hour_ago
    ).all()
    
    total_spend = sum(m.spend for m in recent_metrics)
    total_impressions = sum(m.impressions for m in recent_metrics)
    total_clicks = sum(m.clicks for m in recent_metrics)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "spend_last_hour": float(total_spend),
        "impressions_last_hour": int(total_impressions),
        "clicks_last_hour": int(total_clicks),
        "ctr_last_hour": round((total_clicks / total_impressions * 100) if total_impressions > 0 else 0, 2)
    }
