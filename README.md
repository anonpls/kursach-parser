# Сервис сравнения цен товаров (Scrapy + Django)

Минимальный каркас сервиса сравнения цен с парсингом российских магазинов:
- **DiCENTRE**
- **TechProm**

## Что реализовано
- Django-модели для товаров, магазинов, истории цен и уведомлений о скидках.
- Scrapy-спайдеры для 2 российских магазинов.
- Скрипт, который сам запускает парсинг и сохраняет данные в базу без ручного ввода Python-кода в `manage.py shell`.
- Dev-скрипт для запуска приложения одной командой с параметрами.
- Веб-интерфейс: каталог, поиск, фильтр по магазину, запуск парсинга, уведомления и графики цен.
- API endpoint для графика цен по товару.

## Архитектура
1. `Scrapy` собирает актуальные цены.
2. Скрипт `scripts/load_prices.py` сохраняет товары и историю цен в SQLite через Django-сервисы.
3. `Django` хранит данные и отдает API.
4. При снижении цены формируется запись уведомления.
5. `Celery` запускает асинхронный парсинг из интерфейса, но для обычного локального запуска можно использовать fallback-процесс или `scripts/load_prices.py`.

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

На главной странице можно посмотреть товары, найти товар, отфильтровать магазин, открыть страницу товара с графиком цены и запустить парсинг кнопкой.

Если вам нужен Celery worker для фонового парсинга из интерфейса, запустите тот же скрипт с флагом — тогда скрипт также попробует поднять Redis через Docker:
```bash
python scripts/start_dev.py --with-worker
```
На Windows worker будет запущен с `-P solo`, потому что стандартный `prefork` pool может падать при старте.
Если Redis/Celery недоступны, кнопка запуска парсинга в интерфейсе попробует запустить отдельный фоновый процесс `scripts/load_prices.py`.

### 3) Спарсить товары и сохранить их в базу
Разовая загрузка цен для всех магазинов:
```bash
python scripts/load_prices.py
```

Скрипт сам выполнит Scrapy для DiCENTRE и TechProm, применит миграции, запишет JSON в папку `data/` и сохранит товары в SQLite.
Вводить код вручную в `python manage.py shell` больше не нужно.
Если магазин вернул антибот-страницу, `401` или `403`, скрипт остановится с понятной ошибкой вместо тихого сохранения пустого списка.

Если JSON уже лежит в `data/` и нужно только повторно загрузить его в базу:
```bash
python scripts/load_prices.py --skip-parse
```

Можно загрузить только один магазин:
```bash
python scripts/load_prices.py dicentre
python scripts/load_prices.py techprom
```

### 4) Варианты запуска одной командой
Только применить миграции и запустить сайт:
```bash
python scripts/start_dev.py
```

Спарсить все магазины перед запуском сайта:
```bash
python scripts/start_dev.py --parse-before-start
```

Спарсить только один магазин и не запускать сайт:
```bash
python scripts/start_dev.py --parse-only --stores dicentre
```

Загрузить готовые JSON из `data/`, а потом запустить сайт:
```bash
python scripts/start_dev.py --parse-before-start --skip-parse
```

Запустить сайт и Celery worker для асинхронных задач:
```bash
python scripts/start_dev.py --with-worker
```

### 5) Проверить API графика цен
После загрузки данных откройте:
```text
http://127.0.0.1:8000/api/products/<product_id>/chart/
```

Например, если товар получил ID `1`:
```text
http://127.0.0.1:8000/api/products/1/chart/
```


## Загрузка дополнительных страниц каталога

Парсеры умеют переходить по пагинации/кнопке «загрузить ещё», которая видна в HTML-примерах из `tips/`. Количество страниц задаётся параметром `--max-pages`:

```bash
python scripts/load_prices.py --max-pages 3
python scripts/load_prices.py dicentre --max-pages 5
python scripts/load_prices.py techprom --max-pages 2
```

В интерфейсе тот же параметр находится в карточке запуска парсинга — поле «Страниц каталога».
По умолчанию загружается 1 страница, чтобы случайно не обходить сотни страниц каталога.

## Моделирование скидок для демонстрации графиков

Если реальные скидки долго не появляются, можно сгенерировать искусственную динамику цен по уже загруженным товарам:

```bash
python scripts/simulate_prices.py --days 10 --max-products 40 --write-json
```

Команда создаёт точки `PriceHistory`, уведомления о снижении цены и, при флаге `--write-json`, JSON-снимки в `data/simulated/`.
В веб-интерфейсе это доступно через блок «Смоделировать скидки и историю цен».

## Если `scripts/load_prices.py` пишет `No module named 'app'`
Обновите проект: скрипт добавляет корень репозитория в `sys.path` автоматически. После обновления запускайте его из корня проекта:
```bash
python scripts/load_prices.py dicentre
```

## Если магазин возвращает `401` или `403`
DiCENTRE и TechProm могут включать антибот-защиту. Скрипт отправляет браузерный `User-Agent`, но если сайт все равно блокирует запрос, попробуйте позже, другой магазин или уже сохраненный JSON через:
```bash
python scripts/load_prices.py --skip-parse
```

## Если Scrapy падает с `_setAcceptableProtocols`
На Windows при свежих транзитивных зависимостях может установиться несовместимая версия Twisted.
Переустановите зависимости после обновления `requirements.txt`:
```bash
pip install -r requirements.txt --upgrade
```

## Что есть в интерфейсе
- Карточки товаров с текущей ценой и ссылкой на магазин.
- Поиск по названию и фильтр по магазину.
- Кнопка асинхронного запуска парсинга выбранных магазинов.
- Блок уведомлений о скидках, которые создаются при снижении цены.
- Страница товара с графиком истории цены и списком изменений.

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
scrapy runspider spiders/dicentre_spider.py -O data/dicentre.json
scrapy runspider spiders/techprom_spider.py -O data/techprom.json
```
