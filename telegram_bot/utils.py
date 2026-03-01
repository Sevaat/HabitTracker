from asgiref.sync import sync_to_async

from habits.models import Habit
from users.models import User


@sync_to_async
def get_user_by_username(username):
    """Асинхронное получение пользователя по username"""
    try:
        return User.objects.get(telegram_username=username)
    except User.DoesNotExist:
        return None


@sync_to_async
def get_user_by_chat_id(chat_id):
    """Асинхронное получение пользователя по chat_id"""
    try:
        return User.objects.get(telegram_chat_id=chat_id)
    except User.DoesNotExist:
        return None


@sync_to_async
def get_todays_habits(user):
    """Асинхронное получение привычек на сегодня"""
    from datetime import datetime

    current_time = datetime.now().time()
    return list(Habit.objects.filter(user=user, time__gte=current_time).order_by("time")[:5])


@sync_to_async
def save_user_telegram(user, chat_id):
    """Асинхронное сохранение chat_id пользователя"""
    user.telegram_chat_id = chat_id
    user.save()
    return user
