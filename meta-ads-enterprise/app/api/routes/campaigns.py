from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

from app.core.database import get_sync_db
from app.models.campaign import Campaign, CampaignMetrics
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.meta_ads import MetaAdsService

router = APIRouter()

class CampaignCreate(BaseModel):
    name: str
    objective: str
    daily_budget: Optional[Decimal] = None
    total_budget: Optional[Decimal] = None
    config_data: Optional[dict] = None

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    daily_budget: Optional[Decimal] = None
    total_budget: Optional[Decimal] = None
    config_data: Optional[dict] = None

class CampaignResponse(BaseModel):
    id: str
    campaign_id: str
    name: str
    objective: str
    status: str
    daily_budget: Optional[Decimal]
    total_budget: Optional[Decimal]
    config_data: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class MetricsResponse(BaseModel):
    id: str
    campaign_id: str
    date_start: datetime
    date_stop: datetime
    impressions: Decimal
    clicks: Decimal
    conversions: Decimal
    spend: Decimal
    cpm: Decimal
    ctr: Decimal
    roas: Decimal
    frequency: Decimal
    reach: Decimal
    cost_per_conversion: Decimal
    created_at: datetime

    class Config:
        from_attributes = True

@router.get("/", response_model=List[CampaignResponse])
async def get_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    query = db.query(Campaign).filter(Campaign.user_id == current_user.id)
    
    if status:
        query = query.filter(Campaign.status == status)
    
    campaigns = query.offset(skip).limit(limit).all()
    return campaigns

@router.post("/", response_model=CampaignResponse)
async def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    meta_ads_service = MetaAdsService(current_user.facebook_access_token)
    
    try:
        fb_campaign = await meta_ads_service.create_campaign(
            name=campaign_data.name,
            objective=campaign_data.objective,
            daily_budget=campaign_data.daily_budget,
            total_budget=campaign_data.total_budget
        )
        
        db_campaign = Campaign(
            campaign_id=fb_campaign['id'],
            user_id=current_user.id,
            name=campaign_data.name,
            objective=campaign_data.objective,
            status=fb_campaign.get('status', 'PAUSED'),
            daily_budget=campaign_data.daily_budget,
            total_budget=campaign_data.total_budget,
            config_data=campaign_data.config_data
        )
        
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
        
        return db_campaign
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create campaign: {str(e)}")

@router.get("/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.campaign_id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return campaign

@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: str,
    campaign_data: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.campaign_id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    meta_ads_service = MetaAdsService(current_user.facebook_access_token)
    
    try:
        update_data = campaign_data.dict(exclude_unset=True)
        if update_data:
            await meta_ads_service.update_campaign(campaign_id, update_data)
            
            for field, value in update_data.items():
                setattr(campaign, field, value)
            
            db.commit()
            db.refresh(campaign)
        
        return campaign
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to update campaign: {str(e)}")

@router.delete("/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.campaign_id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    meta_ads_service = MetaAdsService(current_user.facebook_access_token)
    
    try:
        await meta_ads_service.delete_campaign(campaign_id)
        
        db.delete(campaign)
        db.commit()
        
        return {"message": "Campaign deleted successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to delete campaign: {str(e)}")

@router.get("/{campaign_id}/metrics", response_model=List[MetricsResponse])
async def get_campaign_metrics(
    campaign_id: str,
    date_start: Optional[datetime] = None,
    date_end: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.campaign_id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    query = db.query(CampaignMetrics).filter(CampaignMetrics.campaign_id == campaign_id)
    
    if date_start:
        query = query.filter(CampaignMetrics.date_start >= date_start)
    if date_end:
        query = query.filter(CampaignMetrics.date_stop <= date_end)
    
    metrics = query.order_by(CampaignMetrics.date_start.desc()).all()
    return metrics

@router.post("/{campaign_id}/sync-metrics")
async def sync_campaign_metrics(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_sync_db)
):
    campaign = db.query(Campaign).filter(
        Campaign.campaign_id == campaign_id,
        Campaign.user_id == current_user.id
    ).first()
    
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    meta_ads_service = MetaAdsService(current_user.facebook_access_token)
    
    try:
        metrics_data = await meta_ads_service.get_campaign_insights(campaign_id)
        
        for metric in metrics_data:
            db_metric = CampaignMetrics(
                campaign_id=campaign_id,
                date_start=metric['date_start'],
                date_stop=metric['date_stop'],
                impressions=metric.get('impressions', 0),
                clicks=metric.get('clicks', 0),
                conversions=metric.get('conversions', 0),
                spend=metric.get('spend', 0),
                cpm=metric.get('cpm', 0),
                ctr=metric.get('ctr', 0),
                roas=metric.get('roas', 0),
                frequency=metric.get('frequency', 0),
                reach=metric.get('reach', 0),
                cost_per_conversion=metric.get('cost_per_conversion', 0)
            )
            db.add(db_metric)
        
        db.commit()
        
        return {"message": f"Synced {len(metrics_data)} metric records"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to sync metrics: {str(e)}")
