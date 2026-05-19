# Сервис сравнения цен товаров (Scrapy + Django + Celery)

Минимальный каркас сервиса сравнения цен с асинхронным парсингом двух магазинов:
- **ROZETKA**
- **Citrus**

## Что реализовано
- Django-модели для товаров, магазинов и истории цен.
- Celery-задача для периодического обновления цен и уведомлений о скидках.
- Scrapy-спайдеры для 2 магазинов.
- API endpoint для графика цен по товару.

## Архитектура
1. `Scrapy` собирает актуальные цены.
2. `Celery` запускает парсинг асинхронно и сохраняет историю цен.
3. `Django` хранит данные и отдает API.
4. При снижении цены формируется запись уведомления.

## Как запустить парсер (пошагово)

### 1) Установить зависимости
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Поднять Redis (брокер Celery)
Если Docker у вас не запущен (ошибка про `dockerDesktopLinuxEngine` на Windows), сначала откройте **Docker Desktop** и дождитесь статуса *Engine running*.

Проверка:
```bash
docker version
```

Если Docker недоступен, используйте один из вариантов ниже.

#### Вариант A: Docker (если установлен и запущен)
```bash
docker run -d --name price-redis -p 6379:6379 redis:7
```

Если видите ошибку:
`failed to fetch anonymous token ... https://auth.docker.io/token ... EOF`, это обычно сеть/прокси/DNS до Docker Hub.

Проверьте по шагам:
```bash
docker login
docker pull redis:7
```

Если `docker pull` не проходит:
- Проверьте VPN/прокси/фаервол (часто режет `auth.docker.io` и `registry-1.docker.io`).
- На Windows в Docker Desktop задайте proxy (Settings → Resources/Proxies).
- Попробуйте сменить DNS (например 8.8.8.8 / 1.1.1.1) и перезапустить Docker Desktop.

Альтернативы без Docker Hub:
- Используйте Redis через WSL (Вариант B ниже).
- Или локально установите Redis нативно в Windows (Вариант C ниже).

#### Вариант B: Redis без Docker (Windows через WSL)
```bash
wsl
sudo apt update
sudo apt install -y redis-server
sudo service redis-server start
redis-cli ping
```

#### Вариант C: Redis через Chocolatey (нативно в Windows)
```powershell
choco install redis-64 -y
redis-server
```

В ответ на `redis-cli ping` должно быть `PONG`.

### 3) Настроить Django-проект
В `settings.py` должны быть:
- `INSTALLED_APPS`: `app.shops`, `django_celery_results`
- `CELERY_BROKER_URL = "redis://localhost:6379/0"`
- `CELERY_RESULT_BACKEND = "django-db"`

После этого выполнить миграции:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4) Запустить Celery worker
```bash
celery -A app.core.celery_app worker -l info
```

### 5) Снять данные Scrapy-спайдером
Из корня репозитория:
```bash
scrapy runspider spiders/rozetka_spider.py -O data/rozetka.json
scrapy runspider spiders/citrus_spider.py -O data/citrus.json
```

### 6) Отправить данные в асинхронную задачу Celery
Пример через Django shell:
```bash
python manage.py shell
```
```python
import json
from app.shops.tasks import sync_rozetka, sync_citrus

with open("data/rozetka.json", "r", encoding="utf-8") as f:
    rozetka_items = json.load(f)

with open("data/citrus.json", "r", encoding="utf-8") as f:
    citrus_items = json.load(f)

sync_rozetka.delay(rozetka_items)
sync_citrus.delay(citrus_items)
```

### 7) Проверить API графика цен
После загрузки данных:
```bash
GET /api/products/<product_id>/chart/
```

## Быстрый smoke check
Если хотите проверить только парсинг без Django/Celery:
```bash
scrapy runspider spiders/rozetka_spider.py -o /tmp/rozetka.json
head -n 20 /tmp/rozetka.json
```
