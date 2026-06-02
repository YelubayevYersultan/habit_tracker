from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


# ==========================================
# 1. ОБНОВЛЕННАЯ МОДЕЛЬ ПРИВЫЧКИ (БЕЗ ВРЕМЕНИ ВЫПОЛНЕНИЯ)
# ==========================================
class Habit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    title = models.CharField(max_length=150, verbose_name="Действие (что сделать)")
    reminder_time = models.TimeField(verbose_name="Время напоминания")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    is_pleasant = models.BooleanField(default=False, verbose_name="Приятная привычка")
    reward = models.CharField(max_length=255, blank=True, null=True, verbose_name="Вознаграждение (текст)")
    associated_habit = models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True,
                                         verbose_name="Связанная приятная привычка")
    last_sent_date = models.DateField(null=True, blank=True, verbose_name="Дата последней отправки")

    # 👇 НАШЕ ПОЛЕ ДЛЯ QA ТРЕКИНГА СТАТУСА
    is_completed = models.BooleanField(default=False, verbose_name="Выполнена сегодня")

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"
        ordering = ['-created_at']

    def clean(self):
        super().clean()

        if self.reward and self.associated_habit:
            raise ValidationError(
                "Вы не можете выбрать одновременно и текстовое вознаграждение, и связанную привычку. Выберите что-то одно."
            )

        if self.is_pleasant:
            if self.reward or self.associated_habit:
                raise ValidationError(
                    "У приятной привычки не может быть вознаграждения или связанной привычки. Она сама по себе является наградой."
                )

        if self.associated_habit and not self.associated_habit.is_pleasant:
            raise ValidationError(
                "В связанные привычки можно добавлять только те привычки, у которых стоит отметка 'Приятная привычка'."
            )

    def __str__(self):
        return f"{self.title} в {self.reminder_time}"


# ==========================================
# 2. МОДЕЛЬ ПРОФИЛЯ
# ==========================================
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    telegram_id = models.BigIntegerField(unique=True, blank=True, null=True, verbose_name="Telegram ID")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return f"Профиль: {self.user.username} (TG: {self.telegram_id})"


# ==========================================
# 3. СИГНАЛЫ ДЛЯ АВТОМАТИЧЕСКОГО СОЗДАНИЯ ПРОФИЛЯ
# ==========================================
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
