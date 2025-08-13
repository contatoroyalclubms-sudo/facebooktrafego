from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "meta_ads_automation",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

celery_app.conf.beat_schedule = {
    'sync-campaign-metrics': {
        'task': 'app.workers.tasks.sync_all_campaign_metrics',
        'schedule': 1800.0,  # 30 minutes
    },
    
    'optimize-campaigns': {
        'task': 'app.workers.tasks.optimize_all_campaigns',
        'schedule': 3600.0,  # 1 hour
    },
    
    'generate-ai-insights': {
        'task': 'app.workers.tasks.generate_daily_ai_insights',
        'schedule': crontab(hour=8, minute=0),
    },
    
    'send-daily-reports': {
        'task': 'app.workers.tasks.send_daily_reports',
        'schedule': crontab(hour=9, minute=0),
    },
    
    'monitor-alerts': {
        'task': 'app.workers.tasks.monitor_performance_alerts',
        'schedule': 300.0,  # 5 minutes
    },
    
    'auto-pause-campaigns': {
        'task': 'app.workers.tasks.auto_pause_underperforming_campaigns',
        'schedule': 7200.0,  # 2 hours
    },
    
    'cleanup-old-data': {
        'task': 'app.workers.tasks.cleanup_old_data',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),
    },
    
    'train-ml-models': {
        'task': 'app.workers.tasks.train_ml_models',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),
    },
}

celery_app.conf.timezone = 'UTC'

if __name__ == '__main__':
    celery_app.start()
