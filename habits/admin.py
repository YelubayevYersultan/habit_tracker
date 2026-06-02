from django.contrib import admin
from .models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    # 👇 Убрали 'time_to_complete' и добавили 'is_completed'
    list_display = ('id', 'user', 'title', 'is_pleasant', 'reminder_time', 'is_completed')

    # 👇 Добавили 'is_completed' в фильтры справа
    list_filter = ('is_pleasant', 'is_completed', 'user', 'reminder_time')
    search_fields = ('title',)

    # 🚀 ЛОГИКА ИЗОЛЯЦИИ ДАННЫХ:
    def get_queryset(self, request):
        # Берем базовый набор всех привычек из базы данных
        qs = super().get_queryset(request)

        # Если это суперпользователь (ты) — отдаем все привычки без ограничений
        if request.user.is_superuser:
            return qs

        # Если это обычный пользователь — показываем только те, где user равен ему самому
        return qs.filter(user=request.user)

    # 🚀 АВТОПОДСТАНОВКА ПОЛЬЗОВАТЕЛЯ ПРИ СОЗДАНИИ:
    def save_model(self, request, obj, form, change):
        # Если привычка создается с нуля (а не редактируется существующая)
        if not change:
            # Автоматически привязываем текущего авторизованного пользователя
            obj.user = request.user
        super().save_model(request, obj, form, change)
