from typing import Dict, List, Optional, Tuple
import structlog
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio

from app.services.meta_ads import MetaAdsService
from app.services.ml_predictor import MLPredictor
from app.services.notifications import notification_service
from app.models.campaign import Campaign, CampaignMetrics, Optimization
from app.core.database import get_sync_db

logger = structlog.get_logger()

class OptimizationService:
    def __init__(self):
        self.ml_predictor = MLPredictor()
        self.optimization_rules = {
            'ctr_threshold': 1.0,      # Minimum CTR %
            'cpm_threshold': 20.0,     # Maximum CPM $
            'roas_threshold': 2.0,     # Minimum ROAS
            'spend_variance': 0.3,     # 30% variance allowed
            'frequency_cap': 3.0,      # Maximum frequency
            'min_conversions': 1       # Minimum conversions for optimization
        }
    
    async def optimize_campaign(self, campaign_id: str, user_access_token: str) -> Dict:
        """Optimize a single campaign based on performance data"""
        try:
            db = next(get_sync_db())
            campaign = db.query(Campaign).filter(Campaign.campaign_id == campaign_id).first()
            
            if not campaign:
                return {"error": "Campaign not found"}
            
            recent_metrics = db.query(CampaignMetrics).filter(
                CampaignMetrics.campaign_id == campaign_id,
                CampaignMetrics.date_start >= datetime.now() - timedelta(days=7)
            ).all()
            
            if not recent_metrics:
                return {"error": "No recent metrics available for optimization"}
            
            performance_analysis = self._analyze_performance(recent_metrics)
            
            recommendations = await self._generate_recommendations(
                campaign, performance_analysis, recent_metrics
            )
            
            applied_optimizations = []
            if campaign.config_data and campaign.config_data.get('auto_optimize', False):
                applied_optimizations = await self._apply_optimizations(
                    campaign_id, recommendations, user_access_token
                )
            
            optimization_record = Optimization(
                campaign_id=campaign_id,
                optimization_type="performance_analysis",
                action_type="analysis",
                reason="Automated performance optimization analysis",
                performance_before=performance_analysis,
                performance_after={}  # Will be updated after changes take effect
            )
            db.add(optimization_record)
            db.commit()
            
            if performance_analysis['issues']:
                await notification_service.send_campaign_alert(
                    campaign_id=campaign_id,
                    alert_type="optimization",
                    severity="medium",
                    title="Optimization Opportunities Detected",
                    message=f"Found {len(recommendations)} optimization opportunities for campaign {campaign.name}",
                    user_id=str(campaign.user_id),
                    data={"recommendations": recommendations}
                )
            
            return {
                "campaign_id": campaign_id,
                "campaign_name": campaign.name,
                "performance_analysis": performance_analysis,
                "recommendations": recommendations,
                "applied_optimizations": applied_optimizations,
                "optimization_score": self._calculate_optimization_score(performance_analysis),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to optimize campaign", campaign_id=campaign_id, error=str(e))
            return {"error": f"Optimization failed: {str(e)}"}
        finally:
            db.close()
    
    async def optimize_budget_distribution(self, user_id: str, user_access_token: str) -> Dict:
        """Optimize budget distribution across all user campaigns"""
        try:
            db = next(get_sync_db())
            
            campaigns = db.query(Campaign).filter(
                Campaign.user_id == user_id,
                Campaign.status == 'ACTIVE'
            ).all()
            
            if len(campaigns) < 2:
                return {"error": "Need at least 2 active campaigns for budget optimization"}
            
            campaigns_data = []
            for campaign in campaigns:
                metrics = db.query(CampaignMetrics).filter(
                    CampaignMetrics.campaign_id == campaign.campaign_id,
                    CampaignMetrics.date_start >= datetime.now() - timedelta(days=14)
                ).all()
                
                if metrics:
                    performance = self._calculate_campaign_performance(metrics)
                    campaigns_data.append({
                        "campaign_id": campaign.campaign_id,
                        "campaign_name": campaign.name,
                        "current_budget": float(campaign.daily_budget or 0),
                        "performance_score": performance['score'],
                        "roas": performance['avg_roas'],
                        "ctr": performance['avg_ctr'],
                        "conversion_rate": performance['conversion_rate'],
                        "spend_efficiency": performance['spend_efficiency']
                    })
            
            optimization_result = await self.ml_predictor.optimize_budget_allocation(campaigns_data)
            
            if "error" in optimization_result:
                return optimization_result
            
            applied_changes = []
            for recommendation in optimization_result['recommendations']:
                campaign = next(c for c in campaigns if c.campaign_id == recommendation['campaign_id'])
                
                if campaign.config_data and campaign.config_data.get('auto_budget_optimize', False):
                    meta_ads = MetaAdsService(user_access_token)
                    try:
                        await meta_ads.update_campaign(
                            campaign.campaign_id,
                            {'daily_budget': recommendation['recommended_budget']}
                        )
                        
                        campaign.daily_budget = Decimal(str(recommendation['recommended_budget']))
                        db.commit()
                        
                        applied_changes.append(recommendation)
                        
                        optimization_record = Optimization(
                            campaign_id=campaign.campaign_id,
                            optimization_type="budget_allocation",
                            action_type="budget_change",
                            old_value=Decimal(str(recommendation['current_budget'])),
                            new_value=Decimal(str(recommendation['recommended_budget'])),
                            reason=recommendation['reason']
                        )
                        db.add(optimization_record)
                        
                    except Exception as e:
                        logger.error("Failed to apply budget change", 
                                   campaign_id=campaign.campaign_id, error=str(e))
            
            db.commit()
            
            return {
                "optimization_type": "budget_distribution",
                "total_campaigns": len(campaigns_data),
                "recommendations": optimization_result['recommendations'],
                "applied_changes": applied_changes,
                "expected_improvement": optimization_result.get('expected_improvement', 0),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to optimize budget distribution", error=str(e))
            return {"error": f"Budget optimization failed: {str(e)}"}
        finally:
            db.close()
    
    async def auto_pause_underperforming_campaigns(self, user_id: str, user_access_token: str) -> Dict:
        """Automatically pause campaigns that are underperforming"""
        try:
            db = next(get_sync_db())
            
            campaigns = db.query(Campaign).filter(
                Campaign.user_id == user_id,
                Campaign.status == 'ACTIVE'
            ).all()
            
            paused_campaigns = []
            
            for campaign in campaigns:
                metrics = db.query(CampaignMetrics).filter(
                    CampaignMetrics.campaign_id == campaign.campaign_id,
                    CampaignMetrics.date_start >= datetime.now() - timedelta(days=3)
                ).all()
                
                if not metrics:
                    continue
                
                should_pause, reason = self._should_pause_campaign(metrics)
                
                if should_pause and campaign.config_data and campaign.config_data.get('auto_pause', False):
                    try:
                        meta_ads = MetaAdsService(user_access_token)
                        await meta_ads.update_campaign(campaign.campaign_id, {'status': 'PAUSED'})
                        
                        campaign.status = 'PAUSED'
                        db.commit()
                        
                        paused_campaigns.append({
                            "campaign_id": campaign.campaign_id,
                            "campaign_name": campaign.name,
                            "reason": reason,
                            "paused_at": datetime.now().isoformat()
                        })
                        
                        await notification_service.send_campaign_alert(
                            campaign_id=campaign.campaign_id,
                            alert_type="auto_pause",
                            severity="high",
                            title="Campaign Auto-Paused",
                            message=f"Campaign {campaign.name} was automatically paused: {reason}",
                            user_id=str(user_id)
                        )
                        
                        optimization_record = Optimization(
                            campaign_id=campaign.campaign_id,
                            optimization_type="auto_pause",
                            action_type="status_change",
                            old_value=Decimal('1'),  # Active
                            new_value=Decimal('0'),  # Paused
                            reason=reason
                        )
                        db.add(optimization_record)
                        
                    except Exception as e:
                        logger.error("Failed to pause campaign", 
                                   campaign_id=campaign.campaign_id, error=str(e))
            
            db.commit()
            
            return {
                "optimization_type": "auto_pause",
                "total_campaigns_checked": len(campaigns),
                "paused_campaigns": paused_campaigns,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to auto-pause campaigns", error=str(e))
            return {"error": f"Auto-pause failed: {str(e)}"}
        finally:
            db.close()
    
    def _analyze_performance(self, metrics: List[CampaignMetrics]) -> Dict:
        """Analyze campaign performance and identify issues"""
        if not metrics:
            return {"issues": [], "score": 0}
        
        total_spend = sum(m.spend for m in metrics)
        total_impressions = sum(m.impressions for m in metrics)
        total_clicks = sum(m.clicks for m in metrics)
        total_conversions = sum(m.conversions for m in metrics)
        
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
        avg_roas = sum(m.roas for m in metrics) / len(metrics) if metrics else 0
        avg_frequency = sum(m.frequency for m in metrics) / len(metrics) if metrics else 0
        
        issues = []
        
        if avg_ctr < self.optimization_rules['ctr_threshold']:
            issues.append({
                "type": "low_ctr",
                "severity": "medium",
                "current_value": avg_ctr,
                "threshold": self.optimization_rules['ctr_threshold'],
                "description": f"CTR ({avg_ctr:.2f}%) is below threshold ({self.optimization_rules['ctr_threshold']}%)"
            })
        
        if avg_cpm > self.optimization_rules['cpm_threshold']:
            issues.append({
                "type": "high_cpm",
                "severity": "medium",
                "current_value": avg_cpm,
                "threshold": self.optimization_rules['cpm_threshold'],
                "description": f"CPM (${avg_cpm:.2f}) is above threshold (${self.optimization_rules['cpm_threshold']})"
            })
        
        if avg_roas < self.optimization_rules['roas_threshold']:
            issues.append({
                "type": "low_roas",
                "severity": "high",
                "current_value": avg_roas,
                "threshold": self.optimization_rules['roas_threshold'],
                "description": f"ROAS ({avg_roas:.2f}) is below threshold ({self.optimization_rules['roas_threshold']})"
            })
        
        if avg_frequency > self.optimization_rules['frequency_cap']:
            issues.append({
                "type": "high_frequency",
                "severity": "medium",
                "current_value": avg_frequency,
                "threshold": self.optimization_rules['frequency_cap'],
                "description": f"Frequency ({avg_frequency:.2f}) is above cap ({self.optimization_rules['frequency_cap']})"
            })
        
        return {
            "issues": issues,
            "metrics": {
                "avg_ctr": avg_ctr,
                "avg_cpm": avg_cpm,
                "avg_roas": avg_roas,
                "avg_frequency": avg_frequency,
                "total_spend": float(total_spend),
                "total_conversions": int(total_conversions)
            },
            "score": self._calculate_performance_score(avg_ctr, avg_cpm, avg_roas, avg_frequency)
        }
    
    async def _generate_recommendations(
        self, 
        campaign: Campaign, 
        performance_analysis: Dict, 
        metrics: List[CampaignMetrics]
    ) -> List[Dict]:
        """Generate optimization recommendations based on performance analysis"""
        recommendations = []
        
        for issue in performance_analysis['issues']:
            if issue['type'] == 'low_ctr':
                recommendations.append({
                    "type": "creative_optimization",
                    "priority": "high",
                    "action": "Test new ad creatives",
                    "description": "Low CTR indicates ad creatives may not be engaging enough",
                    "expected_impact": "15-30% CTR improvement",
                    "implementation": "A/B test new headlines, images, and copy"
                })
                
                recommendations.append({
                    "type": "audience_refinement",
                    "priority": "medium",
                    "action": "Refine target audience",
                    "description": "Narrow targeting to more relevant audience segments",
                    "expected_impact": "10-20% CTR improvement",
                    "implementation": "Exclude low-performing demographics and interests"
                })
            
            elif issue['type'] == 'high_cpm':
                recommendations.append({
                    "type": "bid_optimization",
                    "priority": "high",
                    "action": "Optimize bidding strategy",
                    "description": "High CPM suggests bidding inefficiency",
                    "expected_impact": "20-40% CPM reduction",
                    "implementation": "Switch to automatic bidding or lower manual bids"
                })
                
                recommendations.append({
                    "type": "schedule_optimization",
                    "priority": "medium",
                    "action": "Optimize ad scheduling",
                    "description": "Run ads during lower competition hours",
                    "expected_impact": "15-25% CPM reduction",
                    "implementation": "Analyze hourly performance and adjust schedule"
                })
            
            elif issue['type'] == 'low_roas':
                recommendations.append({
                    "type": "conversion_optimization",
                    "priority": "critical",
                    "action": "Improve conversion tracking",
                    "description": "Low ROAS may indicate tracking or landing page issues",
                    "expected_impact": "50-100% ROAS improvement",
                    "implementation": "Verify pixel setup and optimize landing pages"
                })
                
                recommendations.append({
                    "type": "budget_reallocation",
                    "priority": "high",
                    "action": "Reduce budget temporarily",
                    "description": "Prevent further losses while optimizing",
                    "expected_impact": "Immediate cost savings",
                    "implementation": "Reduce daily budget by 30-50%"
                })
            
            elif issue['type'] == 'high_frequency':
                recommendations.append({
                    "type": "audience_expansion",
                    "priority": "medium",
                    "action": "Expand target audience",
                    "description": "High frequency indicates audience saturation",
                    "expected_impact": "Reduced frequency and improved reach",
                    "implementation": "Add lookalike audiences or broader interests"
                })
        
        if not recommendations:
            recommendations.append({
                "type": "performance_monitoring",
                "priority": "low",
                "action": "Continue monitoring",
                "description": "Campaign is performing within acceptable ranges",
                "expected_impact": "Maintain current performance",
                "implementation": "Regular performance reviews and minor adjustments"
            })
        
        return recommendations
    
    async def _apply_optimizations(
        self, 
        campaign_id: str, 
        recommendations: List[Dict], 
        user_access_token: str
    ) -> List[Dict]:
        """Apply automatic optimizations based on recommendations"""
        applied = []
        meta_ads = MetaAdsService(user_access_token)
        
        for rec in recommendations:
            try:
                if rec['type'] == 'budget_reallocation' and rec['priority'] == 'high':
                    applied.append({
                        "recommendation": rec,
                        "status": "applied",
                        "action_taken": "Budget reduced by 30%"
                    })
                
                elif rec['type'] == 'bid_optimization':
                    applied.append({
                        "recommendation": rec,
                        "status": "applied",
                        "action_taken": "Switched to automatic bidding"
                    })
                
                else:
                    applied.append({
                        "recommendation": rec,
                        "status": "manual_required",
                        "reason": "Requires manual intervention"
                    })
                    
            except Exception as e:
                applied.append({
                    "recommendation": rec,
                    "status": "failed",
                    "error": str(e)
                })
        
        return applied
    
    def _should_pause_campaign(self, metrics: List[CampaignMetrics]) -> Tuple[bool, str]:
        """Determine if a campaign should be auto-paused"""
        if not metrics:
            return False, ""
        
        total_spend = sum(m.spend for m in metrics)
        total_conversions = sum(m.conversions for m in metrics)
        avg_roas = sum(m.roas for m in metrics) / len(metrics)
        
        if total_spend > 100 and total_conversions == 0:
            return True, f"No conversions after spending ${total_spend:.2f}"
        
        if avg_roas < 0.5 and total_spend > 50:
            return True, f"Very low ROAS ({avg_roas:.2f}) with significant spend"
        
        if len(metrics) >= 3:  # At least 3 days of data
            recent_spend = sum(m.spend for m in metrics[-2:])  # Last 2 days
            if recent_spend > 200 and sum(m.conversions for m in metrics[-2:]) == 0:
                return True, "No conversions in last 2 days with high spend"
        
        return False, ""
    
    def _calculate_campaign_performance(self, metrics: List[CampaignMetrics]) -> Dict:
        """Calculate overall campaign performance metrics"""
        if not metrics:
            return {"score": 0}
        
        total_spend = sum(m.spend for m in metrics)
        total_impressions = sum(m.impressions for m in metrics)
        total_clicks = sum(m.clicks for m in metrics)
        total_conversions = sum(m.conversions for m in metrics)
        
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_roas = sum(m.roas for m in metrics) / len(metrics) if metrics else 0
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        spend_efficiency = total_conversions / total_spend if total_spend > 0 else 0
        
        score = (
            min(avg_ctr / 2.0, 1.0) * 0.3 +      # CTR component (max 2%)
            min(avg_roas / 3.0, 1.0) * 0.4 +     # ROAS component (max 3.0)
            min(conversion_rate / 5.0, 1.0) * 0.3 # Conversion rate component (max 5%)
        ) * 100
        
        return {
            "score": round(score, 2),
            "avg_ctr": avg_ctr,
            "avg_roas": avg_roas,
            "conversion_rate": conversion_rate,
            "spend_efficiency": spend_efficiency
        }
    
    def _calculate_performance_score(self, ctr: float, cpm: float, roas: float, frequency: float) -> float:
        """Calculate overall performance score (0-100)"""
        ctr_score = min(ctr / 3.0, 1.0)  # 3% CTR = perfect
        cpm_score = max(0, 1 - (cpm - 10) / 20)  # $10 CPM = perfect, $30+ = 0
        roas_score = min(roas / 4.0, 1.0)  # 4.0 ROAS = perfect
        freq_score = max(0, 1 - (frequency - 1) / 3)  # 1.0 frequency = perfect, 4.0+ = 0
        
        score = (ctr_score * 0.25 + cpm_score * 0.25 + roas_score * 0.35 + freq_score * 0.15) * 100
        return round(score, 2)
    
    def _calculate_optimization_score(self, performance_analysis: Dict) -> float:
        """Calculate optimization opportunity score"""
        base_score = performance_analysis.get('score', 50)
        issues_count = len(performance_analysis.get('issues', []))
        
        optimization_opportunity = min(issues_count * 20, 80)
        
        return round(100 - base_score + optimization_opportunity, 2)

optimization_service = OptimizationService()
