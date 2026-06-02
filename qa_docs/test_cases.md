# API Test Cases & Coverage Matrix

Документ содержит тест-кейсы, покрытые автоматизированными интеграционными тестами из `habits/tests.py`.

## TC-API-01. Получение списка привычек без авторизации

**Тип:** Negative

**Шаги:**
1. Отправить `GET /api/habits/` без JWT-токена.

**Ожидаемый результат:**
- Статус ответа: `401 Unauthorized`.

---

## TC-API-02. Изоляция данных пользователей

**Тип:** Security

**Предусловия:**
- Существует привычка пользователя `User_A`.
- Выполнена авторизация под `User_B`.

**Шаги:**
1. Отправить `GET /api/habits/` от имени `User_B`.

**Ожидаемый результат:**
- Статус ответа: `200 OK`.
- Привычки `User_A` отсутствуют в ответе.

---

## TC-API-03. Успешное создание привычки

**Тип:** Positive

**Шаги:**
1. Авторизоваться под `User_A`.
2. Отправить `POST /api/habits/` с валидными данными.

**Ожидаемый результат:**
- Статус ответа: `201 Created`.
- Привычка сохранена в БД.

---

## TC-API-04. Конфликт награды и связанной привычки

**Тип:** Negative

**Предусловия:**
- Существует приятная привычка (`ID=5`).

**Шаги:**
1. Отправить `POST /api/habits/`, указав одновременно `reward` и `associated_habit`.

**Ожидаемый результат:**
- Статус ответа: `400 Bad Request`.
- Ошибка валидации.

---

## TC-API-05. Приятная привычка с вознаграждением

**Тип:** Negative

**Шаги:**
1. Отправить `POST /api/habits/` с параметрами:
    - `is_pleasant=true`
    - `reward=<значение>`

**Ожидаемый результат:**
- Статус ответа: `400 Bad Request`.
- Ошибка валидации.

---

## TC-API-06. Первичное выполнение привычки

**Тип:** Positive

**Шаги:**
1. Отправить `POST /api/habits/{id}/complete/`.

**Ожидаемый результат:**
- Статус ответа: `200 OK`.
- Поле `is_completed=true`.

---

## TC-API-07. Повторное выполнение привычки

**Тип:** Negative

**Предусловия:**
- Привычка уже выполнена сегодня.

**Шаги:**
1. Повторно вызвать `POST /api/habits/{id}/complete/`.

**Ожидаемый результат:**
- Статус ответа: `400 Bad Request`.
- Сообщение: `"Привычка уже была выполнена сегодня!"`.

---

## TC-API-08. Выполнение чужой привычки

**Тип:** Security (IDOR)

**Предусловия:**
- Пользователь `User_B` авторизован.
- Привычка принадлежит `User_A`.

**Шаги:**
1. Отправить `POST /api/habits/{foreign_id}/complete/`.

**Ожидаемый результат:**
- Статус ответа: `404 Not Found`.

---

## TC-API-09. Успешное удаление привычки

**Тип:** Positive

**Шаги:**
1. Отправить `DELETE /api/habits/{id}/`.

**Ожидаемый результат:**
- Статус ответа: `204 No Content`.
- Запись удалена из БД.

---

## TC-API-10. Удаление чужой привычки

**Тип:** Security (IDOR)

**Предусловия:**
- Пользователь `User_B` авторизован.
- Привычка принадлежит `User_A`.

**Шаги:**
1. Отправить `DELETE /api/habits/{foreign_id}/`.

**Ожидаемый результат:**
- Статус ответа: `404 Not Found`.
- Удаление не выполнено.

---

## TC-API-11. Автоматическое создание профиля пользователя

**Тип:** Integration

**Шаги:**
1. Отправить `POST /api/register/` с валидными данными и `telegram_id`.

**Ожидаемый результат:**
- Статус ответа: `201 Created`.
- Создан пользователь.
- Создан связанный профиль (`UserProfile`).
- `telegram_id` сохранён корректно.

# Coverage Matrix

| ID | Test Case | Category | Automated |
|----|-----------|----------|-----------|
| TC-API-01 | Unauthorized access | Access Control | ✅ |
| TC-API-02 | User data isolation | Security | ✅ |
| TC-API-03 | Habit creation | CRUD | ✅ |
| TC-API-04 | Reward + associated habit validation | Validation | ✅ |
| TC-API-05 | Pleasant habit validation | Validation | ✅ |
| TC-API-06 | First completion | Business Logic | ✅ |
| TC-API-07 | Duplicate completion | Business Logic | ✅ |
| TC-API-08 | Foreign habit completion | Security (IDOR) | ✅ |
| TC-API-09 | Habit deletion | CRUD | ✅ |
| TC-API-10 | Foreign habit deletion | Security (IDOR) | ✅ |
| TC-API-11 | Profile auto creation | Integration | ✅ |ё