import os
import requests
from celery import shared_task
from django.utils import timezone
from .models import Habit


@shared_task(name="habits.tasks.send_habit_reminder")
def send_habit_reminder():
    # 1. Получаем текущее локальное время Алматы (часы и минуты)
    local_now = timezone.localtime(timezone.now())
    current_time = local_now.time().replace(second=0, microsecond=0)

    print(f"Ищем привычки на локальное время: {current_time}")

    # 2. Ищем в базе все привычки, у которых reminder_time совпадает с текущим временем
    # Используем select_related, чтобы Django за один запрос вытащил юзера и его профиль (оптимизация)
    habits_to_remind = Habit.objects.filter(reminder_time=current_time).select_related('user__profile')

    if not habits_to_remind.exists():
        return f"Нет привычек для отправки на время {current_time}"

    # 3. Достаем токен бота из окружения для прямой отправки через API Телеграма
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    sent_count = 0
    for habit in habits_to_remind:
        # Достаем telegram_id из нашей новой связанной модели UserProfile
        try:
            tg_id = habit.user.profile.telegram_id
        except Exception as e:
            print(f"Не удалось получить профиль для пользователя {habit.user.username}: {e}")
            tg_id = None

        # Если у юзера нет привязанного Telegram ID (например, создан через чистую админку), пропускаем
        if not tg_id:
            print(f"Пропускаем привычку '{habit.title}': у юзера {habit.user.username} нет telegram_id")
            continue

        # Формируем красивый текст напоминания
        text = (
            f"⏰ *Время пришло!*\n\n"
            f"Пора выполнить привычку: *{habit.title}*\n"
            f"Твоя награда после выполнения: *{habit.reward if habit.reward else 'Отсутствует'}*"
        )

        payload = {
            "chat_id": tg_id,
            "text": text,
            "parse_mode": "Markdown"
        }

        # Отправляем прямой POST-запрос в Телеграм
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                sent_count += 1
            else:
                print(f"Телеграм вернул ошибку {response.status_code} для id {tg_id}: {response.text}")
        except Exception as e:
            print(f"Ошибка отправки уведомления для {tg_id}: {e}")

    return f"Успешно отправлено напоминаний: {sent_count} на время {current_time}"


# 👇 НАША НОВАЯ ПЕРИОДИЧЕСКАЯ ЗАДАЧА ДЛЯ СБРОСА СТАТУСОВ
@shared_task(name="habits.tasks.reset_daily_habits")
def reset_daily_habits():
    """
    Периодическая задача, которая каждую полночь сбрасывает
    статус выполнения всех привычек для нового дня.
    """
    # Массово обновляем только те привычки, которые были выполнены (оптимизация БД)
    updated_count = Habit.objects.filter(is_completed=True).update(is_completed=False)

    return f"Статус привычек успешно сброшен. Обновлено записей: {updated_count}"
