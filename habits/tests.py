from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Habit

User = get_user_model()


class ExtendedHabitAPITestCase(APITestCase):

    def setUp(self):
        """
        Фикстуры для тестов. Выполняются перед каждым тест-кейсом.
        """
        # Юзер 1 и его обычная привычка
        self.user1 = User.objects.create_user(username="testuser1", password="password123")
        self.habit1 = Habit.objects.create(
            user=self.user1,
            title="Утренняя пробежка",
            reminder_time="07:00:00",
            reward="Вкусный смузи",
            is_pleasant=False,
            is_completed=False
        )

        # Приятная привычка (нужна для тестов валидации связанных привычек)
        self.pleasant_habit = Habit.objects.create(
            user=self.user1,
            title="Послушать музыку Макса Коржа",
            reminder_time="18:00:00",
            is_pleasant=True,
            is_completed=False
        )

        # Юзер 2 для проверки изоляции данных (Security / Access Control)
        self.user2 = User.objects.create_user(username="testuser2", password="password123")

    # =========================================================================
    # БЛОК 1: ТЕСТЫ АВТОРИЗАЦИИ И ДОСТУПА (Authentication & Access Control)
    # =========================================================================

    def test_get_habits_unauthorized(self):
        """TC-01: Запрос списка без токена должен возвращать 401 Четко по ТЗ"""
        url = reverse('habit-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_data_isolation(self):
        """TC-02: Тест изоляции данных. Юзер 2 не должен видеть привычки Юзера 1"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('habit-list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # Список должен быть пуст для Юзера 2

    # =========================================================================
    # БЛОК 2: ТЕСТЫ ВАЛИДАЦИИ И СОЗДАНИЯ (CRUD: Create & Validation)
    # =========================================================================

    def test_create_habit_success(self):
        """TC-03: Успешное создание привычки авторизованным юзером"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('habit-list')
        payload = {
            "title": "Читать книгу",
            "reminder_time": "22:00:00",
            "reward": "15 минут отдыха",
            "is_pleasant": False
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.filter(user=self.user1).count(), 3)

    def test_validation_reward_and_associated_habit_conflict(self):
        """TC-04: Бизнес-логика: Нельзя одновременно указать награду и связанную привычку"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('habit-list')
        payload = {
            "title": "Учить Python",
            "reminder_time": "10:00:00",
            "reward": "Шоколадка",  # Конфликт: есть награда
            "associated_habit": self.pleasant_habit.id,  # и есть связанная привычка
            "is_pleasant": False
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Нельзя одновременно выбрать текстовое вознаграждение", response.data['non_field_errors'][0])

    def test_validation_pleasant_habit_cannot_have_reward(self):
        """TC-05: Бизнес-логика: У приятной привычки не может быть вознаграждения"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('habit-list')
        payload = {
            "title": "Смотреть YouTube",
            "reminder_time": "20:00:00",
            "reward": "Купить пиццу",  # Конфликт: приятная привычка не требует награды
            "is_pleasant": True
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("У приятной привычки не может быть вознаграждения", response.data['non_field_errors'][0])

    # =========================================================================
    # БЛОК 3: ТЕСТЫ КАСТОМНОГО ЭНДПОИНТА ВЫПОЛНЕНИЯ (Custom Action: Complete)
    # =========================================================================

    def test_complete_habit_success(self):
        """TC-06: Успешное выполнение привычки в первый раз за день"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('habit-complete', kwargs={'pk': self.habit1.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.habit1.refresh_from_db()
        self.assertTrue(self.habit1.is_completed)

    def test_complete_habit_double_click(self):
        """TC-07: Идемпотентность/Валидация: Нельзя выполнить одну привычку дважды за день"""
        self.habit1.is_completed = True
        self.habit1.save()

        self.client.force_authenticate(user=self.user1)
        url = reverse('habit-complete', kwargs={'pk': self.habit1.pk})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("уже была выполнена сегодня", response.data['message'])

    def test_complete_foreign_habit_denied(self):
        """TC-08: Безопасность: Юзер 2 получает 404 при попытке выполнить привычку Юзера 1"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('habit-complete', kwargs={'pk': self.habit1.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # =========================================================================
    # БЛОК 4: ТЕСТЫ УДАЛЕНИЯ И РЕГИСТРАЦИИ (CRUD: Delete & Registration)
    # =========================================================================

    def test_delete_habit_success(self):
        """TC-09: Успешное удаление собственной привычки (Используется ботом)"""
        self.client.force_authenticate(user=self.user1)
        url = reverse('habit-detail', kwargs={'pk': self.habit1.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(pk=self.habit1.pk).exists())

    def test_delete_foreign_habit_denied(self):
        """TC-10: Безопасность: Юзер 2 не может удалить привычку Юзера 1"""
        self.client.force_authenticate(user=self.user2)
        url = reverse('habit-detail', kwargs={'pk': self.habit1.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Habit.objects.filter(pk=self.habit1.pk).exists())

    def test_registration_creates_profile(self):
        """TC-11: Интеграционный тест: Регистрация создает User и привязывает к нему UserProfile"""
        url = reverse('auth_register')
        payload = {
            "username": "telegram_bot_user",
            "password": "securepassword123",
            "telegram_id": 999888777
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, создался ли юзер и замапился ли его Telegram ID в профиль
        new_user = User.objects.get(username="telegram_bot_user")
        self.assertEqual(new_user.profile.telegram_id, 999888777)
