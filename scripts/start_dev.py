import argparse
import shutil
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.load_prices import SPIDERS, parse_prices, save_prices


def run(command: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, cwd=ROOT_DIR, check=check)


def ensure_redis() -> None:
    if not shutil.which("docker"):
        print("Docker не найден: пропускаю запуск Redis. Запустите Redis вручную, если нужен Celery.")
        return

    result = run(["docker", "start", "price-redis"], check=False)
    if result.returncode == 0:
        return

    run(["docker", "run", "-d", "--name", "price-redis", "-p", "6379:6379", "redis:7"])


def start_process(command: list[str]) -> subprocess.Popen:
    print("Запуск:", " ".join(command))
    return subprocess.Popen(command, cwd=ROOT_DIR)


def main() -> None:
    parser = argparse.ArgumentParser(description="Запустить dev-окружение проекта в одном терминале.")
    parser.add_argument(
        "--with-worker",
        action="store_true",
        help="Дополнительно запустить Celery worker. Для загрузки цен через scripts/load_prices.py он не нужен.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Хост Django runserver.")
    parser.add_argument("--port", default="8000", help="Порт Django runserver.")
    parser.add_argument(
        "--stores",
        nargs="+",
        choices=sorted(SPIDERS),
        default=None,
        help="Магазины для предварительного парсинга. По умолчанию все.",
    )
    parser.add_argument(
        "--parse-before-start",
        action="store_true",
        help="Перед запуском сайта спарсить выбранные магазины и сохранить цены в базу.",
    )
    parser.add_argument(
        "--parse-only",
        action="store_true",
        help="Только спарсить выбранные магазины и выйти без запуска Django.",
    )
    parser.add_argument(
        "--skip-parse",
        action="store_true",
        help="Для --parse-before-start/--parse-only не запускать Scrapy, а загрузить JSON из data/.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="Для --parse-before-start/--parse-only не считать пустой Scrapy-результат ошибкой.",
    )
    args = parser.parse_args()

    selected_stores = args.stores or sorted(SPIDERS)

    if args.with_worker:
        ensure_redis()

    run([sys.executable, "manage.py", "migrate"])

    if args.parse_before_start or args.parse_only:
        if not args.skip_parse:
            parse_prices(selected_stores)
        save_prices(selected_stores, allow_empty=args.allow_empty)
        if args.parse_only:
            return

    processes: list[subprocess.Popen] = []
    if args.with_worker:
        celery_command = [sys.executable, "-m", "celery", "-A", "app.core.celery_app", "worker", "-l", "info"]
        if sys.platform.startswith("win"):
            celery_command.extend(["-P", "solo"])
        processes.append(start_process(celery_command))

    processes.append(start_process([sys.executable, "manage.py", "runserver", f"{args.host}:{args.port}"]))

    try:
        processes[-1].wait()
    except KeyboardInterrupt:
        print("Останавливаю процессы...")
    finally:
        for process in processes:
            with suppress(ProcessLookupError):
                process.terminate()


if __name__ == "__main__":
    main()
