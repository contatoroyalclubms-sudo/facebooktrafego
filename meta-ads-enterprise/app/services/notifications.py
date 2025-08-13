import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
import structlog
from datetime import datetime
import json

from app.core.config import settings
from app.models.campaign import Alert
from app.core.database import get_sync_db

logger = structlog.get_logger()

class NotificationService:
    def __init__(self):
        self.slack_webhook_url = settings.SLACK_WEBHOOK_URL
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'username': '',  # Configure via environment
            'password': ''   # Configure via environment
        }
    
    async def send_alert(self, alert_data: Dict, channels: List[str] = None) -> Dict:
        """Send alert through multiple channels"""
        if channels is None:
            channels = ['database', 'slack']  # Default channels
        
        results = {}
        
        if 'database' in channels:
            results['database'] = await self._save_to_database(alert_data)
        
        if 'slack' in channels and self.slack_webhook_url:
            results['slack'] = await self._send_slack_notification(alert_data)
        
        if 'email' in channels:
            results['email'] = await self._send_email_notification(alert_data)
        
        if 'webhook' in channels:
            results['webhook'] = await self._send_webhook_notification(alert_data)
        
        logger.info("Alert sent", alert_type=alert_data.get('alert_type'), channels=channels, results=results)
        
        return {
            "alert_id": alert_data.get('id'),
            "channels": channels,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    async def send_campaign_alert(
        self, 
        campaign_id: str, 
        alert_type: str, 
        severity: str,
        title: str, 
        message: str, 
        user_id: str,
        data: Dict = None
    ) -> Dict:
        """Send campaign-specific alert"""
        alert_data = {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "alert_type": alert_type,
            "severity": severity,
            "title": title,
            "message": message,
            "data": data or {},
            "created_at": datetime.now()
        }
        
        channels = ['database']
        if severity in ['high', 'critical']:
            channels.extend(['slack', 'email'])
        elif severity == 'medium':
            channels.append('slack')
        
        return await self.send_alert(alert_data, channels)
    
    async def send_performance_alert(
        self, 
        campaign_id: str, 
        metric: str, 
        current_value: float,
        threshold: float, 
        user_id: str
    ) -> Dict:
        """Send performance-based alert"""
        severity = self._determine_severity(metric, current_value, threshold)
        
        title = f"Performance Alert: {metric.upper()}"
        message = f"Campaign {campaign_id} {metric} is {current_value:.2f} (threshold: {threshold:.2f})"
        
        return await self.send_campaign_alert(
            campaign_id=campaign_id,
            alert_type="performance",
            severity=severity,
            title=title,
            message=message,
            user_id=user_id,
            data={
                "metric": metric,
                "current_value": current_value,
                "threshold": threshold,
                "deviation": abs(current_value - threshold)
            }
        )
    
    async def send_budget_alert(
        self, 
        campaign_id: str, 
        spent_amount: float,
        budget_limit: float, 
        user_id: str
    ) -> Dict:
        """Send budget-related alert"""
        spend_percentage = (spent_amount / budget_limit) * 100
        
        if spend_percentage >= 90:
            severity = "critical"
            title = "Budget Critical Alert"
            message = f"Campaign {campaign_id} has spent {spend_percentage:.1f}% of budget (${spent_amount:.2f}/${budget_limit:.2f})"
        elif spend_percentage >= 75:
            severity = "high"
            title = "Budget Warning Alert"
            message = f"Campaign {campaign_id} has spent {spend_percentage:.1f}% of budget (${spent_amount:.2f}/${budget_limit:.2f})"
        else:
            severity = "medium"
            title = "Budget Notification"
            message = f"Campaign {campaign_id} budget update: {spend_percentage:.1f}% spent"
        
        return await self.send_campaign_alert(
            campaign_id=campaign_id,
            alert_type="budget",
            severity=severity,
            title=title,
            message=message,
            user_id=user_id,
            data={
                "spent_amount": spent_amount,
                "budget_limit": budget_limit,
                "spend_percentage": spend_percentage
            }
        )
    
    async def send_optimization_notification(
        self, 
        campaign_id: str, 
        optimization_type: str,
        old_value: float, 
        new_value: float, 
        user_id: str
    ) -> Dict:
        """Send optimization notification"""
        title = f"Campaign Optimized: {optimization_type}"
        message = f"Campaign {campaign_id} {optimization_type} changed from {old_value} to {new_value}"
        
        return await self.send_campaign_alert(
            campaign_id=campaign_id,
            alert_type="optimization",
            severity="info",
            title=title,
            message=message,
            user_id=user_id,
            data={
                "optimization_type": optimization_type,
                "old_value": old_value,
                "new_value": new_value,
                "improvement": ((new_value - old_value) / old_value * 100) if old_value > 0 else 0
            }
        )
    
    async def send_daily_report(self, user_id: str, report_data: Dict) -> Dict:
        """Send daily performance report"""
        title = f"Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
        
        message = self._format_daily_report(report_data)
        
        alert_data = {
            "user_id": user_id,
            "alert_type": "daily_report",
            "severity": "info",
            "title": title,
            "message": message,
            "data": report_data,
            "created_at": datetime.now()
        }
        
        return await self.send_alert(alert_data, ['database', 'email'])
    
    async def _save_to_database(self, alert_data: Dict) -> Dict:
        """Save alert to database"""
        try:
            db = next(get_sync_db())
            
            alert = Alert(
                user_id=alert_data['user_id'],
                campaign_id=alert_data.get('campaign_id'),
                alert_type=alert_data['alert_type'],
                severity=alert_data['severity'],
                title=alert_data['title'],
                message=alert_data['message'],
                data=alert_data.get('data', {}),
                is_read=False
            )
            
            db.add(alert)
            db.commit()
            db.refresh(alert)
            
            return {"status": "success", "alert_id": str(alert.id)}
            
        except Exception as e:
            logger.error("Failed to save alert to database", error=str(e))
            return {"status": "error", "error": str(e)}
        finally:
            db.close()
    
    async def _send_slack_notification(self, alert_data: Dict) -> Dict:
        """Send notification to Slack"""
        try:
            if not self.slack_webhook_url:
                return {"status": "skipped", "reason": "No Slack webhook configured"}
            
            color = self._get_slack_color(alert_data['severity'])
            
            slack_payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": alert_data['title'],
                        "text": alert_data['message'],
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert_data['severity'].upper(),
                                "short": True
                            },
                            {
                                "title": "Type",
                                "value": alert_data['alert_type'],
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": alert_data['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                                "short": True
                            }
                        ],
                        "footer": "Meta Ads Enterprise",
                        "ts": int(alert_data['created_at'].timestamp())
                    }
                ]
            }
            
            if alert_data.get('campaign_id'):
                slack_payload["attachments"][0]["fields"].append({
                    "title": "Campaign",
                    "value": alert_data['campaign_id'],
                    "short": True
                })
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.slack_webhook_url,
                    json=slack_payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        return {"status": "success"}
                    else:
                        return {"status": "error", "error": f"HTTP {response.status}"}
                        
        except Exception as e:
            logger.error("Failed to send Slack notification", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _send_email_notification(self, alert_data: Dict) -> Dict:
        """Send email notification"""
        try:
            return {"status": "skipped", "reason": "Email not configured"}
            
        except Exception as e:
            logger.error("Failed to send email notification", error=str(e))
            return {"status": "error", "error": str(e)}
    
    async def _send_webhook_notification(self, alert_data: Dict) -> Dict:
        """Send webhook notification"""
        try:
            return {"status": "skipped", "reason": "Webhook not configured"}
            
        except Exception as e:
            logger.error("Failed to send webhook notification", error=str(e))
            return {"status": "error", "error": str(e)}
    
    def _determine_severity(self, metric: str, current_value: float, threshold: float) -> str:
        """Determine alert severity based on metric deviation"""
        deviation_percent = abs(current_value - threshold) / threshold * 100
        
        if deviation_percent >= 50:
            return "critical"
        elif deviation_percent >= 25:
            return "high"
        elif deviation_percent >= 10:
            return "medium"
        else:
            return "low"
    
    def _get_slack_color(self, severity: str) -> str:
        """Get Slack color based on severity"""
        colors = {
            "critical": "#FF0000",  # Red
            "high": "#FF8C00",      # Orange
            "medium": "#FFD700",    # Yellow
            "low": "#32CD32",       # Green
            "info": "#1E90FF"       # Blue
        }
        return colors.get(severity, "#808080")  # Gray default
    
    def _format_daily_report(self, report_data: Dict) -> str:
        """Format daily report message"""
        message = f"""
📊 **Daily Performance Report**

**Campaign Summary:**
• Total Campaigns: {report_data.get('total_campaigns', 0)}
• Active Campaigns: {report_data.get('active_campaigns', 0)}

**Today's Performance:**
• Total Spend: ${report_data.get('total_spend', 0):.2f}
• Total Impressions: {report_data.get('total_impressions', 0):,}
• Total Clicks: {report_data.get('total_clicks', 0):,}
• Total Conversions: {report_data.get('total_conversions', 0)}

**Key Metrics:**
• Average CTR: {report_data.get('avg_ctr', 0):.2f}%
• Average CPM: ${report_data.get('avg_cpm', 0):.2f}
• Average ROAS: {report_data.get('avg_roas', 0):.2f}

**Alerts:**
• New Alerts: {report_data.get('new_alerts', 0)}
• Unresolved Issues: {report_data.get('unresolved_alerts', 0)}
        """.strip()
        
        return message

notification_service = NotificationService()
