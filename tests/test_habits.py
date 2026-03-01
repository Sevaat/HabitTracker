"""
Тесты для приложения привычек
"""
import pytest
import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from habits.models import Habit
from datetime import time

User = get_user_model()

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
        assert habit.user == test_user

    def test_habit_str(self, test_habit):
        """Тест строкового представления"""
        expected = f"{test_habit.action} в {test_habit.time}"
        assert str(test_habit) == expected

    def test_habit_periodicity_validation(self, test_user):
        """Тест валидации периодичности"""
        from django.core.exceptions import ValidationError

        habit = Habit(
            user=test_user,
            place='Тест',
            time=time(12, 0),
            action='Тестовая привычка',
            is_pleasant=False,
            periodicity=8,  # Больше 7 дней
            duration=60,
            is_public=False
        )

        with pytest.raises(ValidationError):
            habit.full_clean()  # Вызываем валидацию

@pytest.mark.django_db
class TestHabitAPI:
    """Тесты API привычек"""

    def test_get_habits_unauthenticated(self, api_client):
        """Тест доступа без аутентификации"""
        response = api_client.get('/api/habits/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_habit_authenticated(self, auth_client):
        """Тест создания привычки аутентифицированным пользователем"""
        data = {
            'place': 'Спортзал',
            'time': '08:00:00',
            'action': 'Тренировка',
            'is_pleasant': False,
            'periodicity': 1,
            'duration': 90,
            'is_public': False
        }

        response = auth_client.post('/api/habits/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['place'] == 'Спортзал'
        assert response.data['action'] == 'Тренировка'

    def test_habit_list_pagination(self, auth_client, test_user):
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

        response = auth_client.get('/api/habits/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 5  # Пагинация по 5
        assert response.data['count'] == 7

    def test_update_habit(self, auth_client, test_habit):
        """Тест обновления привычки"""
        data = {'place': 'Новое место'}
        response = auth_client.patch(f'/api/habits/{test_habit.id}/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['place'] == 'Новое место'

    def test_delete_habit(self, auth_client, test_habit):
        """Тест удаления привычки"""
        response = auth_client.delete(f'/api/habits/{test_habit.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Проверяем, что привычка действительно удалена
        assert not Habit.objects.filter(id=test_habit.id).exists()

    def test_cannot_update_others_habit(self, api_client, another_user, test_habit):
        """Тест невозможности редактировать чужую привычку"""
        api_client.force_authenticate(user=another_user)

        data = {'place': 'Попытка изменить'}
        response = api_client.patch(f'/api/habits/{test_habit.id}/', data, format='json')

        assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.django_db
class TestHabitValidators:
    """Тесты валидаторов привычек"""

    def test_cannot_have_both_reward_and_linked_habit(self, auth_client, test_user, pleasant_habit):
        """Тест: нельзя указать и награду, и связанную привычку"""
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

        response = auth_client.post('/api/habits/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_duration_must_be_less_than_120(self, auth_client):
        """Тест: длительность не больше 120 секунд"""
        data = {
            'place': 'Офис',
            'time': '15:00:00',
            'action': 'Долгая привычка',
            'is_pleasant': False,
            'periodicity': 1,
            'duration': 150,  # Больше 120
            'is_public': False
        }

        response = auth_client.post('/api/habits/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_linked_habit_must_be_pleasant(self, auth_client, test_habit):
        """Тест: связанная привычка должна быть приятной"""
        data = {
            'place': 'Офис',
            'time': '15:00:00',
            'action': 'Полезная привычка',
            'is_pleasant': False,
            'linked_habit': test_habit.id,  # test_habit - неприятная привычка
            'periodicity': 1,
            'duration': 60,
            'is_public': False
        }

        response = auth_client.post('/api/habits/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestPublicHabits:
    """Тесты публичных привычек"""

    def test_public_habits_list(self, auth_client, test_user):
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

        response = auth_client.get('/api/habits/public/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 2  # Только публичные
        assert response.data['count'] == 2