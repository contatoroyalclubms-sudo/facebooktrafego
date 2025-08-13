from typing import Dict, List, Any, Optional
from pydantic import BaseModel, validator, Field
from datetime import datetime
import re

class CampaignCreateValidator(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    objective: str = Field(..., regex=r'^(CONVERSIONS|TRAFFIC|AWARENESS|ENGAGEMENT|APP_INSTALLS|LEAD_GENERATION|MESSAGES|SALES)$')
    daily_budget: Optional[float] = Field(None, gt=0, le=10000)
    total_budget: Optional[float] = Field(None, gt=0, le=100000)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Campaign name cannot be empty')
        return v.strip()
    
    @validator('daily_budget', 'total_budget')
    def validate_budget(cls, v):
        if v is not None and v < 1:
            raise ValueError('Budget must be at least $1')
        return v

class UserCreateValidator(BaseModel):
    email: str = Field(..., regex=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=255)
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        return v

class DateRangeValidator(BaseModel):
    start_date: datetime
    end_date: datetime
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        if 'start_date' in values and v < values['start_date']:
            raise ValueError('End date must be after start date')
        
        if 'start_date' in values and (v - values['start_date']).days > 365:
            raise ValueError('Date range cannot exceed 1 year')
        
        return v

class FacebookTokenValidator(BaseModel):
    access_token: str = Field(..., min_length=50)
    ad_account_id: str = Field(..., regex=r'^\d+$')
    
    @validator('access_token')
    def validate_token_format(cls, v):
        if not v.startswith(('EAA', 'EAAG')):
            raise ValueError('Invalid Facebook access token format')
        return v

class MetricsValidator(BaseModel):
    impressions: int = Field(..., ge=0)
    clicks: int = Field(..., ge=0)
    conversions: int = Field(..., ge=0)
    spend: float = Field(..., ge=0)
    
    @validator('clicks')
    def validate_clicks_vs_impressions(cls, v, values):
        if 'impressions' in values and v > values['impressions']:
            raise ValueError('Clicks cannot exceed impressions')
        return v
    
    @validator('conversions')
    def validate_conversions_vs_clicks(cls, v, values):
        if 'clicks' in values and v > values['clicks']:
            raise ValueError('Conversions cannot exceed clicks')
        return v

class AlertCreateValidator(BaseModel):
    alert_type: str = Field(..., regex=r'^(performance|budget|optimization|system|custom)$')
    severity: str = Field(..., regex=r'^(low|medium|high|critical)$')
    title: str = Field(..., min_length=1, max_length=255)
    message: str = Field(..., min_length=1, max_length=1000)
    
    @validator('title', 'message')
    def validate_text_fields(cls, v):
        return v.strip()

class OptimizationConfigValidator(BaseModel):
    auto_optimize: bool = False
    auto_pause: bool = False
    auto_budget_optimize: bool = False
    ctr_threshold: float = Field(1.0, gt=0, le=10)
    roas_threshold: float = Field(2.0, gt=0, le=20)
    max_frequency: float = Field(3.0, gt=0, le=10)
    
    @validator('ctr_threshold')
    def validate_ctr_threshold(cls, v):
        if v > 10:
            raise ValueError('CTR threshold cannot exceed 10%')
        return v

class BudgetAllocationValidator(BaseModel):
    campaign_budgets: Dict[str, float]
    total_budget: float = Field(..., gt=0)
    
    @validator('campaign_budgets')
    def validate_budget_allocation(cls, v, values):
        if not v:
            raise ValueError('At least one campaign budget must be specified')
        
        total_allocated = sum(v.values())
        if 'total_budget' in values and abs(total_allocated - values['total_budget']) > 0.01:
            raise ValueError('Sum of campaign budgets must equal total budget')
        
        for campaign_id, budget in v.items():
            if budget < 1:
                raise ValueError(f'Budget for campaign {campaign_id} must be at least $1')
        
        return v

class WebhookValidator(BaseModel):
    url: str = Field(..., regex=r'^https?://.+')
    events: List[str] = Field(..., min_items=1)
    secret: Optional[str] = Field(None, min_length=16)
    
    @validator('events')
    def validate_events(cls, v):
        valid_events = [
            'campaign.created', 'campaign.updated', 'campaign.deleted',
            'metrics.updated', 'alert.created', 'optimization.applied'
        ]
        
        for event in v:
            if event not in valid_events:
                raise ValueError(f'Invalid event type: {event}')
        
        return v

class AIInsightValidator(BaseModel):
    insight_type: str = Field(..., regex=r'^(campaign_analysis|optimization|prediction|anomaly)$')
    confidence_score: float = Field(..., ge=0, le=1)
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=10, max_length=5000)
    
    @validator('confidence_score')
    def validate_confidence(cls, v):
        if v < 0.1:
            raise ValueError('Confidence score too low for actionable insight')
        return v

class ReportConfigValidator(BaseModel):
    report_type: str = Field(..., regex=r'^(daily|weekly|monthly|custom)$')
    metrics: List[str] = Field(..., min_items=1)
    campaigns: Optional[List[str]] = None
    email_recipients: List[str] = Field(..., min_items=1)
    
    @validator('metrics')
    def validate_metrics(cls, v):
        valid_metrics = [
            'spend', 'impressions', 'clicks', 'conversions',
            'ctr', 'cpm', 'roas', 'frequency', 'reach'
        ]
        
        for metric in v:
            if metric not in valid_metrics:
                raise ValueError(f'Invalid metric: {metric}')
        
        return v
    
    @validator('email_recipients')
    def validate_emails(cls, v):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in v:
            if not re.match(email_pattern, email):
                raise ValueError(f'Invalid email address: {email}')
        
        return v

def validate_campaign_objective(objective: str) -> bool:
    """Validate Facebook campaign objective"""
    valid_objectives = [
        'CONVERSIONS', 'TRAFFIC', 'AWARENESS', 'ENGAGEMENT',
        'APP_INSTALLS', 'LEAD_GENERATION', 'MESSAGES', 'SALES',
        'VIDEO_VIEWS', 'REACH', 'BRAND_AWARENESS'
    ]
    return objective.upper() in valid_objectives

def validate_facebook_campaign_id(campaign_id: str) -> bool:
    """Validate Facebook campaign ID format"""
    return campaign_id.isdigit() and len(campaign_id) >= 10

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Validate date range"""
    if end_date < start_date:
        return False
    
    if start_date > datetime.now() or end_date > datetime.now():
        return False
    
    if (end_date - start_date).days > 730:
        return False
    
    return True

def validate_budget_amount(amount: float, min_amount: float = 1.0, max_amount: float = 100000.0) -> bool:
    """Validate budget amount"""
    return min_amount <= amount <= max_amount

def validate_performance_threshold(metric: str, value: float) -> bool:
    """Validate performance threshold values"""
    thresholds = {
        'ctr': (0.1, 20.0),      # 0.1% to 20%
        'cpm': (0.1, 100.0),     # $0.1 to $100
        'roas': (0.1, 50.0),     # 0.1 to 50
        'frequency': (0.1, 10.0), # 0.1 to 10
        'conversion_rate': (0.01, 50.0)  # 0.01% to 50%
    }
    
    if metric not in thresholds:
        return False
    
    min_val, max_val = thresholds[metric]
    return min_val <= value <= max_val

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not isinstance(text, str):
        return ""
    
    sanitized = re.sub(r'[<>"\']', '', text)
    
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def validate_webhook_url(url: str) -> bool:
    """Validate webhook URL"""
    url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return re.match(url_pattern, url) is not None

def validate_api_key(api_key: str) -> bool:
    """Validate API key format"""
    if len(api_key) < 32:
        return False
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    return re.match(pattern, api_key) is not None

def validate_json_data(data: Any, max_size: int = 10000) -> bool:
    """Validate JSON data size and structure"""
    try:
        import json
        json_str = json.dumps(data)
        return len(json_str) <= max_size
    except (TypeError, ValueError):
        return False
