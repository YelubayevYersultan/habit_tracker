from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from habits.views import HabitViewSet, RegisterView

# 🚀 Импортируем вьюшки для генерации Swagger и Redoc документации
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# 🚀 Импортируем вьюшки для токенов
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register(r'habits', HabitViewSet, basename='habit')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),

    # 🚀 Эндпоинты для авторизации:
    # 1. Сюда бот отправляет логин/пароль и получает Access и Refresh токен
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    # 2. Сюда бот отправляет старый Refresh токен, чтобы обновить истекший Access токен
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # 3. Эндпоинт для регистрации пользователей
    path('api/register/', RegisterView.as_view(), name='auth_register'),

    # 📋 Эндпоинты автодокументации API (OpenAPI 3.0):
    # Скачивание сырого JSON/YAML файла спецификации
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Интерактивный Swagger UI интерфейс
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # Альтернативный интерфейс документации Redoc
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
