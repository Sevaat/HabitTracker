from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Habit(models.Model):
    """Модель привычки"""

    # Частота выполнения (в днях)
    PERIOD_CHOICES = [
        (1, "Ежедневно"),
        (2, "Раз в 2 дня"),
        (3, "Раз в 3 дня"),
        (4, "Раз в 4 дня"),
        (5, "Раз в 5 дней"),
        (6, "Раз в 6 дней"),
        (7, "Раз в неделю"),
    ]

    # Основные поля
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="habits", verbose_name="Пользователь"
    )

    place = models.CharField(max_length=255, verbose_name="Место выполнения")

    time = models.TimeField(verbose_name="Время выполнения")

    action = models.CharField(max_length=255, verbose_name="Действие")

    is_pleasant = models.BooleanField(default=False, verbose_name="Признак приятной привычки")

    # Связанная привычка (для полезных привычек)
    linked_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="linked_to",
        verbose_name="Связанная привычка",
        help_text="Приятная привычка, которая является вознаграждением",
    )

    periodicity = models.PositiveSmallIntegerField(
        choices=PERIOD_CHOICES,
        default=1,
        verbose_name="Периодичность (в днях)",
        validators=[MinValueValidator(1), MaxValueValidator(7)],
    )

    reward = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Вознаграждение",
        help_text="Чем вознаградить себя после выполнения",
    )

    duration = models.PositiveSmallIntegerField(
        verbose_name="Время на выполнение (сек)",
        validators=[MinValueValidator(1), MaxValueValidator(120)],
        help_text="Не больше 120 секунд",
    )

    is_public = models.BooleanField(
        default=False, verbose_name="Публичная привычка", help_text="Доступна для просмотра другим пользователям"
    )

    # Служебные поля
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.action} в {self.time}"

    def clean(self):
        """Валидация модели"""
        # Проверка 1: Нельзя заполнить и reward и linked_habit одновременно
        if self.reward and self.linked_habit:
            raise ValidationError("Нельзя указать одновременно вознаграждение и связанную привычку")

        # Проверка 2: У приятной привычки не может быть вознаграждения
        if self.is_pleasant and self.reward:
            raise ValidationError("У приятной привычки не может быть вознаграждения")

        # Проверка 3: У приятной привычки не может быть связанной привычки
        if self.is_pleasant and self.linked_habit:
            raise ValidationError("У приятной привычки не может быть связанной привычки")

        # Проверка 4: Связанная привычка должна быть приятной
        if self.linked_habit and not self.linked_habit.is_pleasant:
            raise ValidationError("Связанная привычка должна быть приятной")

        # Проверка 5: Периодичность не может быть больше 7 дней
        if self.periodicity > 7:
            raise ValidationError("Нельзя выполнять привычку реже 1 раза в 7 дней")

    def save(self, *args, **kwargs):
        """Переопределяем save для вызова валидации"""
        self.full_clean()  # Вызываем валидацию перед сохранением
        super().save(*args, **kwargs)
