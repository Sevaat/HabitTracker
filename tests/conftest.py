"""
Общие фикстуры и конфигурация для всех тестов
"""
import pytest
import uuid
from django.core.management import call_command
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from habits.models import Habit
from datetime import time

User = get_user_model()

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Настройка базы данных для тестов"""
    with django_db_blocker.unblock():
        # Применяем миграции
        call_command('migrate')

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Автоматически даем доступ к БД всем тестам"""
    pass

@pytest.fixture
def api_client():
    """Фикстура для API клиента"""
    return APIClient()

@pytest.fixture
def test_user(db):
    """Фикстура для тестового пользователя с уникальным username"""
    unique_id = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f'testuser_{unique_id}',
        password='testpass123',
        email=f'test_{unique_id}@example.com',
        first_name='Тест',
        last_name='Пользователь'
    )

@pytest.fixture
def another_user(db):
    """Фикстура для другого тестового пользователя"""
    unique_id = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f'anotheruser_{unique_id}',
        password='testpass123',
        email=f'another_{unique_id}@example.com',
        first_name='Другой',
        last_name='Пользователь'
    )

@pytest.fixture
def auth_client(api_client, test_user):
    """Фикстура для авторизованного клиента"""
    api_client.force_authenticate(user=test_user)
    return api_client

@pytest.fixture
def test_habit(db, test_user):
    """Фикстура для тестовой привычки"""
    return Habit.objects.create(
        user=test_user,
        place='Дом',
        time=time(10, 0),
        action='Сделать зарядку',
        is_pleasant=False,
        periodicity=1,
        duration=60,
        is_public=False
    )

@pytest.fixture
def pleasant_habit(db, test_user):
    """Фикстура для приятной привычки"""
    return Habit.objects.create(
        user=test_user,
        place='Дом',
        time=time(20, 0),
        action='Посмотреть фильм',
        is_pleasant=True,
        periodicity=1,
        duration=120,
        is_public=False
    )