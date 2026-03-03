from rest_framework import serializers


class HabitValidator:
    """Комплексный валидатор для привычек"""

    def __call__(self, data):
        # Получаем данные
        reward = data.get("reward")
        linked_habit = data.get("linked_habit")
        is_pleasant = data.get("is_pleasant", False)
        duration = data.get("duration")
        periodicity = data.get("periodicity")

        # Валидация 1: Время выполнения не больше 120 секунд
        if duration and duration > 120:
            raise serializers.ValidationError("Время выполнения не должно превышать 120 секунд")

        # Валидация 2: Нельзя выбрать и reward и linked_habit
        if reward and linked_habit:
            raise serializers.ValidationError("Нельзя указать одновременно вознаграждение и связанную привычку")

        # Валидация 3: У приятной привычки не может быть награды
        if is_pleasant and reward:
            raise serializers.ValidationError("У приятной привычки не может быть вознаграждения")

        # Валидация 4: У приятной привычки не может быть связанной привычки
        if is_pleasant and linked_habit:
            raise serializers.ValidationError("У приятной привычки не может быть связанной привычки")

        # Валидация 5: Связанная привычка должна быть приятной
        if linked_habit and not linked_habit.is_pleasant:
            raise serializers.ValidationError("Связанная привычка должна быть приятной")

        # Валидация 6: Периодичность не больше 7 дней
        if periodicity and periodicity > 7:
            raise serializers.ValidationError("Нельзя выполнять привычку реже 1 раза в 7 дней")


def validate_habit_time(value):
    """Валидатор времени выполнения"""
    if value > 120:
        raise serializers.ValidationError("Время выполнения не должно превышать 120 секунд")
    return value
