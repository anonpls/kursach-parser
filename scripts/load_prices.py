import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

DATA_DIR = ROOT_DIR / "data"
SPIDERS = {
    "dns": {
        "path": ROOT_DIR / "spiders" / "dns_spider.py",
        "output": DATA_DIR / "dns.json",
        "store_name": "DNS",
        "base_url": "https://www.dns-shop.ru/",
    },
    "citilink": {
        "path": ROOT_DIR / "spiders" / "citilink_spider.py",
        "output": DATA_DIR / "citilink.json",
        "store_name": "Ситилинк",
        "base_url": "https://www.citilink.ru/",
    },
}


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT_DIR, check=True)


def parse_prices(stores: list[str]) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    for store in stores:
        config = SPIDERS[store]
        run([
            sys.executable,
            "-m",
            "scrapy",
            "runspider",
            str(config["path"]),
            "-O",
            str(config["output"]),
        ])


def save_prices(stores: list[str], allow_empty: bool = False) -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.pricecompare.settings")

    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False, verbosity=0)

    from app.shops.services import upsert_products

    for store in stores:
        config = SPIDERS[store]
        with config["output"].open("r", encoding="utf-8") as file:
            items = json.load(file)
        if not items and not allow_empty:
            raise RuntimeError(
                f"{config['store_name']}: Scrapy не собрал ни одного товара. "
                "Чаще всего сайт вернул антибот/401/403 или изменилась верстка. "
                "Подробности смотрите выше в логе Scrapy."
            )
        updated = upsert_products(config["store_name"], config["base_url"], items)
        print(f"{config['store_name']}: сохранено или обновлено товаров: {updated}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Спарсить цены и сразу сохранить их в Django DB.")
    parser.add_argument(
        "stores",
        nargs="*",
        choices=sorted(SPIDERS),
        default=sorted(SPIDERS),
        help="Магазины для парсинга. По умолчанию запускаются все.",
    )
    parser.add_argument(
        "--skip-parse",
        action="store_true",
        help="Не запускать Scrapy, а загрузить уже готовые JSON-файлы из папки data.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Не считать ошибкой пустой результат парсинга.",
    )
    args = parser.parse_args()

    if not args.skip_parse:
        parse_prices(args.stores)
    save_prices(args.stores, allow_empty=args.allow_empty)


if __name__ == "__main__":
    main()
