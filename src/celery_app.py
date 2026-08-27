import os
from celery import Celery
from celery.schedules import crontab

# Assuming Redis runs on localhost default port via Docker Compose
REDIS_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "learnleague_tasks",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat schedule for Gamification Cron Jobs
celery_app.conf.beat_schedule = {
    # 1. Weekly Winner: Runs every Sunday at Midnight (UTC)
    "calculate-weekly-winner-every-sunday": {
        "task": "src.tasks.calculate_weekly_winner",
        "schedule": crontab(hour=0, minute=0, day_of_week="sunday"),
    },
    # 2. Streak Reset Monitor: Runs every day at Midnight (UTC)
    "monitor-streaks-daily": {
        "task": "src.tasks.monitor_streaks",
        "schedule": crontab(hour=0, minute=0),
    },
}
