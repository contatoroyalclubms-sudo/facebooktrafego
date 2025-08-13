from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from typing import Dict, List, Optional
import structlog
from datetime import datetime, timedelta
from app.core.config import settings

logger = structlog.get_logger()

class MetaAdsService:
    def __init__(self, access_token: str, ad_account_id: str = None):
        self.access_token = access_token
        self.ad_account_id = ad_account_id or settings.FACEBOOK_AD_ACCOUNT_ID
        
        FacebookAdsApi.init(
            app_id=settings.FACEBOOK_APP_ID,
            app_secret=settings.FACEBOOK_APP_SECRET,
            access_token=access_token
        )
        
        self.ad_account = AdAccount(f'act_{self.ad_account_id}')
    
    async def create_campaign(
        self, 
        name: str, 
        objective: str, 
        daily_budget: Optional[float] = None,
        total_budget: Optional[float] = None
    ) -> Dict:
        """Create a new campaign"""
        try:
            campaign_data = {
                Campaign.Field.name: name,
                Campaign.Field.objective: objective,
                Campaign.Field.status: Campaign.Status.paused,
            }
            
            if daily_budget:
                campaign_data[Campaign.Field.daily_budget] = int(daily_budget * 100)  # Convert to cents
            elif total_budget:
                campaign_data[Campaign.Field.lifetime_budget] = int(total_budget * 100)
            
            campaign = self.ad_account.create_campaign(params=campaign_data)
            
            logger.info("Campaign created", campaign_id=campaign['id'], name=name)
            
            return {
                'id': campaign['id'],
                'name': name,
                'objective': objective,
                'status': 'PAUSED'
            }
            
        except Exception as e:
            logger.error("Failed to create campaign", error=str(e), name=name)
            raise Exception(f"Meta Ads API error: {str(e)}")
    
    async def update_campaign(self, campaign_id: str, update_data: Dict) -> Dict:
        """Update an existing campaign"""
        try:
            campaign = Campaign(campaign_id)
            
            fb_update_data = {}
            
            if 'name' in update_data:
                fb_update_data[Campaign.Field.name] = update_data['name']
            
            if 'status' in update_data:
                status_mapping = {
                    'ACTIVE': Campaign.Status.active,
                    'PAUSED': Campaign.Status.paused,
                    'DELETED': Campaign.Status.deleted
                }
                fb_update_data[Campaign.Field.status] = status_mapping.get(
                    update_data['status'], Campaign.Status.paused
                )
            
            if 'daily_budget' in update_data and update_data['daily_budget']:
                fb_update_data[Campaign.Field.daily_budget] = int(update_data['daily_budget'] * 100)
            
            if fb_update_data:
                campaign.api_update(params=fb_update_data)
            
            logger.info("Campaign updated", campaign_id=campaign_id, updates=fb_update_data)
            
            return {'id': campaign_id, 'updated': True}
            
        except Exception as e:
            logger.error("Failed to update campaign", error=str(e), campaign_id=campaign_id)
            raise Exception(f"Meta Ads API error: {str(e)}")
    
    async def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign"""
        try:
            campaign = Campaign(campaign_id)
            campaign.api_update(params={Campaign.Field.status: Campaign.Status.deleted})
            
            logger.info("Campaign deleted", campaign_id=campaign_id)
            return True
            
        except Exception as e:
            logger.error("Failed to delete campaign", error=str(e), campaign_id=campaign_id)
            raise Exception(f"Meta Ads API error: {str(e)}")
    
    async def get_campaigns(self) -> List[Dict]:
        """Get all campaigns for the ad account"""
        try:
            campaigns = self.ad_account.get_campaigns(
                fields=[
                    Campaign.Field.id,
                    Campaign.Field.name,
                    Campaign.Field.objective,
                    Campaign.Field.status,
                    Campaign.Field.daily_budget,
                    Campaign.Field.lifetime_budget,
                    Campaign.Field.created_time,
                    Campaign.Field.updated_time
                ]
            )
            
            campaign_list = []
            for campaign in campaigns:
                campaign_data = {
                    'id': campaign.get('id'),
                    'name': campaign.get('name'),
                    'objective': campaign.get('objective'),
                    'status': campaign.get('status'),
                    'daily_budget': campaign.get('daily_budget', 0) / 100 if campaign.get('daily_budget') else None,
                    'lifetime_budget': campaign.get('lifetime_budget', 0) / 100 if campaign.get('lifetime_budget') else None,
                    'created_time': campaign.get('created_time'),
                    'updated_time': campaign.get('updated_time')
                }
                campaign_list.append(campaign_data)
            
            return campaign_list
            
        except Exception as e:
            logger.error("Failed to get campaigns", error=str(e))
            raise Exception(f"Meta Ads API error: {str(e)}")
    
    async def get_campaign_insights(
        self, 
        campaign_id: str, 
        date_start: Optional[datetime] = None,
        date_end: Optional[datetime] = None
    ) -> List[Dict]:
        """Get insights/metrics for a campaign"""
        try:
            campaign = Campaign(campaign_id)
            
            if not date_start:
                date_start = datetime.now() - timedelta(days=30)
            if not date_end:
                date_end = datetime.now()
            
            params = {
                'time_range': {
                    'since': date_start.strftime('%Y-%m-%d'),
                    'until': date_end.strftime('%Y-%m-%d')
                },
                'level': 'campaign',
                'breakdowns': [],
                'time_increment': 1  # Daily breakdown
            }
            
            fields = [
                AdsInsights.Field.impressions,
                AdsInsights.Field.clicks,
                AdsInsights.Field.spend,
                AdsInsights.Field.cpm,
                AdsInsights.Field.ctr,
                AdsInsights.Field.frequency,
                AdsInsights.Field.reach,
                AdsInsights.Field.date_start,
                AdsInsights.Field.date_stop,
                'conversions',
                'cost_per_conversion'
            ]
            
            insights = campaign.get_insights(fields=fields, params=params)
            
            metrics_list = []
            for insight in insights:
                metrics_data = {
                    'date_start': datetime.strptime(insight.get('date_start'), '%Y-%m-%d'),
                    'date_stop': datetime.strptime(insight.get('date_stop'), '%Y-%m-%d'),
                    'impressions': int(insight.get('impressions', 0)),
                    'clicks': int(insight.get('clicks', 0)),
                    'conversions': int(insight.get('conversions', 0)),
                    'spend': float(insight.get('spend', 0)),
                    'cpm': float(insight.get('cpm', 0)),
                    'ctr': float(insight.get('ctr', 0)),
                    'roas': float(insight.get('roas', 0)) if insight.get('roas') else 0,
                    'frequency': float(insight.get('frequency', 0)),
                    'reach': int(insight.get('reach', 0)),
                    'cost_per_conversion': float(insight.get('cost_per_conversion', 0))
                }
                metrics_list.append(metrics_data)
            
            logger.info("Campaign insights retrieved", campaign_id=campaign_id, metrics_count=len(metrics_list))
            
            return metrics_list
            
        except Exception as e:
            logger.error("Failed to get campaign insights", error=str(e), campaign_id=campaign_id)
            raise Exception(f"Meta Ads API error: {str(e)}")
    
    async def get_account_info(self) -> Dict:
        """Get ad account information"""
        try:
            account_info = self.ad_account.api_get(
                fields=[
                    AdAccount.Field.id,
                    AdAccount.Field.name,
                    AdAccount.Field.account_status,
                    AdAccount.Field.currency,
                    AdAccount.Field.timezone_name,
                    AdAccount.Field.amount_spent,
                    AdAccount.Field.balance
                ]
            )
            
            return {
                'id': account_info.get('id'),
                'name': account_info.get('name'),
                'status': account_info.get('account_status'),
                'currency': account_info.get('currency'),
                'timezone': account_info.get('timezone_name'),
                'amount_spent': float(account_info.get('amount_spent', 0)) / 100,
                'balance': float(account_info.get('balance', 0)) / 100
            }
            
        except Exception as e:
            logger.error("Failed to get account info", error=str(e))
            raise Exception(f"Meta Ads API error: {str(e)}")
