from rest_framework import serializers
from .models import Habit
from .validators import HabitValidator


class HabitSerializer(serializers.ModelSerializer):
    """Сериализатор для привычек"""

    class Meta:
        model = Habit
        fields = [
            'id', 'place', 'time', 'action', 'is_pleasant',
            'linked_habit', 'periodicity', 'reward', 'duration',
            'is_public', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # Применяем наш кастомный валидатор
        validator = HabitValidator()
        validator(data)

        # Проверяем, что пользователь не может указать чужую привычку
        linked_habit = data.get('linked_habit')
        if linked_habit:
            request = self.context.get('request')
            if linked_habit.user != request.user:
                raise serializers.ValidationError(
                    "Можно использовать только свои привычки"
                )

        return data

    def create(self, validated_data):
        # Автоматически устанавливаем текущего пользователя
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class HabitListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка привычек (упрощенный)"""

    class Meta:
        model = Habit
        fields = [
            'id', 'place', 'action', 'time',
            'is_pleasant', 'is_public'
        ]


class PublicHabitSerializer(serializers.ModelSerializer):
    """Сериализатор для публичных привычек"""
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Habit
        fields = [
            'id', 'user_username', 'place', 'time', 'action',
            'is_pleasant', 'periodicity', 'duration', 'is_public'
        ]