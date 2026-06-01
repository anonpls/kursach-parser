# Сервис сравнения цен товаров (Scrapy + Django)

Минимальный каркас сервиса сравнения цен с парсингом российских магазинов:
- **DNS**
- **Ситилинк**

## Что реализовано
- Django-модели для товаров, магазинов и истории цен.
- Scrapy-спайдеры для 2 российских магазинов.
- Скрипт, который сам запускает парсинг и сохраняет данные в базу без ручного ввода Python-кода в `manage.py shell`.
- Dev-скрипт для запуска приложения из одного терминала.
- API endpoint для графика цен по товару.

## Архитектура
1. `Scrapy` собирает актуальные цены.
2. Скрипт `scripts/load_prices.py` сохраняет товары и историю цен в SQLite через Django-сервисы.
3. `Django` хранит данные и отдает API.
4. При снижении цены формируется запись уведомления.
5. `Celery` оставлен в проекте для асинхронных задач, но для обычного локального запуска он не обязателен.

## Быстрый запуск без четырех терминалов

### 1) Установить зависимости
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

На Windows в `cmd` активация такая:
```cmd
.venv\Scripts\activate
```

### 2) Запустить сайт
Одна команда применит миграции и запустит Django:
```bash
python scripts/start_dev.py
```

После запуска сайт будет доступен на:
```text
http://127.0.0.1:8000/
```

Если вам все-таки нужен Celery worker, запустите тот же скрипт с флагом — тогда скрипт также попробует поднять Redis через Docker:
```bash
python scripts/start_dev.py --with-worker
```
На Windows worker будет запущен с `-P solo`, потому что стандартный `prefork` pool может падать при старте.

### 3) Спарсить товары и сохранить их в базу
Откройте второй терминал только для разовой загрузки цен и выполните:
```bash
python scripts/load_prices.py
```

Скрипт сам выполнит Scrapy для DNS и Ситилинка, запишет JSON в папку `data/` и сохранит товары в SQLite.
Вводить код вручную в `python manage.py shell` больше не нужно.

Если JSON уже лежит в `data/` и нужно только повторно загрузить его в базу:
```bash
python scripts/load_prices.py --skip-parse
```

Можно загрузить только один магазин:
```bash
python scripts/load_prices.py dns
python scripts/load_prices.py citilink
```

### 4) Проверить API графика цен
После загрузки данных откройте:
```text
http://127.0.0.1:8000/api/products/<product_id>/chart/
```

Например, если товар получил ID `1`:
```text
http://127.0.0.1:8000/api/products/1/chart/
```

## Если Scrapy падает с `_setAcceptableProtocols`
На Windows при свежих транзитивных зависимостях может установиться несовместимая версия Twisted.
Переустановите зависимости после обновления `requirements.txt`:
```bash
pip install -r requirements.txt --upgrade
```

## Ручной запуск компонентов, если нужен

### Redis через Docker
```bash
docker start price-redis
```
Если контейнера еще нет:
```bash
docker run -d --name price-redis -p 6379:6379 redis:7
```

### Django
```bash
python manage.py migrate
python manage.py runserver
```

### Celery worker
Linux/macOS:
```bash
celery -A app.core.celery_app worker -l info
```

Windows:
```bash
celery -A app.core.celery_app worker -l info -P solo
```

### Scrapy без сохранения в базу
```bash
scrapy runspider spiders/dns_spider.py -O data/dns.json
scrapy runspider spiders/citilink_spider.py -O data/citilink.json
```
