from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
import hashlib
import secrets
import string

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    if currency == "USD":
        return f"${amount:,.2f}"
    elif currency == "BRL":
        return f"R$ {amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"

def format_number(number: int) -> str:
    """Format large numbers with K, M, B suffixes"""
    if number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    elif number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    elif number >= 1_000:
        return f"{number / 1_000:.1f}K"
    else:
        return str(number)

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage with % symbol"""
    return f"{value:.{decimals}f}%"

def calculate_ctr(clicks: int, impressions: int) -> float:
    """Calculate Click-Through Rate"""
    if impressions == 0:
        return 0.0
    return (clicks / impressions) * 100

def calculate_cpm(spend: float, impressions: int) -> float:
    """Calculate Cost Per Mille (CPM)"""
    if impressions == 0:
        return 0.0
    return (spend / impressions) * 1000

def calculate_roas(revenue: float, spend: float) -> float:
    """Calculate Return on Ad Spend"""
    if spend == 0:
        return 0.0
    return revenue / spend

def calculate_conversion_rate(conversions: int, clicks: int) -> float:
    """Calculate conversion rate"""
    if clicks == 0:
        return 0.0
    return (conversions / clicks) * 100

def calculate_cost_per_conversion(spend: float, conversions: int) -> float:
    """Calculate cost per conversion"""
    if conversions == 0:
        return 0.0
    return spend / conversions

def get_date_range(period: str) -> tuple[datetime, datetime]:
    """Get date range for common periods"""
    end_date = datetime.now()
    
    if period == "today":
        start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "yesterday":
        start_date = (end_date - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59)
    elif period == "last_7_days":
        start_date = end_date - timedelta(days=7)
    elif period == "last_30_days":
        start_date = end_date - timedelta(days=30)
    elif period == "this_month":
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "last_month":
        first_day_this_month = end_date.replace(day=1)
        end_date = first_day_this_month - timedelta(days=1)
        start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59)
    else:
        start_date = end_date - timedelta(days=7)
    
    return start_date, end_date

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_facebook_campaign_id(campaign_id: str) -> bool:
    """Validate Facebook campaign ID format"""
    return campaign_id.isdigit() and len(campaign_id) >= 10

def generate_api_key() -> str:
    """Generate a secure API key"""
    return secrets.token_urlsafe(32)

def generate_password(length: int = 12) -> str:
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def hash_string(text: str) -> str:
    """Generate SHA-256 hash of a string"""
    return hashlib.sha256(text.encode()).hexdigest()

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero"""
    if denominator == 0:
        return default
    return numerator / denominator

def parse_facebook_date(date_string: str) -> datetime:
    """Parse Facebook API date string to datetime"""
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")
        except ValueError:
            return datetime.now()

def get_performance_status(metric_value: float, thresholds: Dict[str, float]) -> str:
    """Get performance status based on thresholds"""
    if metric_value >= thresholds.get("excellent", 100):
        return "excellent"
    elif metric_value >= thresholds.get("good", 75):
        return "good"
    elif metric_value >= thresholds.get("average", 50):
        return "average"
    elif metric_value >= thresholds.get("poor", 25):
        return "poor"
    else:
        return "critical"

def calculate_trend(current_value: float, previous_value: float) -> Dict[str, Any]:
    """Calculate trend between two values"""
    if previous_value == 0:
        return {
            "direction": "neutral",
            "percentage": 0.0,
            "absolute": current_value
        }
    
    percentage_change = ((current_value - previous_value) / previous_value) * 100
    absolute_change = current_value - previous_value
    
    if percentage_change > 5:
        direction = "up"
    elif percentage_change < -5:
        direction = "down"
    else:
        direction = "neutral"
    
    return {
        "direction": direction,
        "percentage": round(percentage_change, 2),
        "absolute": round(absolute_change, 2)
    }

def group_by_date(data: List[Dict], date_field: str = "date") -> Dict[str, List[Dict]]:
    """Group data by date"""
    grouped = {}
    for item in data:
        date_key = item[date_field].strftime("%Y-%m-%d") if isinstance(item[date_field], datetime) else str(item[date_field])
        if date_key not in grouped:
            grouped[date_key] = []
        grouped[date_key].append(item)
    return grouped

def aggregate_metrics(metrics: List[Dict]) -> Dict[str, float]:
    """Aggregate a list of metrics"""
    if not metrics:
        return {}
    
    aggregated = {}
    
    sum_fields = ["spend", "impressions", "clicks", "conversions", "reach"]
    for field in sum_fields:
        aggregated[field] = sum(metric.get(field, 0) for metric in metrics)
    
    avg_fields = ["ctr", "cpm", "roas", "frequency"]
    for field in avg_fields:
        values = [metric.get(field, 0) for metric in metrics if metric.get(field, 0) > 0]
        aggregated[field] = sum(values) / len(values) if values else 0
    
    return aggregated

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    filename = filename.strip(' .')
    
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result

def get_business_days_between(start_date: datetime, end_date: datetime) -> int:
    """Get number of business days between two dates"""
    business_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days

def is_business_hour(dt: datetime, start_hour: int = 9, end_hour: int = 17) -> bool:
    """Check if datetime is within business hours"""
    return (
        dt.weekday() < 5 and  # Monday to Friday
        start_hour <= dt.hour < end_hour
    )
