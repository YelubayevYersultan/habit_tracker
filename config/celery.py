import os
from celery import Celery
from celery.schedules import crontab  # 👈 Импортируем crontab для гибкой настройки расписания

# Говорим Celery, где искать настройки проекта Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Создаем экземпляр приложения Celery и даем ему имя
app = Celery('config')

# Читаем настройки из settings.py, все ключи для Celery должны начинаться с префикса CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически ищем файлы tasks.py внутри всех наших приложений (например, в habits/)
app.autodiscover_tasks()

# 📅 НАСТРОЙКА ПЕРИОДИЧЕСКИХ ЗАДАЧ (CELERY BEAT)
app.conf.beat_schedule = {
    # 1. Задача на отправку напоминаний каждую минуту
    'send-reminders-every-minute': {
        'task': 'habits.tasks.send_habit_reminder',
        'schedule': crontab(minute='*'),  # Каждую минуту
    },
    # 2. Задача на сброс статусов выполненных привычек каждую полночь
    'reset-habits-every-midnight': {
        'task': 'habits.tasks.reset_daily_habits',
        'schedule': crontab(minute=0, hour=0),  # Ровно в 00:00 ночи
    },
}
