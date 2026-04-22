## tg-logger-bot

Telegram-бот для логирования модерационных событий в основном чате, проверки доступа в служебные чаты администрации и управления сохранёнными текстами: кастомными командами, приветствием и заметками.

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
- поддерживает кастомные команды, приветствие и заметки в SQLite с нормализацией имени и кэшем;
- умеет подтверждать обновление уже существующих текстов через inline-кнопки `Принять` / `Отклонить`;
- умеет искать сохранённые тексты не только по точному совпадению, но и через локальный smart search по опечаткам и близким формам слов;
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

- `+команда <имя>` на первой строке и текст ответа со второй строки — создать кастомную команду, а при повторном имени предложить подтверждение обновления.
- `+приветствие` на первой строке и текст со второй строки — сохранить приветствие, которое вызывается сообщением `приветствие`.
- `+заметка <имя>` на первой строке и текст со второй строки — сохранить заметку, которая вызывается сообщением с точным названием заметки.
- `-команда <имя>` — удалить кастомную команду.
- `?команды` — показать список кастомных команд.

Точные текстовые триггеры:

- `приветствие` — отправить сохранённое приветствие;
- `<имя заметки>` — отправить заметку;
- `<имя кастомной команды>` — отправить кастомную команду.

Права доступа:

- создавать и менять приветствие, заметки и кастомные команды может только `owner_id`;
- читать приветствие и заметки могут `owner_id` и админы основного чата;
- обычные кастомные команды по-прежнему доступны всем.

Если приветствие, заметка или команда уже существуют, бот не перезаписывает их сразу. Вместо этого он показывает текущий и новый текст и ждёт подтверждения через кнопки `✅ Принять` / `🚫 Отклонить`.

Отдельной команды `+умная команда` нет. Вместо неё бот после промаха по точному триггеру запускает smart search по сохранённым текстам. Он учитывает опечатки, окончания и близкие словоформы, но не удаляет и не скрывает существующие дубли автоматически.

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
- при включенном tracing в логах сохраняется тот же `trace_id`, что и в OpenTelemetry trace, и дополнительно появляется `span_id`;
- при выключенном tracing `trace_id` остаётся локальным UUID fallback, как и раньше;
- Bot API transport теперь всегда идёт через один явно сконфигурированный `aiohttp` session layer, а не через разные code path при `TRACING__ENABLED=true/false`;
- для всех запросов к Telegram Bot API пишутся structured logs со статусом, длительностью и resolver mode, а для `getUpdates` дополнительно видны batch stats;
- добавлены отдельные Prometheus-метрики `tg_logger_telegram_api_requests_total`, `tg_logger_telegram_api_request_duration_seconds` и `tg_logger_polling_last_success_unixtime`;
- метрики Prometheus поднимаются встроенным HTTP server, по умолчанию на `0.0.0.0:9000`.

## Docker

Запуск через Compose:

```bash
docker compose up --build -d
```

Контейнер хранит SQLite в named volume `bot-data`, поэтому данные не теряются между пересозданиями контейнера.

## Локальные Адреса

Все основные локальные адреса собраны здесь, чтобы не искать их по README и `.env`.

- бот metrics endpoint при локальном запуске: `http://localhost:9000/metrics`
- Grafana: `http://localhost:3000`
- Jaeger UI: `http://localhost:16686`
- Prometheus: `http://localhost:9090`
- Loki API: `http://localhost:3100`
- Tempo API: `http://localhost:3200`
- Alloy UI/metrics: `http://localhost:12345`
- Alloy OTLP gRPC ingest: `http://localhost:4317`
- Alloy OTLP HTTP ingest: `http://localhost:4318`

## Grafana, Loki И Tempo

Для observability-стека добавлен отдельный Docker profile `observability`. В него входят:

- `Prometheus` — забирает метрики у бота, Loki и Alloy;
- `Loki` — хранит логи;
- `Tempo` — хранит traces;
- `Alloy` — собирает Docker stdout/stderr из контейнеров, отправляет их в Loki и принимает OTLP traces от бота для прокидывания в Tempo;
- `Grafana` — уже с provisioned datasource и двумя дашбордами: `tg-logger-bot Observability` и `tg-logger-bot Logs`;
- `tempo-query` — адаптирует Tempo под Jaeger Remote Storage API;
- `jaeger-query` — поднимает Jaeger UI поверх тех же traces, которые уже лежат в Tempo.

Запуск:

```bash
docker compose --profile observability up --build -d
```

Если нужно поднять только observability-стек без перезапуска бота:

```bash
docker compose --profile observability up -d prometheus loki tempo tempo-query alloy grafana jaeger-query
```

Полезные адреса:

- бот metrics endpoint при локальном запуске: `http://localhost:9000/metrics`
- Grafana: `http://localhost:3000`
- Jaeger UI: `http://localhost:16686`
- Prometheus: `http://localhost:9090`
- Loki API: `http://localhost:3100`
- Tempo API: `http://localhost:3200`
- Alloy UI/metrics: `http://localhost:12345`
- Alloy OTLP gRPC ingest: `http://localhost:4317`
- Alloy OTLP HTTP ingest: `http://localhost:4318`

Логин в Grafana берётся из `.env`:

- `GRAFANA_ADMIN_USER`
- `GRAFANA_ADMIN_PASSWORD`

Что уже настроено:

- datasource `Prometheus`;
- datasource `Loki`;
- datasource `Tempo`;
- дашборд `tg-logger-bot Observability`;
- дашборд `tg-logger-bot Logs` с переключателем `Service` по контейнерам стека;
- Jaeger UI как дополнительный read-only интерфейс к traces из Tempo;
- link из Loki log entry в соответствующий trace по полю `trace_id`;
- сбор Docker-логов через `Alloy`, а не `Promtail`.

`tg-logger-bot Logs` читает те же JSON-логи из Loki, но рендерит их в Grafana в человекочитаемом виде: время, `level`, `logger`, `message` и ключевой контекст (`step`, `handler`, `update_type`, `update_id`, `trace_id`, `span_id`). Там же есть отдельные панели со счётчиками и лентами для `ERROR`/`CRITICAL` и `WARNING`, а счётчики вынесены в фиксированные окна `24h`, `7d`, `30d` и `all time` (по всем сохранённым логам Loki).

### Tracing

Tracing по умолчанию выключен. Для включения задай в `.env`:

- `TRACING__ENABLED=true`
- `TRACING__SERVICE_NAME=tg-logger-bot`
- `TRACING__OTLP_ENDPOINT=http://localhost:4317` для локального запуска или оставь Docker override `http://alloy:4317` внутри Compose
- `TRACING__SAMPLING_RATIO=1.0`
- `TRACING__INSECURE=true`

Бот продолжает писать JSON-логи в stdout/Loki без изменения формата сообщения. Форматирование происходит уже в Grafana через LogQL, а traces отправляются по OTLP gRPC в `Alloy -> Tempo`.

После включения tracing в Grafana можно:

- открыть trace напрямую из log entry по `trace_id`;
- смотреть root span `telegram.update`, child spans `handler.*`, а также spans для SQLite и исходящих Telegram Bot API запросов.

Целевой backend для tracing в этом проекте — `Tempo`, не `Jaeger`.

### Telegram HTTP Transport

Для long polling и всех исходящих Bot API запросов используются отдельные настройки transport layer:

- `TELEGRAM_HTTP__RESOLVER=aiodns`
- `TELEGRAM_HTTP__DNS_CACHE_TTL_SECONDS=3600`
- `TELEGRAM_HTTP__SESSION_TIMEOUT_SECONDS=60.0`
- `TELEGRAM_HTTP__CONNECTION_LIMIT=100`

`aiodns` является дефолтным resolver mode для production-like запуска. Если на локальной Windows-машине `AsyncResolver` окажется проблемным, можно явно переключиться на `TELEGRAM_HTTP__RESOLVER=threaded`.

Если выбран `aiodns`, но библиотека недоступна или resolver не может инициализироваться, приложение падает на старте с явной ошибкой, а не молча уходит на другой transport path.

### Jaeger UI

Jaeger UI доступен по `http://localhost:${JAEGER_PORT:-16686}` и читает те же traces из Tempo через связку `jaeger-query -> tempo-query -> tempo`. Отдельного Jaeger storage backend в проект не добавляется.

Это дополнительный compatibility/convenience интерфейс для тех случаев, когда удобнее смотреть trace именно в Jaeger. Основным и поддерживаемым способом работы с traces остаются `Grafana + Tempo + Loki links`.

Важно: в этом проекте используется `Jaeger v1 query UI`, а ветка Jaeger v1 уже объявлена EOL. Поэтому UI зафиксирован на конкретной версии и не рассматривается как основной observability frontend.

Для `tempo-query` используется pinned known-good build, потому что текущая release-ветка `2.9.x` в этой связке корректно отдаёт список сервисов и операций, но падает на открытии самого trace через Jaeger UI.

Для логов в Grafana открой `Explore`, выбери datasource `Loki` и используй, например, такие запросы:

```logql
{compose_service="bot"}
```

```logql
{compose_project="tg-logger-bot", compose_service="bot"} |= "message_reaction_logged"
```
