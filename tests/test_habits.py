import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from habits.models import Habit
from datetime import time
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def api_client():
    """Фикстура для API клиента"""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Фикстура для тестового пользователя"""
    return User.objects.create_user(
        username='testuser',
        password='testpass123'
    )


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


@pytest.mark.django_db
class TestHabitModel:
    """Тесты модели Habit"""

    def test_create_habit(self, test_user):
        """Тест создания привычки"""
        habit = Habit.objects.create(
            user=test_user,
            place='Офис',
            time=time(15, 0),
            action='Выпить воду',
            is_pleasant=True,
            periodicity=1,
            duration=30,
            is_public=True
        )

        assert habit.place == 'Офис'
        assert habit.action == 'Выпить воду'
        assert habit.duration == 30
        assert habit.is_pleasant is True

    def test_habit_str(self, test_habit):
        """Тест строкового представления"""
        expected = f"{test_habit.action} в {test_habit.time}"
        assert str(test_habit) == expected


@pytest.mark.django_db
class TestHabitAPI:
    """Тесты API привычек"""

    def test_get_habits_unauthenticated(self, api_client):
        """Тест доступа без аутентификации"""
        response = api_client.get('/api/habits/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_habit_authenticated(self, api_client, test_user):
        """Тест создания привычки аутентифицированным пользователем"""
        api_client.force_authenticate(user=test_user)

        data = {
            'place': 'Спортзал',
            'time': '08:00:00',
            'action': 'Тренировка',
            'is_pleasant': False,
            'periodicity': 1,
            'duration': 90,
            'is_public': False
        }

        response = api_client.post('/api/habits/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['place'] == 'Спортзал'
        assert response.data['action'] == 'Тренировка'

    def test_habit_list_pagination(self, api_client, test_user):
        """Тест пагинации списка привычек"""
        # Создаем 7 привычек
        for i in range(7):
            Habit.objects.create(
                user=test_user,
                place=f'Место {i}',
                time=time(10, 0),
                action=f'Действие {i}',
                is_pleasant=False,
                periodicity=1,
                duration=60,
                is_public=False
            )

        api_client.force_authenticate(user=test_user)
        response = api_client.get('/api/habits/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 5  # Пагинация по 5
        assert response.data['count'] == 7

    def test_update_habit(self, api_client, test_user, test_habit):
        """Тест обновления привычки"""
        api_client.force_authenticate(user=test_user)

        data = {'place': 'Новое место'}
        response = api_client.patch(f'/api/habits/{test_habit.id}/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['place'] == 'Новое место'

    def test_delete_habit(self, api_client, test_user, test_habit):
        """Тест удаления привычки"""
        api_client.force_authenticate(user=test_user)

        response = api_client.delete(f'/api/habits/{test_habit.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Проверяем, что привычка действительно удалена
        assert not Habit.objects.filter(id=test_habit.id).exists()

    def test_cannot_update_others_habit(self, api_client, test_user, test_habit):
        """Тест невозможности редактировать чужую привычку"""
        # Создаем другого пользователя
        other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )

        api_client.force_authenticate(user=other_user)

        data = {'place': 'Попытка изменить'}
        response = api_client.patch(f'/api/habits/{test_habit.id}/', data, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestHabitValidators:
    """Тесты валидаторов привычек"""

    def test_cannot_have_both_reward_and_linked_habit(self, api_client, test_user):
        """Тест: нельзя указать и награду, и связанную привычку"""
        api_client.force_authenticate(user=test_user)

        # Создаем приятную привычку для связи
        pleasant_habit = Habit.objects.create(
            user=test_user,
            place='Дом',
            time=time(10, 0),
            action='Приятная привычка',
            is_pleasant=True,
            periodicity=1,
            duration=30,
            is_public=False
        )

        data = {
            'place': 'Офис',
            'time': '15:00:00',
            'action': 'Полезная привычка',
            'is_pleasant': False,
            'reward': 'Шоколадка',
            'linked_habit': pleasant_habit.id,
            'periodicity': 1,
            'duration': 60,
            'is_public': False
        }

        response = api_client.post('/api/habits/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duration_must_be_less_than_120(self, api_client, test_user):
        """Тест: длительность не больше 120 секунд"""
        api_client.force_authenticate(user=test_user)

        data = {
            'place': 'Офис',
            'time': '15:00:00',
            'action': 'Долгая привычка',
            'is_pleasant': False,
            'periodicity': 1,
            'duration': 150,  # Больше 120
            'is_public': False
        }

        response = api_client.post('/api/habits/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_linked_habit_must_be_pleasant(self, api_client, test_user):
        """Тест: связанная привычка должна быть приятной"""
        api_client.force_authenticate(user=test_user)

        # Создаем НЕприятную привычку для связи
        not_pleasant_habit = Habit.objects.create(
            user=test_user,
            place='Дом',
            time=time(10, 0),
            action='Неприятная привычка',
            is_pleasant=False,
            periodicity=1,
            duration=30,
            is_public=False
        )

        data = {
            'place': 'Офис',
            'time': '15:00:00',
            'action': 'Полезная привычка',
            'is_pleasant': False,
            'linked_habit': not_pleasant_habit.id,
            'periodicity': 1,
            'duration': 60,
            'is_public': False
        }

        response = api_client.post('/api/habits/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPublicHabits:
    """Тесты публичных привычек"""

    def test_public_habits_list(self, api_client, test_user):
        """Тест получения списка публичных привычек"""
        # Создаем публичные привычки
        Habit.objects.create(
            user=test_user,
            place='Парк',
            time=time(9, 0),
            action='Публичная привычка 1',
            is_pleasant=False,
            periodicity=1,
            duration=60,
            is_public=True
        )

        Habit.objects.create(
            user=test_user,
            place='Спортзал',
            time=time(18, 0),
            action='Публичная привычка 2',
            is_pleasant=False,
            periodicity=1,
            duration=45,
            is_public=True
        )

        # Создаем приватную привычку
        Habit.objects.create(
            user=test_user,
            place='Дом',
            time=time(22, 0),
            action='Приватная привычка',
            is_pleasant=False,
            periodicity=1,
            duration=30,
            is_public=False
        )

        api_client.force_authenticate(user=test_user)
        response = api_client.get('/api/habits/public/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Только публичные