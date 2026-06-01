import argparse
import shutil
import subprocess
import sys
from contextlib import suppress
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


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
    args = parser.parse_args()

    if args.with_worker:
        ensure_redis()

    run([sys.executable, "manage.py", "migrate"])

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
