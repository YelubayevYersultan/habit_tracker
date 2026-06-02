from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Habit, UserProfile

User = get_user_model()


# ==========================================
# 1. ОБНОВЛЕННЫЙ СЕРИАЛИЗАТОР ПРИВЫЧКИ
# ==========================================
class HabitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = '__all__'
        read_only_fields = ('user',)

    def validate(self, data):
        is_pleasant = data.get('is_pleasant', False)
        reward = data.get('reward', None)
        associated_habit = data.get('associated_habit', None)

        if reward and associated_habit:
            raise serializers.ValidationError(
                "Нельзя одновременно выбрать текстовое вознаграждение и связанную привычку."
            )

        if is_pleasant and (reward or associated_habit):
            raise serializers.ValidationError(
                "У приятной привычки не может быть вознаграждения или связанной привычки."
            )

        if associated_habit and not associated_habit.is_pleasant:
            raise serializers.ValidationError(
                "В связанные привычки можно добавлять только приятные привычки."
            )

        return data


# ==========================================
# 2. СЕРИАЛИЗАТОР ДЛЯ РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЕЙ
# ==========================================
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    telegram_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'telegram_id')

    def create(self, validated_data):
        telegram_id = validated_data.pop('telegram_id')

        # Создаем пользователя
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )

        # 👇 Безопасное получение или создание профиля (исправляет падение Swagger)
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.telegram_id = telegram_id
        profile.save()

        return user
