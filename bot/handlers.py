import os
import httpx
import redis
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from states import AddHabitForm, RegisterForm, LoginForm  # Импортируем состояния

router = Router()

# Подключаемся к Redis. Контейнер называется 'redis', данные будут жить даже после рестарта бота.
redis_client = redis.Redis(host='redis', port=6379, db=1, decode_responses=True)


# --- КЛАВИАТУРЫ ---

# 1. Меню для неавторизованных пользователей
def get_auth_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📝 Зарегистрироваться"),
                KeyboardButton(text="🔐 Войти")
            ]
        ],
        resize_keyboard=True
    )


# 2. Главное меню для работы с привычками
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📋 Мои привычки"),
                KeyboardButton(text="➕ Добавить привычку")
            ]
        ],
        resize_keyboard=True
    )


# --- ОБРАБОТКА КОМАНДЫ /START ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()  # Сбрасываем любые зависшие состояния

    tg_id = message.from_user.id

    # Проверяем в Redis, есть ли сохраненная сессия (токен) для этого пользователя
    if redis_client.get(str(tg_id)):
        await message.answer(
            f"Привет, {message.from_user.first_name}! Рад видеть тебя снова.\n"
            "Твоя сессия активна. Используй меню ниже для управления привычками 👇",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            f"Привет! Я бот-трекер привычек.\n"
            "Чтобы начать пользоваться сервисом, тебе нужно зарегистрироваться или войти в свой аккаунт 👇",
            reply_markup=get_auth_keyboard()
        )


# ==========================================
# БЛОК РЕГИСТРАЦИИ ПОЛЬЗОВАТЕЛЯ (FSM)
# ==========================================

@router.message(F.text == "📝 Зарегистрироваться")
async def start_registration(message: Message, state: FSMContext):
    await state.set_state(RegisterForm.username)
    await message.answer("Шаг 1: Придумай и введи уникальный логин (username):")


@router.message(RegisterForm.username)
async def process_reg_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(RegisterForm.password)
    await message.answer("Шаг 2: Придумай и введи пароль:")


@router.message(RegisterForm.password)
async def process_reg_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    user_data = await state.get_data()
    await state.clear()

    payload = {
        "username": user_data['username'],
        "password": user_data['password'],
        "telegram_id": message.from_user.id  # Передаем реальный ID чата для бэкенда Django
    }

    await message.answer("Регистрирую тебя на сервере... ⏳")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://web:8000/api/register/", json=payload)
            if response.status_code == 201:
                await message.answer(
                    "🎉 Регистрация прошла успешно! Теперь нажми кнопку <b>«🔐 Войти»</b>, чтобы авторизоваться.",
                    parse_mode="HTML",
                    reply_markup=get_auth_keyboard()
                )
            else:
                error_msg = response.json()
                await message.answer(f"❌ Ошибка регистрации: {error_msg}. Попробуй другой логин.")
        except Exception as e:
            await message.answer("❌ Ошибка подключения к серверу при регистрации.")
            print(f"Reg error: {e}")


# ==========================================
# БЛОК АВТОРИЗАЦИИ (ВХОД В АККАУНТ)
# ==========================================

@router.message(F.text == "🔐 Войти")
async def start_login(message: Message, state: FSMContext):
    await state.set_state(LoginForm.username)
    await message.answer("Введи свой логин:")


@router.message(LoginForm.username)
async def process_login_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text)
    await state.set_state(LoginForm.password)
    await message.answer("Введи свой пароль:")


@router.message(LoginForm.password)
async def process_login_password(message: Message, state: FSMContext):
    await state.update_data(password=message.text)
    user_data = await state.get_data()
    await state.clear()

    payload = {
        "username": user_data['username'],
        "password": user_data['password']
    }

    await message.answer("Проверяю данные... 🔐")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://web:8000/api/token/", json=payload)
            if response.status_code == 200:
                tokens = response.json()

                # 💾 Сохраняем access-токен в Redis. Ключ — string от tg_id.
                # Ставим время жизни (ex) 30 дней в секундах, чтобы кэш автоматически чистился.
                tg_id = str(message.from_user.id)
                redis_client.set(tg_id, tokens['access'], ex=30 * 24 * 60 * 60)

                await message.answer(
                    "🔑 Авторизация успешна! Добро пожаловать.\nТеперь тебе доступны все функции.",
                    reply_markup=get_main_keyboard()
                )
            else:
                await message.answer("❌ Неверный логин или пароль. Попробуй войти снова.")
        except Exception as e:
            await message.answer("❌ Ошибка сервера при авторизации.")
            print(f"Login error: {e}")


# ==========================================
# РАБОТА С ПРИВЫЧКАМИ (HTML ПАРСИНГ)
# ==========================================

@router.message(F.text == "📋 Мои привычки")
async def list_habits(message: Message):
    tg_id = str(message.from_user.id)

    # 🔍 Достаем токен из Redis
    token = redis_client.get(tg_id)

    if not token:
        await message.answer("🔒 Ты не авторизован. Пожалуйста, нажми «🔐 Войти».", reply_markup=get_auth_keyboard())
        return

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://web:8000/api/habits/", headers=headers)
            if response.status_code == 200:
                habits = response.json()
                if not habits:
                    await message.answer("У тебя пока нет созданных привычек.")
                    return

                # 👇 Заголовок переведен на HTML
                await message.answer("📋 <b>Твои привычки на сегодня:</b>", parse_mode="HTML")

                for h in habits:
                    is_done = h.get('is_completed')
                    # 👇 Форматирование статусов через HTML-теги
                    status_emoji = "✅ <b>Выполнено</b>" if is_done else "⏳ <b>В процессе</b>"

                    # 👇 Формируем безопасный HTML-текст (теги <b> вместо звездочек)
                    text = (
                        f"🔹 <b>{h.get('title')}</b> — в {h.get('reminder_time')}\n"
                        f"Статус: {status_emoji}\n"
                        f"Вознаграждение: {h.get('reward', 'Нет')}"
                    )

                    # Динамически собираем inline-кнопки в один ряд
                    inline_buttons = []

                    # 1. Кнопка выполнения (только для незавершенных привычек)
                    if not is_done:
                        inline_buttons.append(
                            InlineKeyboardButton(
                                text="Выполнить ✅",
                                callback_data=f"complete_{h.get('id')}"
                            )
                        )

                    # 2. Кнопка удаления (доступна всегда)
                    inline_buttons.append(
                        InlineKeyboardButton(
                            text="Удалить ❌",
                            callback_data=f"delete_{h.get('id')}"
                        )
                    )

                    reply_markup = InlineKeyboardMarkup(inline_keyboard=[inline_buttons])

                    # 👇 Отправляем сообщение строго как HTML
                    await message.answer(text, parse_mode="HTML", reply_markup=reply_markup)
            else:
                # Если бэкенд вернул 401/403 (токен просрочен), удаляем его из Redis
                redis_client.delete(tg_id)
                await message.answer("Сессия истекла. Войди в аккаунт заново.", reply_markup=get_auth_keyboard())
        except Exception as e:
            # Логируем точную ошибку в консоль контейнера
            print(f"Ошибка в list_habits: {e}")
            await message.answer("Ошибка подключения к серверу.")


# 👇 ОБРАБОТЧИК КЛИКА ПО КНОПКЕ "ВЫПОЛНИТЬ" (POST)
@router.callback_query(F.data.startswith("complete_"))
async def process_complete_habit(callback: CallbackQuery):
    tg_id = str(callback.from_user.id)
    habit_id = callback.data.split("_")[1]

    token = redis_client.get(tg_id)
    if not token:
        await callback.answer("Сессия истекла. Войди заново.", show_alert=True)
        return

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            # Отправляем запрос на кастомный эндпоинт Django
            response = await client.post(f"http://web:8000/api/habits/{habit_id}/complete/", headers=headers)

            if response.status_code == 200:
                await callback.answer("Привычка выполнена! 🎉")

                # Достаем старый текст, заменяем статус и сохраняем теги жирного шрифта через HTML
                old_text = callback.message.text
                new_text = old_text.replace("⏳ В процессе", "✅ Выполнено")

                # После выполнения оставляем ТОЛЬКО кнопку удаления
                only_delete_markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="Удалить ❌", callback_data=f"delete_{habit_id}")
                        ]
                    ]
                )

                # 👇 Обязательно передаем parse_mode="HTML", чтобы сообщение обновилось корректно
                await callback.message.edit_text(new_text, reply_markup=only_delete_markup, parse_mode="HTML")
            else:
                error_data = response.json()
                await callback.answer(error_data.get("message", "Ошибка при выполнении"), show_alert=True)
        except Exception as e:
            print(f"Ошибка в process_complete_habit: {e}")
            await callback.answer("Не удалось связаться с сервером.", show_alert=True)


# 👇 ОБРАБОТЧИК КЛИКА ПО КНОПКЕ "УДАЛИТЬ" (DELETE)
@router.callback_query(F.data.startswith("delete_"))
async def process_delete_habit(callback: CallbackQuery):
    tg_id = str(callback.from_user.id)
    habit_id = callback.data.split("_")[1]

    token = redis_client.get(tg_id)
    if not token:
        await callback.answer("Сессия истекла. Войди заново.", show_alert=True)
        return

    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            # Отправляем DELETE-запрос на стандартный REST URL бэкенда Django
            response = await client.delete(f"http://web:8000/api/habits/{habit_id}/", headers=headers)

            if response.status_code == 204:  # 204 No Content — успешный код удаления в DRF по умолчанию
                await callback.answer("Привычка успешно удалена! 🗑")
                # Полностью удаляем сообщение с этой привычкой из ленты бота
                await callback.message.delete()
            else:
                await callback.answer("Не удалось удалить привычку. Возможно, она уже удалена.", show_alert=True)
        except Exception as e:
            print(f"Ошибка в process_delete_habit: {e}")
            await callback.answer("Ошибка связи с сервером при удалении.", show_alert=True)


# ==========================================
# БЛОК ДОБАВЛЕНИЯ ПРИВЫЧКИ (FSM)
# ==========================================

@router.message(F.text == "➕ Добавить привычку")
async def start_add_habit(message: Message, state: FSMContext):
    tg_id = str(message.from_user.id)

    # Проверяем наличие сессии перед запуском FSM формы
    if not redis_client.get(tg_id):
        await message.answer("🔒 Сначала войди в аккаунт!", reply_markup=get_auth_keyboard())
        return

    await state.set_state(AddHabitForm.name)
    await message.answer("Шаг 1: Введи название привычки (например: <b>Пить воду</b>):", parse_mode="HTML")


@router.message(AddHabitForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddHabitForm.time)
    await message.answer("Шаг 2: Введи время в формате ЧЧ:ММ (например: <b>08:30</b>):", parse_mode="HTML")


@router.message(AddHabitForm.time)
async def process_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await state.set_state(AddHabitForm.reward)
    await message.answer("Шаг 3: Какая будет награда? (например: <b>Вкусный кофе</b>):", parse_mode="HTML")


@router.message(AddHabitForm.reward)
async def process_reward(message: Message, state: FSMContext):
    await state.update_data(reward=message.text)
    user_data = await state.get_data()
    await state.clear()

    habit_payload = {
        "title": user_data['name'],
        "reminder_time": f"{user_data['time']}:00",
        "reward": user_data['reward'],
        "is_pleasant": False
    }

    tg_id = str(message.from_user.id)
    token = redis_client.get(tg_id)
    headers = {"Authorization": f"Bearer {token}"}

    await message.answer("Отправляю данные на сервер... ⏳")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://web:8000/api/habits/", json=habit_payload, headers=headers)
            if response.status_code == 201:
                await message.answer(
                    f"🎉 Привычка <b>\"{user_data['name']}\"</b> успешно создана!",
                    parse_mode="HTML",
                    reply_markup=get_main_keyboard()
                )
            else:
                await message.answer(f"❌ Ошибка сервера ({response.status_code}).", reply_markup=get_main_keyboard())
        except Exception as e:
            await message.answer("❌ Не удалось связаться с сервером.", reply_markup=get_main_keyboard())
