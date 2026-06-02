# Test Plan – Habit Tracker

## 1. Overview

### Project

Habit Tracker — приложение для управления привычками, состоящее из следующих компонентов:

- Django REST Framework API
- PostgreSQL
- Redis
- Telegram Bot
- Docker Compose Environment

### Purpose

Цель тестирования — проверить корректность работы бизнес-логики, безопасность API, интеграцию Telegram Bot с Backend и стабильность приложения в Docker-окружении.

---

## 2. Scope

### In Scope

#### Backend API

- Регистрация пользователей
- JWT-аутентификация
- CRUD-операции для привычек
- Кастомный endpoint `/complete/`

#### Business Logic

- Валидация создания привычек
- Ограничения для приятных привычек
- Проверка выполнения привычки один раз в сутки

#### Security Testing

- Авторизация пользователей
- Изоляция пользовательских данных
- Проверка защиты от IDOR

#### Integration Testing

- Telegram Bot ↔ Backend API
- Callback обработчики
- Отображение сообщений в Telegram

---

### Out of Scope

- Performance Testing
- Load Testing
- Stress Testing
- Telegram Infrastructure Testing
- Penetration Testing

---

## 3. Test Objectives

Проверить:

- корректность работы REST API;
- выполнение бизнес-требований;
- безопасность доступа к данным;
- корректность интеграции Telegram Bot и Backend;
- стабильность работы Docker-окружения.

---

## 4. Test Types

| Test Type | Description |
|------------|-------------|
| Functional Testing | Проверка бизнес-функциональности |
| API Testing | Проверка REST API |
| Integration Testing | Проверка взаимодействия компонентов |
| Security Testing | Проверка доступа и авторизации |
| Regression Testing | Проверка после внесения изменений |

---

## 5. Test Environment

### Infrastructure

| Component | Technology |
|------------|------------|
| Backend | Django REST Framework |
| Database | PostgreSQL |
| Cache | Redis |
| Bot | Aiogram |
| Containerization | Docker Compose |
| Testing Framework | Django APITestCase |

### Environment

```bash
docker-compose up -d
```

Сервисы:

- web
- bot
- db
- redis

---

## 6. Entry Criteria

Тестирование начинается при выполнении следующих условий:

- Docker-контейнеры успешно запущены;
- PostgreSQL доступен;
- миграции выполнены без ошибок;
- Swagger/OpenAPI документация доступна;
- тестовая база данных создаётся корректно.

---

## 7. Exit Criteria

Тестирование считается завершённым при выполнении следующих условий:

- все автоматизированные тесты успешно проходят;
- отсутствуют открытые дефекты уровня Blocker и Critical;
- успешно пройдены E2E-сценарии через Telegram Bot;
- достигнуто 100% покрытие критической бизнес-логики.

---

## 8. Test Strategy

### Automated Testing

Выполняется с использованием:

```python
rest_framework.test.APITestCase
```

Покрываемые сценарии:

- позитивные проверки;
- негативные проверки;
- проверки безопасности;
- интеграционные сценарии.

### Manual Testing

Проверяются сценарии взаимодействия через Telegram Bot:

- отображение списка привычек;
- создание привычек;
- выполнение привычек;
- удаление привычек;
- работа inline-кнопок;
- корректность HTML-разметки сообщений.

---

## 9. Test Deliverables

В рамках проекта подготовлены следующие QA-артефакты:

- Test Plan
- Test Cases
- Bug Reports Log
- API Coverage Matrix
- Automated Tests
- Postman Collection

---

## 10. Risks

| Risk | Probability | Impact | Mitigation |
|--------|------------|---------|------------|
| Docker networking issues | Medium | High | Использование Docker DNS (`web:8000`) |
| PostgreSQL locale conflicts | Medium | High | Настройка параметров TEST DATABASE |
| Telegram parsing errors | Medium | Medium | Использование HTML Parse Mode |
| JWT authorization failures | Low | High | Покрытие интеграционными тестами |

---

## 11. Resources

| Role | Responsibilities |
|--------|------------------|
| QA Engineer | Test Design, Test Execution, Bug Reporting |
| Developer | Bug Fixing, Code Review |

---

## 12. Metrics

| Metric | Value |
|----------|--------|
| Automated Test Cases | 11 |
| Bug Reports | 4 |
| Critical Open Defects | 0 |
| Security Test Cases | 4 |
| Integration Test Cases | 1 |