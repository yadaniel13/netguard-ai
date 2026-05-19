# NetGuard AI — Система интеллектуальной фильтрации сетевого трафика

Дипломная работа по направлению **«Программная инженерия»**  
Тема: *Разработка системы интеллектуальной фильтрации сетевого трафика на основе методов машинного обучения*

---

## Описание

Веб-приложение для анализа и классификации сетевого трафика с использованием трёх алгоритмов машинного обучения:
- **Logistic Regression** — базовая линейная модель
- **Random Forest** — ансамблевый метод (100 деревьев)
- **XGBoost** — градиентный бустинг

Распознаёт типы трафика:
| Тип | Описание |
|-----|----------|
| Normal Traffic | Легитимный трафик |
| DDoS/DoS Attack | Атаки отказа в обслуживании |
| Port Scan | Сканирование портов |
| Brute Force | Перебор учётных данных (FTP, SSH) |
| Botnet | Ботнет-активность |
| Web Attack | Веб-атаки (XSS, SQL Injection, Brute Force) |

---

## Стек технологий

| Компонент | Технологии |
|-----------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| ML | scikit-learn, XGBoost, pandas, numpy, joblib |
| Frontend | Bootstrap 5, Jinja2, JavaScript |
| Визуализация | matplotlib, seaborn |
| База данных | SQLite |
| DevOps | Docker, docker-compose |

---

## Быстрый старт

### Вариант 1: Docker (рекомендуется)

```bash
# Клонировать или перейти в папку проекта
cd diploma

# Запустить одной командой
docker-compose up --build
```

Открыть в браузере: **http://localhost:8000**

---

### Вариант 2: Локальный запуск

```bash
# 1. Создать виртуальное окружение
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Запустить приложение
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Структура проекта

```
diploma/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   └── config.py            # Конфигурация
├── api/
│   └── routes/
│       ├── pages.py         # HTML страницы
│       ├── upload.py        # Загрузка файлов
│       ├── analysis.py      # Запуск анализа
│       ├── statistics.py    # Статистика
│       └── reports.py       # Экспорт отчётов
├── ml/
│   ├── preprocessor.py      # Предобработка данных
│   ├── trainer.py           # Обучение моделей
│   ├── evaluator.py         # Оценка качества
│   └── predictor.py         # Инференс
├── services/
│   ├── analysis_service.py  # Оркестрация анализа
│   ├── file_service.py      # Работа с файлами
│   └── report_service.py    # Генерация отчётов
├── database/
│   ├── models.py            # ORM модели
│   ├── crud.py              # CRUD операции
│   └── database.py          # Подключение к БД
├── visualization/
│   └── charts.py            # Генерация графиков
├── templates/               # Jinja2 HTML шаблоны
├── static/                  # CSS, JS, изображения
├── scripts/
│   ├── generate_sample_data.py  # Генератор датасета
│   └── train_models.py          # Обучение моделей
├── tests/                   # Тесты
├── datasets/                # Датасеты
├── models/                  # Сохранённые модели
├── uploads/                 # Загруженные файлы
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## API Документация

После запуска: **http://localhost:8000/docs**

### Основные эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| `GET` | `/` | Дашборд |
| `GET` | `/upload` | Страница загрузки |
| `GET` | `/history` | История анализов |
| `GET` | `/analysis/{id}` | Результаты анализа |
| `GET` | `/models` | Сравнение моделей |
| `POST` | `/api/upload` | Загрузить CSV файл |
| `POST` | `/api/analyze/{file_id}` | Запустить анализ |
| `GET` | `/api/analysis/{id}` | Получить результаты (JSON) |
| `GET` | `/api/statistics` | Сводная статистика |
| `GET` | `/api/report/{id}/csv` | Скачать отчёт CSV |
| `GET` | `/api/report/{id}/json` | Скачать отчёт JSON |

---

## Датасет

Система поддерживает формат **CIC-IDS2017**.  
При первом запуске автоматически генерируется демонстрационный датасет из 5 000 записей.

Для использования реального датасета:
1. Скачать CIC-IDS2017 с https://www.unb.ca/cic/datasets/ids-2017.html
2. Загрузить CSV через интерфейс приложения

---

## Тестирование

```bash
# Запустить все тесты
pytest tests/ -v

# С покрытием
pytest tests/ --cov=. --cov-report=html
```

---

## Схема базы данных

```sql
uploaded_files      -- Метаданные загруженных файлов
analysis_results    -- Результаты анализа
ml_metrics          -- Метрики моделей МО
attack_statistics   -- Статистика по типам атак
```

---

## Скриншоты

- **Дашборд**: сводная статистика, последние анализы
- **Загрузка**: drag & drop форма загрузки CSV
- **Результаты**: графики распределения, матрица ошибок, ROC-кривые, таблицы метрик
- **История**: список всех анализов с поиском
- **Модели**: сравнение алгоритмов МО

---

## Автор

Дипломная работа, 2024  
Направление: Программная инженерия
