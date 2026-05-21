# SiteGuard

Автоматическая проверка сайтов на юридико-технические риски.

## Стек

- **Frontend**: Next.js 14 / App Router / TypeScript / Tailwind CSS
- **Backend**: FastAPI + SQLAlchemy + Alembic
- **DB**: PostgreSQL 16
- **Queue**: Redis + RQ
- **Scanner**: httpx + BeautifulSoup + Playwright
- **PDF**: Playwright
- **Deploy**: Docker Compose

## Быстрый старт

### 1. Клонировать и настроить окружение

```bash
cp .env.example .env
# Отредактируйте .env при необходимости
```

### 2. Запустить все сервисы

```bash
docker compose up --build
```

Сервисы будут доступны:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### 3. Применить миграции БД

После первого запуска (когда postgres уже поднялся):

```bash
docker compose exec backend alembic upgrade head
```

Или запустить отдельно:

```bash
docker compose run --rm backend alembic upgrade head
```

### 4. Проверить работу

```bash
# Health check
curl http://localhost:8000/api/health

# Запустить сканирование
curl -X POST http://localhost:8000/api/scans \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# Получить результат (подставьте scan_id из ответа выше)
curl http://localhost:8000/api/scans/{scan_id}

# Скачать PDF
curl -o report.pdf http://localhost:8000/api/scans/{scan_id}/pdf
```

## Структура проекта

```
root/
├── frontend/                  # Next.js приложение
│   ├── src/
│   │   ├── app/               # App Router страницы
│   │   │   ├── page.tsx       # Главная
│   │   │   ├── scan/[id]/     # Страница результатов
│   │   │   ├── pricing/       # Тарифы
│   │   │   ├── privacy/       # Политика конфиденциальности
│   │   │   ├── offer/         # Публичная оферта
│   │   │   └── about/         # О сервисе
│   │   ├── components/
│   │   │   ├── ui/            # Базовые компоненты
│   │   │   └── sections/      # Секции главной страницы
│   │   ├── lib/               # API клиент
│   │   └── types/             # TypeScript типы
│   └── Dockerfile
│
├── backend/                   # FastAPI приложение
│   ├── app/
│   │   ├── api/               # Роуты (scans, health)
│   │   ├── core/              # Конфиг, утилиты URL
│   │   ├── db/                # SQLAlchemy сессия
│   │   ├── models/            # ORM модели
│   │   ├── schemas/           # Pydantic схемы
│   │   ├── scanner/           # Логика сканирования
│   │   ├── workers/           # RQ worker
│   │   ├── pdf/               # Генерация PDF
│   │   └── main.py            # FastAPI app
│   ├── alembic/               # Миграции БД
│   ├── Dockerfile
│   ├── Dockerfile.worker
│   └── requirements.txt
│
├── docker-compose.yml
├── .env.example
└── README.md
```

## Запуск worker отдельно (для разработки)

```bash
# Установить зависимости
cd backend
pip install -r requirements.txt
playwright install chromium

# Запустить worker
python -m app.workers.main
```

## Переменные окружения

| Переменная | Описание | По умолчанию |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://siteguard:...` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `SECRET_KEY` | Секретный ключ приложения | — |
| `ALLOWED_ORIGINS` | CORS origins (через запятую) | `http://localhost:3000` |
| `RATE_LIMIT_PER_MINUTE` | Лимит запросов с одного IP | `10` |
| `SCANNER_MAX_PAGES` | Макс. страниц для сканирования | `10` |
| `SCANNER_TIMEOUT` | Таймаут запроса (сек) | `15` |
| `NEXT_PUBLIC_API_URL` | URL backend для frontend | `http://localhost:8000` |

## API

### POST /api/scans
Создать новое сканирование.

```json
// Request
{ "url": "https://example.com" }

// Response
{ "scan_id": "uuid", "status": "queued" }
```

### GET /api/scans/{scan_id}
Получить статус и результаты сканирования.

```json
{
  "id": "uuid",
  "url": "https://example.com",
  "status": "completed",
  "progress": 100,
  "score": 75,
  "risk_level": "yellow",
  "checks": [...],
  "issues": [...],
  "created_at": "...",
  "finished_at": "..."
}
```

### GET /api/scans/{scan_id}/pdf
Скачать PDF-отчёт (только для завершённых сканирований).

### GET /api/health
Проверка работоспособности сервиса.

## Проверки

| Код | Название | Законодательство |
|---|---|---|
| `https` | HTTPS | — |
| `privacy_policy` | Политика конфиденциальности | ФЗ-152 |
| `form_consent` | Согласие в формах | ФЗ-152, ст. 9 |
| `cookie_banner` | Cookie-баннер | — |
| `advertising_marking` | Маркировка рекламы ERID | ФЗ-347 |
| `company_requisites` | Реквизиты компании | ЗоЗПП |
| `consumer_rights` | Права потребителей | ЗоЗПП |
| `meta_title` | Тег title | — |
| `meta_description` | Meta description | — |
| `robots_txt` | robots.txt | — |
| `sitemap_xml` | sitemap.xml | — |

## Скоринг

- Начальный балл: **100**
- Нарушение высокого риска: **−25**
- Нарушение среднего риска: **−12**
- Нарушение низкого риска: **−5**
- Минимальный балл: **0**

Уровни риска:
- 🟢 **Зелёный**: 80–100
- 🟡 **Жёлтый**: 50–79
- 🔴 **Красный**: 0–49

## Ограничение запросов

Rate limiting реализован через `slowapi` на уровне FastAPI.
По умолчанию: 10 запросов в минуту с одного IP на endpoint `POST /api/scans`.
Настраивается через переменную `RATE_LIMIT_PER_MINUTE`.

## Дисклеймер

Все отчёты SiteGuard носят исключительно информационный характер и основаны на автоматическом
анализе открытых данных сайта. Отчёты не являются юридическим заключением.
