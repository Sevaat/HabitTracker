import os

from celery import Celery
from celery.schedules import crontab

# Устанавливаем настройки Django по умолчанию
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

# Используем строку конфигурации из Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находим задачи во всех приложениях
app.autodiscover_tasks()

# Настройка периодических задач
app.conf.beat_schedule = {
    "send-habit-reminders": {
        "task": "habits.tasks.send_habit_reminders",
        "schedule": crontab(minute="*/5"),  # Каждые 5 минут
    },
}
