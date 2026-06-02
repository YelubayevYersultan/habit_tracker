# Bug Reports Log

Журнал дефектов, обнаруженных и устранённых в процессе разработки и тестирования проекта Habit Tracker (Django REST
Framework + Telegram Bot + Docker).

## BUG-001. Telegram Bot не может подключиться к Backend API

**Status:** Closed  
**Severity:** Blocker  
**Priority:** High  
**Component:** Docker Network

### Preconditions

Сервисы запущены через Docker Compose.

### Steps to Reproduce

1. Выполнить запуск проекта:
   ```bash
   docker-compose up -d
   ```

2. В коде бота выполнить запрос:

   ```python
   http://localhost:8000/api/habits/
   ```

### Expected Result

Бот успешно получает ответ от Django API.

### Actual Result

Возникает ошибка подключения:

```text
httpx.ConnectError: [Errno -2] Name or service not known
```

### Root Cause

Внутри Docker-контейнера адрес `localhost` указывает на сам контейнер бота, а не на контейнер Django.

### Resolution

URL изменён на Docker DNS-имя сервиса:

```python
http: // web: 8000 / api / habits /
```

---

## BUG-002. Ошибка запуска Django из-за некорректного INSTALLED_APPS

**Status:** Closed  
**Severity:** Blocker  
**Priority:** High  
**Component:** Django Configuration

### Steps to Reproduce

1. Открыть файл `settings.py`.
2. Добавить приложение `'drf_spectacular'`.
3. Пропустить запятую между `'drf_spectacular'` и `'habits'`.
4. Запустить приложение.

### Expected Result

Django успешно запускается.

### Actual Result

Приложение завершается с ошибкой:

```text
ModuleNotFoundError: No module named 'drf_spectacularhabits'
```

### Root Cause

Python автоматически склеивает соседние строковые литералы при отсутствии разделителя.

### Resolution

Добавлена пропущенная запятая в списке `INSTALLED_APPS`.

---

## BUG-003. Падение Telegram Bot при обновлении сообщения

**Status:** Closed  
**Severity:** Major  
**Priority:** High  
**Component:** Telegram Bot UI

### Steps to Reproduce

1. Открыть список привычек в Telegram-боте.
2. Нажать кнопку «Выполнить ✅».
3. Выполнить обновление сообщения через:

```python
callback.message.edit_text(..., parse_mode="MarkdownV2")
```

### Expected Result

Сообщение успешно обновляется.

### Actual Result

Бот завершает выполнение с ошибкой парсинга Telegram API.

Кнопка остаётся в состоянии загрузки.

### Root Cause

MarkdownV2 требует обязательного экранирования специальных символов:

```text
. - ( ) _ * [ ] ~ ` > # + = | { }
```

### Resolution

Форматирование переведено на HTML:

```python
parse_mode = "HTML"
```

Markdown-разметка заменена на HTML-теги:

```html
<b>Текст</b>
```

---

## BUG-004. Ошибка создания тестовой базы PostgreSQL

**Status:** Closed  
**Severity:** Major  
**Priority:** Medium  
**Component:** Database / Test Environment

### Steps to Reproduce

1. Запустить тестовый набор:

```bash
docker-compose exec web python manage.py test
```

### Expected Result

Создаётся временная тестовая база данных и запускаются тесты.

### Actual Result

Тестирование завершается ошибкой:

```text
Got an error creating the test database:
template database "template1" has a collation version...
```

### Root Cause

Конфликт локалей PostgreSQL между хостовой системой и Docker-контейнером.

### Resolution

Добавлена конфигурация тестовой базы данных:

```python
DATABASES = {
    'default': {
        'TEST': {
            'CHARSET': 'utf8',
            'COLLATION': 'en_US.UTF-8',
        }
    }
}
```

---

# Bug Summary

| ID      | Title                                                      | Severity | Priority | Status |
|---------|------------------------------------------------------------|----------|----------|--------|
| BUG-001 | Telegram Bot cannot reach Backend API                      | Blocker  | High     | Closed |
| BUG-002 | Django startup failure due to INSTALLED_APPS configuration | Blocker  | High     | Closed |
| BUG-003 | Telegram message update parsing error                      | Major    | High     | Closed |
| BUG-004 | PostgreSQL test database initialization failure            | Major    | Medium   | Closed |

## Statistics

| Metric      | Value |
|-------------|-------|
| Total Bugs  | 4     |
| Closed Bugs | 4     |
| Blocker     | 2     |
| Major       | 2     |
| Open Bugs   | 0     |