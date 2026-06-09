import argparse
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

DEFAULT_JSON_DIR = ROOT_DIR / "data" / "simulated"
STORE_NAMES = {
    "dicentre": "DiCENTRE",
    "techprom": "TechProm",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Смоделировать скидки и историю цен для демонстрационных графиков.")
    parser.add_argument(
        "stores",
        nargs="*",
        choices=sorted(STORE_NAMES),
        default=None,
        help="Магазины для моделирования. По умолчанию используются все товары из базы.",
    )
    parser.add_argument("--days", type=int, default=10, help="Сколько дней истории создать. По умолчанию 10.")
    parser.add_argument("--max-products", type=int, default=40, help="Сколько товаров изменить. По умолчанию 40.")
    parser.add_argument("--seed", type=int, default=42, help="Seed для повторяемой генерации. По умолчанию 42.")
    parser.add_argument(
        "--write-json",
        action="store_true",
        help="Дополнительно записать JSON-снимки в data/simulated/.",
    )
    parser.add_argument(
        "--json-dir",
        type=Path,
        default=DEFAULT_JSON_DIR,
        help="Папка для JSON-снимков при --write-json.",
    )
    args = parser.parse_args()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.pricecompare.settings")

    import django
    from django.core.management import call_command

    django.setup()
    call_command("migrate", interactive=False, verbosity=0)

    from app.shops.services import simulate_price_dynamics

    stores = [STORE_NAMES[store] for store in args.stores] if args.stores else None
    result = simulate_price_dynamics(
        stores=stores,
        days=args.days,
        max_products=args.max_products,
        seed=args.seed,
        json_dir=args.json_dir if args.write_json else None,
    )
    print(
        "Смоделировано: "
        f"товаров={result['products']}, "
        f"точек истории={result['history']}, "
        f"уведомлений о скидках={result['discounts']}, "
        f"json-файлов={result['json_files']}"
    )


if __name__ == "__main__":
    main()
