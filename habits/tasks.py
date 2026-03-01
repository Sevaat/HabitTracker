from celery import shared_task
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Habit
from users.models import User
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_habit_reminders():
    """
    Отправка напоминаний о привычках
    Запускается каждые 5 минут
    """
    logger.info("Запуск проверки напоминаний о привычках")

    current_time = timezone.now()
    current_time_str = current_time.strftime('%H:%M')

    # Ищем привычки, которые нужно выполнить сейчас
    habits_to_remind = Habit.objects.filter(
        time__hour=current_time.hour,
        time__minute=current_time.minute,
        user__telegram_chat_id__isnull=False  # Только пользователи с Telegram
    )

    for habit in habits_to_remind:
        send_single_reminder.delay(habit.id)

    logger.info(f"Найдено {habits_to_remind.count()} привычек для напоминания")

    return f"Отправлено {habits_to_remind.count()} напоминаний"


@shared_task
def send_single_reminder(habit_id):
    """
    Отправка одного напоминания
    """
    try:
        from telegram_bot.bot import HabitBot
        import asyncio

        habit = Habit.objects.get(id=habit_id)

        # Формируем сообщение
        emoji = "🎯" if habit.is_pleasant else "⏰"
        message = (
            f"{emoji} *Напоминание о привычке!*\n\n"
            f"📍 *Где:* {habit.place}\n"
            f"📝 *Что:* {habit.action}\n"
            f"⏱ *Время:* {habit.duration} сек\n"
        )

        if habit.reward:
            message += f"🎁 *Награда:* {habit.reward}\n"

        if habit.linked_habit:
            message += f"✨ *После:* {habit.linked_habit.action}\n"

        message += "\nУдачи! 💪"

        # Отправляем через бота
        bot = HabitBot()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            bot.send_notification(habit.user.telegram_chat_id, message)
        )

        logger.info(f"Напоминание отправлено для привычки {habit.id}")

    except Habit.DoesNotExist:
        logger.error(f"Привычка {habit_id} не найдена")
    except Exception as e:
        logger.error(f"Ошибка отправки напоминания: {e}")


@shared_task
def check_missed_habits():
    """
    Проверка пропущенных привычек
    """
    yesterday = timezone.now() - timedelta(days=1)

    logger.info("Проверка пропущенных привычек")