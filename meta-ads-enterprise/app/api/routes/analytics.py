from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from decimal import Decimal

from app.core.database import get_sync_db
from app.models.campaign import Campaign, CampaignMetrics
from app.models.user import User
from app.api.routes.auth import get_current_active_user

router = APIRouter()

class AnalyticsResponse(BaseModel):
    total_campaigns: int
    active_campaigns: int
    total_spend: Decimal
    total_impressions: int
    total_clicks: int
    total_conversions: int
    average_ctr: float
    average_cpm: float
    average_roas: float

class CampaignPerformance(BaseModel):
    campaign_id: str
    campaign_name: str
    spend: Decimal
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    cpm: float
    roas: float
    performance_score: float

class TimeSeriesData(BaseModel):
    date: datetime
    spend: Decimal
    impressions: int
    clicks: int
    conversions: int
    ctr: float
    cpm: float

@router.get("/overview", response_model=AnalyticsResponse)
async def get_analytics_overview(
    date_start: Optional[datetime] = Query(None),
    date_end: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    if not date_end:
        date_end = datetime.now()
    if not date_start:
        date_start = date_end - timedelta(days=30)
    
    campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).all()
    campaign_ids = [c.campaign_id for c in campaigns]
    
    metrics_query = db.query(CampaignMetrics).filter(
        CampaignMetrics.campaign_id.in_(campaign_ids),
        CampaignMetrics.date_start >= date_start,
        CampaignMetrics.date_stop <= date_end
    )
    
    metrics = metrics_query.all()
    
    total_spend = sum(m.spend for m in metrics)
    total_impressions = sum(m.impressions for m in metrics)
    total_clicks = sum(m.clicks for m in metrics)
    total_conversions = sum(m.conversions for m in metrics)
    
    average_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    average_cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
    average_roas = sum(m.roas for m in metrics) / len(metrics) if metrics else 0
    
    total_campaigns = len(campaigns)
    active_campaigns = len([c for c in campaigns if c.status == 'ACTIVE'])
    
    return AnalyticsResponse(
        total_campaigns=total_campaigns,
        active_campaigns=active_campaigns,
        total_spend=total_spend,
        total_impressions=int(total_impressions),
        total_clicks=int(total_clicks),
        total_conversions=int(total_conversions),
        average_ctr=round(average_ctr, 2),
        average_cpm=round(average_cpm, 2),
        average_roas=round(average_roas, 2)
    )

@router.get("/campaigns/performance", response_model=List[CampaignPerformance])
async def get_campaign_performance(
    date_start: Optional[datetime] = Query(None),
    date_end: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    if not date_end:
        date_end = datetime.now()
    if not date_start:
        date_start = date_end - timedelta(days=30)
    
    campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).all()
    
    performance_data = []
    
    for campaign in campaigns:
        metrics = db.query(CampaignMetrics).filter(
            CampaignMetrics.campaign_id == campaign.campaign_id,
            CampaignMetrics.date_start >= date_start,
            CampaignMetrics.date_stop <= date_end
        ).all()
        
        if not metrics:
            continue
        
        total_spend = sum(m.spend for m in metrics)
        total_impressions = sum(m.impressions for m in metrics)
        total_clicks = sum(m.clicks for m in metrics)
        total_conversions = sum(m.conversions for m in metrics)
        
        ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
        avg_roas = sum(m.roas for m in metrics) / len(metrics) if metrics else 0
        
        performance_score = (
            (ctr * 0.3) +  # CTR weight
            (avg_roas * 0.4) +  # ROAS weight
            (total_conversions * 0.3)  # Conversions weight
        )
        
        performance_data.append(CampaignPerformance(
            campaign_id=campaign.campaign_id,
            campaign_name=campaign.name,
            spend=total_spend,
            impressions=int(total_impressions),
            clicks=int(total_clicks),
            conversions=int(total_conversions),
            ctr=round(ctr, 2),
            cpm=round(cpm, 2),
            roas=round(avg_roas, 2),
            performance_score=round(performance_score, 2)
        ))
    
    performance_data.sort(key=lambda x: x.performance_score, reverse=True)
    return performance_data[:limit]

@router.get("/timeseries", response_model=List[TimeSeriesData])
async def get_timeseries_data(
    date_start: Optional[datetime] = Query(None),
    date_end: Optional[datetime] = Query(None),
    campaign_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    if not date_end:
        date_end = datetime.now()
    if not date_start:
        date_start = date_end - timedelta(days=30)
    
    query = db.query(CampaignMetrics).filter(
        CampaignMetrics.date_start >= date_start,
        CampaignMetrics.date_stop <= date_end
    )
    
    if campaign_id:
        campaign = db.query(Campaign).filter(
            Campaign.campaign_id == campaign_id,
            Campaign.user_id == current_user.id
        ).first()
        if not campaign:
            return []
        
        query = query.filter(CampaignMetrics.campaign_id == campaign_id)
    else:
        user_campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).all()
        campaign_ids = [c.campaign_id for c in user_campaigns]
        query = query.filter(CampaignMetrics.campaign_id.in_(campaign_ids))
    
    metrics = query.order_by(CampaignMetrics.date_start).all()
    
    daily_data = {}
    for metric in metrics:
        date_key = metric.date_start.date()
        
        if date_key not in daily_data:
            daily_data[date_key] = {
                'spend': 0,
                'impressions': 0,
                'clicks': 0,
                'conversions': 0
            }
        
        daily_data[date_key]['spend'] += metric.spend
        daily_data[date_key]['impressions'] += metric.impressions
        daily_data[date_key]['clicks'] += metric.clicks
        daily_data[date_key]['conversions'] += metric.conversions
    
    timeseries_data = []
    for date, data in sorted(daily_data.items()):
        ctr = (data['clicks'] / data['impressions'] * 100) if data['impressions'] > 0 else 0
        cpm = (data['spend'] / data['impressions'] * 1000) if data['impressions'] > 0 else 0
        
        timeseries_data.append(TimeSeriesData(
            date=datetime.combine(date, datetime.min.time()),
            spend=data['spend'],
            impressions=int(data['impressions']),
            clicks=int(data['clicks']),
            conversions=int(data['conversions']),
            ctr=round(ctr, 2),
            cpm=round(cpm, 2)
        ))
    
    return timeseries_data

@router.get("/insights")
async def get_insights(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_sync_db)
):
    date_start = datetime.now() - timedelta(days=7)
    
    campaigns = db.query(Campaign).filter(Campaign.user_id == current_user.id).all()
    campaign_ids = [c.campaign_id for c in campaigns]
    
    recent_metrics = db.query(CampaignMetrics).filter(
        CampaignMetrics.campaign_id.in_(campaign_ids),
        CampaignMetrics.date_start >= date_start
    ).all()
    
    insights = []
    
    if recent_metrics:
        avg_ctr = sum(m.ctr for m in recent_metrics) / len(recent_metrics)
        avg_roas = sum(m.roas for m in recent_metrics) / len(recent_metrics)
        total_spend = sum(m.spend for m in recent_metrics)
        
        if avg_ctr < 1.0:
            insights.append({
                "type": "warning",
                "title": "CTR Baixo Detectado",
                "message": f"Sua CTR média está em {avg_ctr:.2f}%. Considere otimizar seus anúncios.",
                "recommendation": "Teste novos criativos ou ajuste o targeting"
            })
        
        if avg_roas < 2.0:
            insights.append({
                "type": "alert",
                "title": "ROAS Abaixo do Ideal",
                "message": f"Seu ROAS médio está em {avg_roas:.2f}. Meta recomendada: 3.0+",
                "recommendation": "Revise suas campanhas de menor performance"
            })
        
        if total_spend > 1000:
            insights.append({
                "type": "info",
                "title": "Alto Volume de Investimento",
                "message": f"Você investiu ${total_spend:.2f} nos últimos 7 dias",
                "recommendation": "Monitore de perto o ROI de suas campanhas"
            })
    
    return {"insights": insights}
