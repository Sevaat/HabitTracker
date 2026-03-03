"""
Тесты для приложения пользователей (users)
"""
import pytest
import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    """Тесты модели User"""

    def test_create_user(self):
        """Тест создания обычного пользователя"""
        unique_id = uuid.uuid4().hex[:8]
        user = User.objects.create_user(
            username=f'testuser2_{unique_id}',
            password='testpass123',
            email=f'test2_{unique_id}@example.com'
        )
        assert user.username.startswith('testuser2_')
        assert user.email.startswith('test2_')
        assert user.check_password('testpass123')
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_superuser(self):
        """Тест создания суперпользователя"""
        unique_id = uuid.uuid4().hex[:8]
        admin_user = User.objects.create_superuser(
            username=f'admin_{unique_id}',
            password='adminpass123',
            email=f'admin_{unique_id}@example.com'
        )
        assert admin_user.username.startswith('admin_')
        assert admin_user.is_staff
        assert admin_user.is_superuser

    def test_user_str_method(self, test_user):
        """Тест строкового представления пользователя"""
        assert str(test_user) == test_user.username

    def test_user_with_telegram(self, test_user):
        """Тест пользователя с Telegram данными"""
        unique_id = uuid.uuid4().hex[:4]
        test_user.telegram_username = f'@testuser_{unique_id}'
        test_user.telegram_chat_id = f'123456789{unique_id}'
        test_user.save()

        assert test_user.telegram_username.startswith('@testuser_')
        assert test_user.telegram_chat_id.startswith('123456789')

@pytest.mark.django_db
class TestUserRegistration:
    """Тесты регистрации пользователей"""

    def test_user_registration_success(self, api_client):
        """Тест успешной регистрации"""
        unique_id = uuid.uuid4().hex[:8]
        data = {
            'username': f'newuser_{unique_id}',
            'password': 'testpass123',
            'password2': 'testpass123',
            'email': f'newuser_{unique_id}@example.com',
            'first_name': 'Новый',
            'last_name': 'Пользователь'
        }

        response = api_client.post('/api/users/register/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert response.data['user']['username'] == f'newuser_{unique_id}'
        assert User.objects.filter(username=f'newuser_{unique_id}').exists()

    def test_user_registration_password_mismatch(self, api_client):
        """Тест регистрации с несовпадающими паролями"""
        unique_id = uuid.uuid4().hex[:8]
        data = {
            'username': f'newuser_{unique_id}',
            'password': 'testpass123',
            'password2': 'differentpass',
            'email': f'newuser_{unique_id}@example.com'
        }

        response = api_client.post('/api/users/register/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in str(response.data)

    def test_user_registration_missing_fields(self, api_client):
        """Тест регистрации с отсутствующими полями"""
        unique_id = uuid.uuid4().hex[:8]
        data = {
            'username': f'newuser_{unique_id}',
            'password': 'testpass123'
            # password2 отсутствует
        }

        response = api_client.post('/api/users/register/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_registration_duplicate_username(self, api_client, test_user):
        """Тест регистрации с существующим username"""
        data = {
            'username': test_user.username,  # Уже существует
            'password': 'testpass123',
            'password2': 'testpass123',
            'email': 'new@example.com'
        }

        response = api_client.post('/api/users/register/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestUserAuthentication:
    """Тесты аутентификации"""

    def test_user_login_success(self, api_client, test_user):
        """Тест успешного входа"""
        data = {
            'username': test_user.username,
            'password': 'testpass123'
        }

        response = api_client.post('/api/users/login/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_user_login_wrong_password(self, api_client, test_user):
        """Тест входа с неверным паролем"""
        data = {
            'username': test_user.username,
            'password': 'wrongpass'
        }

        response = api_client.post('/api/users/login/', data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_login_nonexistent_user(self, api_client):
        """Тест входа с несуществующим пользователем"""
        data = {
            'username': 'nosuchuser',
            'password': 'testpass123'
        }

        response = api_client.post('/api/users/login/', data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_refresh(self, api_client, test_user):
        """Тест обновления токена"""
        # Сначала получаем токены
        login_data = {
            'username': test_user.username,
            'password': 'testpass123'
        }
        login_response = api_client.post('/api/users/login/', login_data, format='json')
        refresh_token = login_response.data['refresh']

        # Обновляем токен
        refresh_data = {
            'refresh': refresh_token
        }
        refresh_response = api_client.post('/api/users/refresh/', refresh_data, format='json')
        assert refresh_response.status_code == status.HTTP_200_OK
        assert 'access' in refresh_response.data

@pytest.mark.django_db
class TestUserProfile:
    """Тесты профиля пользователя"""

    def test_get_user_profile(self, auth_client):
        """Тест получения профиля через список привычек"""
        response = auth_client.get('/api/habits/')
        assert response.status_code == status.HTTP_200_OK

    def test_update_user_telegram(self, auth_client, test_user):
        """Тест обновления Telegram данных"""
        unique_id = uuid.uuid4().hex[:4]
        data = {
            'telegram_username': f'@testuser_{unique_id}'
        }
        response = auth_client.post('/api/telegram/link/', data, format='json')
        assert response.status_code == status.HTTP_200_OK

        # Проверяем, что данные сохранились
        test_user.refresh_from_db()
        assert test_user.telegram_username == f'testuser_{unique_id}'