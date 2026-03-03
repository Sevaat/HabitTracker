"""
Тесты для Telegram бота
"""
import pytest
import uuid
from unittest.mock import Mock, patch, AsyncMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from telegram_bot.bot import HabitBot
from datetime import time

User = get_user_model()

@pytest.mark.django_db
class TestTelegramBot:
    """Тесты Telegram бота"""

    def test_bot_initialization(self):
        """Тест инициализации бота"""
        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
            bot = HabitBot()
            assert bot.token == 'test_token'
            assert bot.application is None

    @patch('telegram_bot.bot.Application.builder')
    def test_bot_setup(self, mock_builder):
        """Тест настройки бота"""
        # Мокаем Application
        mock_app = Mock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app

        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
            bot = HabitBot()
            bot.setup()

        # Проверяем, что обработчики добавились
        assert mock_app.add_handler.call_count >= 3  # start, help, my_habits

    @pytest.mark.asyncio
    @patch('telegram_bot.bot.get_user_by_username')
    @patch('telegram_bot.bot.save_user_telegram')
    async def test_start_command_user_exists(self, mock_save, mock_get_user, test_user):
        """Тест команды /start когда пользователь существует"""
        # Настраиваем моки
        mock_get_user.return_value = test_user
        mock_save.return_value = test_user

        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
            bot = HabitBot()

            # Создаем моки для update и context
            mock_update = Mock()
            mock_update.effective_user.username = test_user.telegram_username
            mock_update.effective_user.first_name = 'Тест'
            mock_update.effective_chat.id = '123456789'
            mock_update.message.reply_text = AsyncMock()

            mock_context = Mock()

            # Вызываем команду
            await bot.start_command(mock_update, mock_context)

            # Проверяем, что ответ был отправлен
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    @patch('telegram_bot.bot.get_user_by_username')
    async def test_start_command_user_not_exists(self, mock_get_user):
        """Тест команды /start когда пользователь не существует"""
        # Настраиваем мок
        mock_get_user.return_value = None

        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
            bot = HabitBot()

            mock_update = Mock()
            mock_update.effective_user.username = 'unknown_user'
            mock_update.effective_user.first_name = 'Неизвестный'
            mock_update.effective_chat.id = '999999'
            mock_update.message.reply_text = AsyncMock()
            mock_context = Mock()

            await bot.start_command(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Тест команды /help"""
        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
            bot = HabitBot()

            mock_update = Mock()
            mock_update.message.reply_text = AsyncMock()
            mock_context = Mock()

            await bot.help_command(mock_update, mock_context)

            # Проверяем, что ответ был отправлен
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    @patch('telegram_bot.bot.get_user_by_chat_id')
    @patch('telegram_bot.bot.get_todays_habits')
    async def test_my_habits_command_with_habits(self, mock_get_habits, mock_get_user, test_user, test_habit):
        """Тест команды /my_habits с привычками"""
        # Настраиваем моки
        mock_get_user.return_value = test_user
        mock_get_habits.return_value = [test_habit]

        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
            bot = HabitBot()

            mock_update = Mock()
            mock_update.effective_chat.id = test_user.telegram_chat_id
            mock_update.message.reply_text = AsyncMock()
            mock_context = Mock()

            await bot.my_habits_command(mock_update, mock_context)

            # Проверяем, что ответ был отправлен
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    @patch('telegram_bot.bot.get_user_by_chat_id')
    @patch('telegram_bot.bot.get_todays_habits')
    async def test_my_habits_command_no_habits(self, mock_get_habits, mock_get_user, test_user):
        """Тест команды /my_habits без привычек"""
        # Настраиваем моки
        mock_get_user.return_value = test_user
        mock_get_habits.return_value = []

        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
            bot = HabitBot()

            mock_update = Mock()
            mock_update.effective_chat.id = test_user.telegram_chat_id
            mock_update.message.reply_text = AsyncMock()
            mock_context = Mock()

            await bot.my_habits_command(mock_update, mock_context)

            # Проверяем, что ответ был отправлен
            mock_update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    @patch('telegram_bot.bot.get_user_by_chat_id')
    async def test_my_habits_command_user_not_found(self, mock_get_user):
        """Тест команды /my_habits когда пользователь не найден"""
        # Настраиваем мок
        mock_get_user.return_value = None

        with patch('telegram_bot.bot.settings') as mock_settings:
            mock_settings.TELEGRAM_BOT_TOKEN = 'test_token'
            bot = HabitBot()

            mock_update = Mock()
            mock_update.effective_chat.id = '999999'
            mock_update.message.reply_text = AsyncMock()
            mock_context = Mock()

            await bot.my_habits_command(mock_update, mock_context)

            # Проверяем, что ответ был отправлен
            mock_update.message.reply_text.assert_called_once()

@pytest.mark.django_db
class TestTelegramAPI:
    """Тесты API endpoints для Telegram"""

    def test_telegram_link_success(self, auth_client, test_user):
        """Тест успешной привязки Telegram"""
        unique_id = uuid.uuid4().hex[:4]
        data = {
            'telegram_username': f'@new_telegram_user_{unique_id}'
        }
        response = auth_client.post('/api/telegram/link/', data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        assert response.data['telegram_username'] == f'new_telegram_user_{unique_id}'

        # Проверяем, что данные сохранились в БД
        test_user.refresh_from_db()
        assert test_user.telegram_username == f'new_telegram_user_{unique_id}'

    def test_telegram_link_without_username(self, auth_client):
        """Тест привязки без указания username"""
        data = {}
        response = auth_client.post('/api/telegram/link/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_telegram_link_unauthenticated(self, api_client):
        """Тест привязки без авторизации"""
        data = {
            'telegram_username': '@testuser'
        }
        response = api_client.post('/api/telegram/link/', data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_telegram_status_with_chat_id(self, auth_client, test_user):
        """Тест статуса с привязанным Telegram"""
        unique_id = uuid.uuid4().hex[:4]
        test_user.telegram_chat_id = f'123456789{unique_id}'
        test_user.save()

        response = auth_client.get('/api/telegram/status/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_linked'] is True
        assert response.data['telegram_chat_id'] == f'123456789{unique_id}'

    def test_telegram_status_without_chat_id(self, auth_client, test_user):
        """Тест статуса без привязанного Telegram"""
        test_user.telegram_chat_id = None
        test_user.save()

        response = auth_client.get('/api/telegram/status/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_linked'] is False

    def test_telegram_unlink_success(self, auth_client, test_user):
        """Тест успешной отвязки Telegram"""
        # Сначала привязываем
        unique_id = uuid.uuid4().hex[:4]
        test_user.telegram_chat_id = f'123456789{unique_id}'
        test_user.telegram_username = f'testuser_{unique_id}'
        test_user.save()

        # Отвязываем
        response = auth_client.post('/api/telegram/unlink/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'

        # Проверяем, что данные удалились
        test_user.refresh_from_db()
        assert test_user.telegram_chat_id is None
        assert test_user.telegram_username is None

    def test_telegram_unlink_unauthenticated(self, api_client):
        """Тест отвязки без авторизации"""
        response = api_client.post('/api/telegram/unlink/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED