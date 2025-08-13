from celery import current_task
from datetime import datetime, timedelta
from typing import List, Dict
import structlog
from sqlalchemy.orm import Session

from app.workers.celery_app import celery_app
from app.core.database import get_sync_db
from app.models.user import User
from app.models.campaign import Campaign, CampaignMetrics, Alert
from app.services.meta_ads import MetaAdsService
from app.services.ai_service import AIService
from app.services.ml_predictor import MLPredictor
from app.services.notifications import notification_service
from app.services.optimization import optimization_service

logger = structlog.get_logger()

@celery_app.task(bind=True)
async def sync_all_campaign_metrics(self):
    """Sync metrics for all active campaigns"""
    try:
        db = next(get_sync_db())
        
        users = db.query(User).filter(
            User.facebook_access_token.isnot(None),
            User.is_active == True
        ).all()
        
        total_synced = 0
        errors = []
        
        for user in users:
            try:
                campaigns = db.query(Campaign).filter(
                    Campaign.user_id == user.id,
                    Campaign.status.in_(['ACTIVE', 'PAUSED'])
                ).all()
                
                if not campaigns:
                    continue
                
                meta_ads = MetaAdsService(user.facebook_access_token)
                
                for campaign in campaigns:
                    try:
                        date_start = datetime.now() - timedelta(days=3)
                        insights = await meta_ads.get_campaign_insights(
                            campaign.campaign_id, 
                            date_start=date_start
                        )
                        
                        for insight in insights:
                            existing = db.query(CampaignMetrics).filter(
                                CampaignMetrics.campaign_id == campaign.campaign_id,
                                CampaignMetrics.date_start == insight['date_start']
                            ).first()
                            
                            if not existing:
                                metric = CampaignMetrics(
                                    campaign_id=campaign.campaign_id,
                                    date_start=insight['date_start'],
                                    date_stop=insight['date_stop'],
                                    impressions=insight['impressions'],
                                    clicks=insight['clicks'],
                                    conversions=insight['conversions'],
                                    spend=insight['spend'],
                                    cpm=insight['cpm'],
                                    ctr=insight['ctr'],
                                    roas=insight['roas'],
                                    frequency=insight['frequency'],
                                    reach=insight['reach'],
                                    cost_per_conversion=insight['cost_per_conversion']
                                )
                                db.add(metric)
                                total_synced += 1
                        
                        db.commit()
                        
                    except Exception as e:
                        logger.error("Failed to sync campaign metrics", 
                                   campaign_id=campaign.campaign_id, error=str(e))
                        errors.append(f"Campaign {campaign.campaign_id}: {str(e)}")
                        
            except Exception as e:
                logger.error("Failed to sync user campaigns", user_id=str(user.id), error=str(e))
                errors.append(f"User {user.email}: {str(e)}")
        
        db.close()
        
        result = {
            "task": "sync_all_campaign_metrics",
            "total_synced": total_synced,
            "users_processed": len(users),
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Campaign metrics sync completed", **result)
        return result
        
    except Exception as e:
        logger.error("Failed to sync campaign metrics", error=str(e))
        raise self.retry(exc=e, countdown=300, max_retries=3)

@celery_app.task(bind=True)
async def optimize_all_campaigns(self):
    """Run optimization for all active campaigns"""
    try:
        db = next(get_sync_db())
        
        users = db.query(User).filter(
            User.facebook_access_token.isnot(None),
            User.is_active == True
        ).all()
        
        total_optimized = 0
        results = []
        
        for user in users:
            try:
                campaigns = db.query(Campaign).filter(
                    Campaign.user_id == user.id,
                    Campaign.status == 'ACTIVE'
                ).all()
                
                for campaign in campaigns:
                    if campaign.config_data and campaign.config_data.get('auto_optimize', False):
                        try:
                            result = await optimization_service.optimize_campaign(
                                campaign.campaign_id,
                                user.facebook_access_token
                            )
                            
                            if "error" not in result:
                                total_optimized += 1
                                results.append({
                                    "campaign_id": campaign.campaign_id,
                                    "optimization_score": result.get('optimization_score', 0),
                                    "recommendations": len(result.get('recommendations', [])),
                                    "applied_optimizations": len(result.get('applied_optimizations', []))
                                })
                            
                        except Exception as e:
                            logger.error("Failed to optimize campaign", 
                                       campaign_id=campaign.campaign_id, error=str(e))
                
            except Exception as e:
                logger.error("Failed to optimize user campaigns", user_id=str(user.id), error=str(e))
        
        db.close()
        
        result = {
            "task": "optimize_all_campaigns",
            "total_optimized": total_optimized,
            "users_processed": len(users),
            "optimization_results": results,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Campaign optimization completed", **result)
        return result
        
    except Exception as e:
        logger.error("Failed to optimize campaigns", error=str(e))
        raise self.retry(exc=e, countdown=600, max_retries=2)

@celery_app.task(bind=True)
async def generate_daily_ai_insights(self):
    """Generate AI insights for all campaigns"""
    try:
        db = next(get_sync_db())
        ai_service = AIService()
        
        users = db.query(User).filter(User.is_active == True).all()
        
        total_insights = 0
        
        for user in users:
            try:
                campaigns = db.query(Campaign).filter(
                    Campaign.user_id == user.id,
                    Campaign.status.in_(['ACTIVE', 'PAUSED'])
                ).all()
                
                for campaign in campaigns:
                    metrics = db.query(CampaignMetrics).filter(
                        CampaignMetrics.campaign_id == campaign.campaign_id,
                        CampaignMetrics.date_start >= datetime.now() - timedelta(days=7)
                    ).all()
                    
                    if metrics:
                        campaign_data = {
                            "name": campaign.name,
                            "objective": campaign.objective,
                            "status": campaign.status,
                            "daily_budget": float(campaign.daily_budget or 0)
                        }
                        
                        metrics_data = [
                            {
                                "date_start": m.date_start,
                                "spend": float(m.spend),
                                "impressions": int(m.impressions),
                                "clicks": int(m.clicks),
                                "conversions": int(m.conversions),
                                "ctr": float(m.ctr),
                                "cpm": float(m.cpm),
                                "roas": float(m.roas)
                            }
                            for m in metrics
                        ]
                        
                        insight = await ai_service.generate_campaign_insights(
                            campaign_data, metrics_data
                        )
                        
                        if insight and "error" not in insight:
                            from app.models.campaign import AIInsight
                            
                            ai_insight = AIInsight(
                                user_id=user.id,
                                insight_type=insight['insight_type'],
                                title=insight['title'],
                                content=insight['content'],
                                confidence_score=insight.get('confidence_score', 0.5),
                                data={
                                    "campaign_id": campaign.campaign_id,
                                    "quality_score": insight.get('quality_score', 0),
                                    "recommendations": insight.get('recommendations', [])
                                }
                            )
                            
                            db.add(ai_insight)
                            total_insights += 1
                
                db.commit()
                
            except Exception as e:
                logger.error("Failed to generate insights for user", user_id=str(user.id), error=str(e))
        
        db.close()
        
        result = {
            "task": "generate_daily_ai_insights",
            "total_insights": total_insights,
            "users_processed": len(users),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("AI insights generation completed", **result)
        return result
        
    except Exception as e:
        logger.error("Failed to generate AI insights", error=str(e))
        raise self.retry(exc=e, countdown=900, max_retries=2)

@celery_app.task(bind=True)
async def send_daily_reports(self):
    """Send daily performance reports to all users"""
    try:
        db = next(get_sync_db())
        
        users = db.query(User).filter(User.is_active == True).all()
        reports_sent = 0
        
        for user in users:
            try:
                today = datetime.now().date()
                today_start = datetime.combine(today, datetime.min.time())
                today_end = datetime.combine(today, datetime.max.time())
                
                campaigns = db.query(Campaign).filter(Campaign.user_id == user.id).all()
                campaign_ids = [c.campaign_id for c in campaigns]
                
                today_metrics = db.query(CampaignMetrics).filter(
                    CampaignMetrics.campaign_id.in_(campaign_ids),
                    CampaignMetrics.date_start >= today_start,
                    CampaignMetrics.date_stop <= today_end
                ).all()
                
                unread_alerts = db.query(Alert).filter(
                    Alert.user_id == user.id,
                    Alert.is_read == False
                ).count()
                
                report_data = {
                    "user_email": user.email,
                    "total_campaigns": len(campaigns),
                    "active_campaigns": len([c for c in campaigns if c.status == 'ACTIVE']),
                    "total_spend": sum(m.spend for m in today_metrics),
                    "total_impressions": sum(m.impressions for m in today_metrics),
                    "total_clicks": sum(m.clicks for m in today_metrics),
                    "total_conversions": sum(m.conversions for m in today_metrics),
                    "avg_ctr": (sum(m.ctr for m in today_metrics) / len(today_metrics)) if today_metrics else 0,
                    "avg_cpm": (sum(m.cpm for m in today_metrics) / len(today_metrics)) if today_metrics else 0,
                    "avg_roas": (sum(m.roas for m in today_metrics) / len(today_metrics)) if today_metrics else 0,
                    "new_alerts": unread_alerts,
                    "unresolved_alerts": unread_alerts
                }
                
                await notification_service.send_daily_report(str(user.id), report_data)
                reports_sent += 1
                
            except Exception as e:
                logger.error("Failed to send daily report", user_id=str(user.id), error=str(e))
        
        db.close()
        
        result = {
            "task": "send_daily_reports",
            "reports_sent": reports_sent,
            "users_processed": len(users),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Daily reports sent", **result)
        return result
        
    except Exception as e:
        logger.error("Failed to send daily reports", error=str(e))
        raise self.retry(exc=e, countdown=1800, max_retries=2)

@celery_app.task(bind=True)
async def monitor_performance_alerts(self):
    """Monitor campaign performance and send alerts"""
    try:
        db = next(get_sync_db())
        
        campaigns = db.query(Campaign).filter(Campaign.status == 'ACTIVE').all()
        alerts_sent = 0
        
        for campaign in campaigns:
            try:
                recent_metrics = db.query(CampaignMetrics).filter(
                    CampaignMetrics.campaign_id == campaign.campaign_id,
                    CampaignMetrics.date_start >= datetime.now() - timedelta(hours=24)
                ).all()
                
                if not recent_metrics:
                    continue
                
                total_spend = sum(m.spend for m in recent_metrics)
                total_conversions = sum(m.conversions for m in recent_metrics)
                avg_ctr = sum(m.ctr for m in recent_metrics) / len(recent_metrics)
                avg_roas = sum(m.roas for m in recent_metrics) / len(recent_metrics)
                
                if campaign.daily_budget and total_spend >= float(campaign.daily_budget) * 0.9:
                    await notification_service.send_budget_alert(
                        campaign_id=campaign.campaign_id,
                        spent_amount=float(total_spend),
                        budget_limit=float(campaign.daily_budget),
                        user_id=str(campaign.user_id)
                    )
                    alerts_sent += 1
                
                if avg_ctr < 1.0:  # CTR below 1%
                    await notification_service.send_performance_alert(
                        campaign_id=campaign.campaign_id,
                        metric="ctr",
                        current_value=avg_ctr,
                        threshold=1.0,
                        user_id=str(campaign.user_id)
                    )
                    alerts_sent += 1
                
                if avg_roas < 1.5:  # ROAS below 1.5
                    await notification_service.send_performance_alert(
                        campaign_id=campaign.campaign_id,
                        metric="roas",
                        current_value=avg_roas,
                        threshold=1.5,
                        user_id=str(campaign.user_id)
                    )
                    alerts_sent += 1
                
                if total_spend > 50 and total_conversions == 0:
                    await notification_service.send_campaign_alert(
                        campaign_id=campaign.campaign_id,
                        alert_type="no_conversions",
                        severity="high",
                        title="No Conversions Alert",
                        message=f"Campaign has spent ${total_spend:.2f} with no conversions in the last 24 hours",
                        user_id=str(campaign.user_id)
                    )
                    alerts_sent += 1
                
            except Exception as e:
                logger.error("Failed to monitor campaign", campaign_id=campaign.campaign_id, error=str(e))
        
        db.close()
        
        result = {
            "task": "monitor_performance_alerts",
            "campaigns_monitored": len(campaigns),
            "alerts_sent": alerts_sent,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Performance monitoring completed", **result)
        return result
        
    except Exception as e:
        logger.error("Failed to monitor performance", error=str(e))
        raise self.retry(exc=e, countdown=300, max_retries=3)

@celery_app.task(bind=True)
async def auto_pause_underperforming_campaigns(self):
    """Auto-pause campaigns that are underperforming"""
    try:
        db = next(get_sync_db())
        
        users = db.query(User).filter(
            User.facebook_access_token.isnot(None),
            User.is_active == True
        ).all()
        
        total_paused = 0
        
        for user in users:
            try:
                result = await optimization_service.auto_pause_underperforming_campaigns(
                    str(user.id),
                    user.facebook_access_token
                )
                
                if "error" not in result:
                    total_paused += len(result.get('paused_campaigns', []))
                
            except Exception as e:
                logger.error("Failed to auto-pause campaigns for user", user_id=str(user.id), error=str(e))
        
        db.close()
        
        result = {
            "task": "auto_pause_underperforming_campaigns",
            "users_processed": len(users),
            "campaigns_paused": total_paused,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Auto-pause task completed", **result)
        return result
        
    except Exception as e:
        logger.error("Failed to auto-pause campaigns", error=str(e))
        raise self.retry(exc=e, countdown=1800, max_retries=2)

@celery_app.task(bind=True)
async def cleanup_old_data(self):
    """Clean up old data to maintain database performance"""
    try:
        db = next(get_sync_db())
        
        cutoff_date = datetime.now() - timedelta(days=90)
        
        old_metrics = db.query(CampaignMetrics).filter(
            CampaignMetrics.date_start < cutoff_date
        ).delete()
        
        old_alerts = db.query(Alert).filter(
            Alert.created_at < datetime.now() - timedelta(days=30),
            Alert.resolved_at.isnot(None)
        ).delete()
        
        from app.models.campaign import SystemLog
        old_logs = db.query(SystemLog).filter(
            SystemLog.created_at < datetime.now() - timedelta(days=30)
        ).delete()
        
        db.commit()
        db.close()
        
        result = {
            "task": "cleanup_old_data",
            "metrics_deleted": old_metrics,
            "alerts_deleted": old_alerts,
            "logs_deleted": old_logs,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Data cleanup completed", **result)
        return result
        
    except Exception as e:
        logger.error("Failed to cleanup old data", error=str(e))
        raise self.retry(exc=e, countdown=3600, max_retries=2)

@celery_app.task(bind=True)
async def train_ml_models(self):
    """Train ML models with latest data"""
    try:
        db = next(get_sync_db())
        ml_predictor = MLPredictor()
        
        historical_data = []
        
        cutoff_date = datetime.now() - timedelta(days=60)
        metrics = db.query(CampaignMetrics).filter(
            CampaignMetrics.date_start >= cutoff_date
        ).all()
        
        for metric in metrics:
            campaign = db.query(Campaign).filter(
                Campaign.campaign_id == metric.campaign_id
            ).first()
            
            if campaign:
                historical_data.append({
                    "date_start": metric.date_start,
                    "daily_budget": float(campaign.daily_budget or 0),
                    "impressions": int(metric.impressions),
                    "clicks": int(metric.clicks),
                    "conversions": int(metric.conversions),
                    "spend": float(metric.spend),
                    "ctr": float(metric.ctr),
                    "cpm": float(metric.cpm),
                    "roas": float(metric.roas),
                    "frequency": float(metric.frequency)
                })
        
        training_result = await ml_predictor.train_performance_predictor(historical_data)
        
        db.close()
        
        result = {
            "task": "train_ml_models",
            "training_data_points": len(historical_data),
            "training_result": training_result,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("ML model training completed", **result)
        return result
        
    except Exception as e:
        logger.error("Failed to train ML models", error=str(e))
        raise self.retry(exc=e, countdown=3600, max_retries=2)

@celery_app.task
async def sync_single_campaign_metrics(campaign_id: str, user_access_token: str):
    """Sync metrics for a single campaign"""
    try:
        meta_ads = MetaAdsService(user_access_token)
        insights = await meta_ads.get_campaign_insights(campaign_id)
        
        db = next(get_sync_db())
        
        synced_count = 0
        for insight in insights:
            existing = db.query(CampaignMetrics).filter(
                CampaignMetrics.campaign_id == campaign_id,
                CampaignMetrics.date_start == insight['date_start']
            ).first()
            
            if not existing:
                metric = CampaignMetrics(
                    campaign_id=campaign_id,
                    date_start=insight['date_start'],
                    date_stop=insight['date_stop'],
                    impressions=insight['impressions'],
                    clicks=insight['clicks'],
                    conversions=insight['conversions'],
                    spend=insight['spend'],
                    cpm=insight['cpm'],
                    ctr=insight['ctr'],
                    roas=insight['roas'],
                    frequency=insight['frequency'],
                    reach=insight['reach'],
                    cost_per_conversion=insight['cost_per_conversion']
                )
                db.add(metric)
                synced_count += 1
        
        db.commit()
        db.close()
        
        return {
            "campaign_id": campaign_id,
            "synced_metrics": synced_count,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to sync single campaign metrics", campaign_id=campaign_id, error=str(e))
        raise e

@celery_app.task
async def generate_campaign_predictions(campaign_id: str, days_ahead: int = 7):
    """Generate predictions for a specific campaign"""
    try:
        db = next(get_sync_db())
        ml_predictor = MLPredictor()
        
        campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
        if not campaign:
            return {"error": "Campaign not found"}
        
        historical_metrics = db.query(CampaignMetrics).filter(
            CampaignMetrics.campaign_id == campaign_id,
            CampaignMetrics.date_start >= datetime.now() - timedelta(days=30)
        ).all()
        
        if not historical_metrics:
            return {"error": "No historical data available"}
        
        campaign_data = {
            "campaign_id": campaign_id,
            "daily_budget": float(campaign.daily_budget or 0),
            "avg_impressions": sum(m.impressions for m in historical_metrics) / len(historical_metrics),
            "avg_clicks": sum(m.clicks for m in historical_metrics) / len(historical_metrics),
            "avg_ctr": sum(m.ctr for m in historical_metrics) / len(historical_metrics),
            "avg_cpm": sum(m.cpm for m in historical_metrics) / len(historical_metrics)
        }
        
        predictions = await ml_predictor.predict_campaign_performance(campaign_data, days_ahead)
        
        db.close()
        
        return predictions
        
    except Exception as e:
        logger.error("Failed to generate campaign predictions", campaign_id=campaign_id, error=str(e))
        raise e
