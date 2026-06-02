from django.shortcuts import render
from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from drf_spectacular.utils import extend_schema, extend_schema_view  # 🚀 Импорт инструментов документации
from .models import Habit
from .serializers import HabitSerializer, RegisterSerializer


@extend_schema_view(
    list=extend_schema(summary="Получить список привычек",
                       description="Возвращает список всех привычек текущего авторизованного пользователя."),
    create=extend_schema(summary="Создать новую привычку",
                         description="Создает привычку и автоматически привязывает её к текущему пользователю."),
    retrieve=extend_schema(summary="Получить детали привычки",
                           description="Возвращает подробную информацию о конкретной привычке по её ID."),
    update=extend_schema(summary="Полностью обновить привычку",
                         description="Полное обновление всех полей существующей привычки."),
    partial_update=extend_schema(summary="Частично обновить привычку",
                                 description="Изменение отдельных полей привычки."),
    destroy=extend_schema(summary="Удалить привычку", description="Удаляет привычку из базы данных по её ID.")
)
class HabitViewSet(viewsets.ModelViewSet):
    """
    Эндпоинт для работы с привычками.
    Автоматически поддерживает: GET, POST, PUT, PATCH, DELETE.
    """
    serializer_class = HabitSerializer
    # 🔒 Закрываем API от анонимных пользователей. Работать с ним могут только авторизованные.
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Этот метод фильтрует привычки на уровне API.
        Обычный пользователь видит ТОЛЬКО свои привычки. Суперадмин видит все.
        """
        user = self.request.user
        if user.is_superuser:
            return Habit.objects.all()
        return Habit.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Этот метод автоматически привязывает текущего пользователя к создаваемой привычке.
        Django сам вытащит юзера из JWT-токена и запишет в поле user модели Habit.
        """
        serializer.save(user=self.request.user)

    # 🚀 Аннотируем наш кастомный эндпоинт выполнения для Swagger:
    @extend_schema(
        summary="Отметить привычку выполненной сегодня",
        description="Переключает флаг is_completed в True. Доступно только владельцу привычки.",
        responses={
            200: {"description": "Успешное выполнение привычки 🎉"},
            400: {"description": "Привычка уже была выполнена сегодня"},
            401: {"description": "Не авторизован (отсутствует или истек токен)"},
            404: {"description": "Привычка не найдена"}
        }
    )
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """
        Кастомный экшен, который отмечает привычку как выполненную.
        """
        habit = self.get_object()  # Django сам найдет нужную привычку текущего юзера по ID (pk)

        if habit.is_completed:
            return Response(
                {"message": f"Привычка '{habit.title}' уже была выполнена сегодня!"},
                status=status.HTTP_400_BAD_REQUEST
            )

        habit.is_completed = True
        habit.save()

        return Response(
            {"message": f"Привычка '{habit.title}' успешно выполнена сегодня! 🎉"},
            status=status.HTTP_200_OK
        )


@extend_schema(
    summary="Регистрация нового пользователя",
    description="Создает новую учетную запись пользователя и автоматически генерирует для него пустой профиль UserProfile."
)
class RegisterView(generics.CreateAPIView):
    """
    Эндпоинт для регистрации нового пользователя через Telegram-бота.
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)  # Доступно всем без токена
    serializer_class = RegisterSerializer
