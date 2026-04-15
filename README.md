## tg-logger-bot

Telegram-бот для логирования модерационных событий в основном чате, проверки доступа в служебные чаты администрации и управления кастомными текстовыми командами.

## Архитектура

Проект разложен по слоям:

- `src/app/config` — загрузка и валидация настроек.
- `src/app/bootstrap` — composition root: сборка контейнера зависимостей и `Dispatcher`.
- `src/app/domain` — модели и правила предметной области.
- `src/app/application` — сервисы и протоколы.
- `src/app/infrastructure` — SQLite и системные адаптеры.
- `src/app/presentation` — aiogram-роутеры, фильтры, middleware, парсеры, форматтеры, клавиатуры.
- `tests` — unit/integration-style проверки основных сценариев.

## Функциональность

- логирует:
  - самостоятельный выход из группы;
  - исключение пользователя администратором;
  - добавление пользователя другим участником;
  - самостоятельный вход пользователя;
  - редактирование сообщений;
  - изменение пользовательских ограничений;
  - выдачу прав администратора;
- проверяет join request в лог-чат и инфо-чат: пропускает только админов основного чата;
- поддерживает кастомные команды в SQLite с нормализацией имени и кэшем.
- сохраняет снапшоты сообщений для сравнения `было -> стало` при `edited_message`;
- ведёт structured logging по каждому update и отдаёт Prometheus-метрики.

## Системные апдейты

Бот собирает и логирует в `LOG_CHAT_ID` все системные события, которые реально доступны через Telegram Bot API:

- вход/выход/кик/изменение прав/назначение администратора;
- service messages внутри `CHAT_ID`: изменение названия, фото, автоудаления, закрепления, видеочаты, темы форума, миграцию чата, boost service message;
- реакции `message_reaction` и агрегированные `message_reaction_count`;
- `chat_boost` / `removed_chat_boost`;
- `my_chat_member` для отслеживания изменения статуса самого бота;
- редактирование сообщений с сохранением предыдущего состояния, если сообщение уже было известно боту.

Ограничение Telegram Bot API: обычное удаление сообщений в группах не приходит боту отдельным update. Поэтому кейс `удалил сообщение` нельзя реализовать только на Bot API и bot token без перехода на MTProto/userbot-архитектуру.

## Команды

- `+команда <имя>` на первой строке и текст ответа со второй строки — создать или обновить кастомную команду.
- `-команда <имя>` — удалить кастомную команду.
- `?команды` — показать список кастомных команд.

Изменять команды и публиковать `/start` может только `owner_id`.

## Локальный запуск

1. Создай `.env` по примеру из `.env.example`.
2. Установи зависимости: `uv sync`.
3. Запусти бота: `uv run tg-logger-bot`.

База данных по умолчанию хранится в `data/bot.db`. Если рядом лежит старый `bot.db`, приложение один раз перенесёт его в новую директорию данных.

## Проверки

- `uv run pytest`
- `uv run mypy`

## Логи И Метрики

- логи идут в stdout в JSON-формате;
- на каждый update формируется `trace_id`, `update_id`, `update_type`, шаги обработки и длительность;
- метрики Prometheus поднимаются встроенным HTTP server, по умолчанию на `0.0.0.0:9000`.

## Docker

Запуск через Compose:

```bash
docker compose up --build -d
```

Контейнер хранит SQLite в named volume `bot-data`, поэтому данные не теряются между пересозданиями контейнера.

## Grafana И Loki

Для observability-стека добавлен отдельный Docker profile `observability`. В него входят:

- `Prometheus` — забирает метрики у бота, Loki и Alloy;
- `Loki` — хранит логи;
- `Alloy` — собирает Docker stdout/stderr из контейнеров и отправляет в Loki;
- `Grafana` — уже с provisioned datasource и дашбордом `tg-logger-bot Observability`.

Запуск:

```bash
docker compose --profile observability up --build -d
```

Если нужно поднять только observability-стек без перезапуска бота:

```bash
docker compose --profile observability up -d loki alloy prometheus grafana
```

Полезные адреса:

- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`
- Loki API: `http://localhost:3100`
- Alloy UI/metrics: `http://localhost:12345`

Логин в Grafana берётся из `.env`:

- `GRAFANA_ADMIN_USER`
- `GRAFANA_ADMIN_PASSWORD`

Что уже настроено:

- datasource `Prometheus`;
- datasource `Loki`;
- дашборд `tg-logger-bot Observability`;
- сбор Docker-логов через `Alloy`, а не `Promtail`.

Для логов в Grafana открой `Explore`, выбери datasource `Loki` и используй, например, такие запросы:

```logql
{compose_service="bot"}
```

```logql
{compose_project="tg-logger-bot", compose_service="bot"} |= "message_reaction_logged"
```
