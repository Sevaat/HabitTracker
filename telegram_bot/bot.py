import logging
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from django.conf import settings
from users.models import User

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class HabitBot:
    """Класс для работы с Telegram ботом"""

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        chat_id = update.effective_chat.id

        # Сохраняем chat_id пользователя
        try:
            django_user = User.objects.get(telegram_username=user.username)
            django_user.telegram_chat_id = chat_id
            django_user.save()

            await update.message.reply_text(
                f"Привет, {user.first_name}! 🎉\n"
                f"Теперь ты будешь получать уведомления о привычках здесь."
            )
        except User.DoesNotExist:
            await update.message.reply_text(
                "Привет! 👋\n"
                "Для получения уведомлений сначала зарегистрируйся в нашем сервисе "
                "и укажи свой Telegram username в профиле."
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        help_text = """
        🤖 *Команды бота:*
        /start - Начать работу с ботом
        /help - Показать это сообщение
        /my_habits - Список моих привычек на сегодня
        /stop - Отключить уведомления

        ✨ *Что я умею:*
        - Напоминать о привычках
        - Отслеживать выполнение
        - Мотивировать тебя!
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def my_habits_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать привычки на сегодня"""
        from habits.models import Habit
        from datetime import date, datetime

        chat_id = update.effective_chat.id

        try:
            user = User.objects.get(telegram_chat_id=chat_id)
            today = date.today()
            current_time = datetime.now().time()

            # Получаем сегодняшние привычки
            habits = Habit.objects.filter(
                user=user,
                time__gte=current_time  # Только будущие
            ).order_by('time')[:5]

            if habits:
                message = "📋 *Твои привычки на сегодня:*\n\n"
                for habit in habits:
                    emoji = "✅" if habit.is_pleasant else "🔔"
                    message += f"{emoji} *{habit.time.strftime('%H:%M')}* - {habit.action}\n"
                    message += f"   📍 {habit.place}\n"
                    if habit.duration:
                        message += f"   ⏱ {habit.duration} сек\n"
                    message += "\n"
            else:
                message = "🎉 На сегодня привычек нет! Отдыхай!"

            await update.message.reply_text(message, parse_mode='Markdown')

        except User.DoesNotExist:
            await update.message.reply_text(
                "❌ Ты не зарегистрирован в системе. Используй /start"
            )

    async def send_notification(self, chat_id: int, message: str):
        """Отправка уведомления пользователю"""
        try:
            bot = Bot(token=self.token)
            await bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Уведомление отправлено пользователю {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")

    def setup(self):
        """Настройка обработчиков команд"""
        self.application = Application.builder().token(self.token).build()

        # Добавляем обработчики команд
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("my_habits", self.my_habits_command))

        logger.info("Telegram бот настроен")

    def run(self):
        """Запуск бота"""
        self.setup()
        self.application.run_polling()