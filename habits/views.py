from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Habit
from .permissions import IsOwner
from .serializers import HabitListSerializer, HabitSerializer, PublicHabitSerializer


class HabitListCreateView(generics.ListCreateAPIView):
    """
    GET: Список привычек текущего пользователя
    POST: Создание новой привычки
    """

    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Возвращаем только привычки текущего пользователя
        return Habit.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return HabitListSerializer
        return HabitSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HabitRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Детальная информация о привычке
    PUT/PATCH: Редактирование привычки
    DELETE: Удаление привычки
    """

    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)


class PublicHabitListView(generics.ListAPIView):
    """
    GET: Список публичных привычек (всех пользователей)
    """

    serializer_class = PublicHabitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Habit.objects.filter(is_public=True)


class HabitTogglePublicView(generics.UpdateAPIView):
    """
    Переключение статуса публичности привычки
    """

    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def patch(self, request, *args, **kwargs):
        habit = self.get_object()
        habit.is_public = not habit.is_public
        habit.save()

        return Response({"status": "success", "is_public": habit.is_public}, status=status.HTTP_200_OK)

    def get_queryset(self):
        return Habit.objects.filter(user=self.request.user)
