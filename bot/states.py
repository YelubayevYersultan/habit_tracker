from aiogram.fsm.state import State, StatesGroup


# Состояния для формы добавления привычки
class AddHabitForm(StatesGroup):
    name = State()
    time = State()
    reward = State()


# 📝 Состояния для регистрации нового аккаунта
class RegisterForm(StatesGroup):
    username = State()
    password = State()


# 🔐 Состояния для входа в существующий аккаунт
class LoginForm(StatesGroup):
    username = State()
    password = State()
