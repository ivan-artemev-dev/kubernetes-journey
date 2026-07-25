# GDELT Analytics Dashboard

Веб-дашборд для аналитики новостных публикаций GDELT GKG, хранящихся в Elasticsearch.

## Требования

- Python 3.11+
- Node.js 20+
- Доступный Elasticsearch с индексом `gdelt_gkg`

Репозиторий не содержит виртуального окружения и зависимостей (`venv/`, `node_modules/`) —
их нужно установить один раз после копирования проекта на машину.

## Установка и запуск с нуля

### 1. Бэкенд
```bash
cd backend
python -m venv venv

# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
# Windows (cmd)
venv\Scripts\activate.bat
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
python main.py
```
При первом запуске автоматически создастся `references.db` (справочники тем/GCAM/стран).
API поднимется на `http://localhost:8000` (адрес и порт берутся из `backend/.env`).

### 2. Фронтенд
Открыть новый терминал:
```bash
cd frontend
npm install
npm run dev
```
Приложение будет доступно на `http://localhost:5173` (порт берётся из `frontend/.env`).

## Конфигурация через .env

**`backend/.env`** (создать на основе `backend/.env.example`, если файла нет):
```
ELASTIC_URL=http://localhost:9200   # адрес Elasticsearch
ELASTIC_INDEX=gdelt_gkg             # имя индекса
BACKEND_HOST=0.0.0.0                # на каком адресе слушает API
BACKEND_PORT=8000                   # порт бэкенда
```

**`frontend/.env`** (создать на основе `frontend/.env.example`, если файла нет):
```
FRONTEND_PORT=5173   # порт dev-сервера фронтенда
BACKEND_PORT=8000    # порт бэкенда - фронтенд проксирует /api на него
```

Если меняете `BACKEND_PORT`, укажите одно и то же значение в обоих `.env`-файлах
(в `backend/.env` — на каком порту стартует API, в `frontend/.env` — куда фронтенд
проксирует запросы `/api`).

Важно: бэкенд нужно запускать командой `python main.py` (а не `uvicorn main:app --port ...`),
иначе порт и хост из `.env` не применятся.

## Особенности маппинга индекса

Реальный маппинг `gdelt_gkg` отличается от идеализированной схемы, из-за чего часть эндпоинтов
работает не как обычные ES-агрегации:

- **`gcam`** замаплен как `object` с `enabled: false` — не индексируется. `/api/gcam/summary`
  читает значения через `runtime_mappings`-скрипт по `_source`, поэтому без явного периода
  запрос по умолчанию сужается до последних 24 часов (иначе — полный скан индекса и таймаут).
- **`url`** замаплен как `keyword` с `index: false` — обычный поиск по нему невозможен.
  `/api/search?type=url` использует runtime-поле (нижний регистр `_source.url`) и wildcard-запрос
  по нему; по той же причине без явного периода поиск ограничен последними 24 часами.
- **`persons` / `organizations` / `source_name`** — `keyword` без анализатора, поэтому частичный
  регистронезависимый поиск (`type=person|org|source`) реализован через `wildcard`-запрос
  (`*значение*`), а не `match`.
- **`date`** — настоящий индексированный `date` (не строка), поэтому агрегации по дням
  (`/api/entity/*`, `/api/historical`) используют нативный `date_histogram`.

## Структура

```
backend/
  main.py          # FastAPI-приложение, эндпоинты
  elastic.py        # запросы и агрегации к Elasticsearch
  references.py      # справочники (темы GDELT, GCAM, страны) в SQLite
  references.db       # строится автоматически при первом запуске
frontend/
  src/pages/          # Feed, Search, Entity, Trends, GCAM, Map, Historical
  src/components/      # ToneBar, ThemeTag, EntityCard, FeedItem
```
