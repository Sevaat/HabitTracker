from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class TelegramLinkView(APIView):
    """
    Привязка Telegram аккаунта
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        telegram_username = request.data.get("telegram_username")

        if not telegram_username:
            return Response({"error": "Не указан Telegram username"}, status=status.HTTP_400_BAD_REQUEST)

        # Очищаем username (убираем @ если есть)
        telegram_username = telegram_username.replace("@", "")

        # Сохраняем username пользователю
        user = request.user
        user.telegram_username = telegram_username
        user.save()

        return Response(
            {"status": "success", "message": "Telegram username сохранен", "telegram_username": telegram_username}
        )


class TelegramStatusView(APIView):
    """
    Статус привязки Telegram
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response(
            {
                "is_linked": bool(user.telegram_chat_id),
                "telegram_username": user.telegram_username,
                "telegram_chat_id": user.telegram_chat_id,
            }
        )


class TelegramUnlinkView(APIView):
    """
    Отвязка Telegram
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        user.telegram_chat_id = None
        user.telegram_username = None
        user.save()

        return Response({"status": "success", "message": "Telegram отвязан"})
