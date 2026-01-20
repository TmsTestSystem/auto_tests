"""
Быстрая очистка отчётов и логов по нагрузочному тестированию проекта.

Что удаляет (и при необходимости заново создаёт как пустые директории):
- load_testing/locust_logs/
- load_testing/reports/
- load_testing/load/locust_logs/
- load_testing/load/reports/
- load_testing/component_load/reports/
- locust_logs/ (в корне)
- logs/ (в корне)
- все подпапки в reports/ (если такая директория есть)

Запуск (из корня репозитория):
    python -m utils.cleanup_reports
или:
    python utils/cleanup_reports.py
"""

from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _safe_rmtree(path: Path) -> None:
    """
    Удаляет директорию, если она существует.
    Ошибки игнорируются, чтобы скрипт был "безопасным" при повторных запусках.
    """
    if path.exists():
        try:
            shutil.rmtree(path)
            print(f"[CLEAN] Removed: {path}")
        except Exception as exc:
            print(f"[CLEAN][WARN] Failed to remove {path}: {exc}")


def _recreate_dir(path: Path) -> None:
    """
    Создаёт директорию (и родителей), если их нет.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        print(f"[CLEAN] Ensured dir: {path}")
    except Exception as exc:
        print(f"[CLEAN][WARN] Failed to create dir {path}: {exc}")


def clean_load_reports() -> None:
    """
    Основная функция очистки отчётов/логов.
    """
    # Директории, которые просто удаляем и создаём заново пустыми
    dirs_to_reset = [
        ROOT / "load_testing" / "locust_logs",
        ROOT / "load_testing" / "reports",
        ROOT / "load_testing" / "load" / "locust_logs",
        ROOT / "load_testing" / "load" / "reports",
        ROOT / "load_testing" / "component_load" / "reports",
        ROOT / "locust_logs",
        ROOT / "logs",
    ]

    for d in dirs_to_reset:
        _safe_rmtree(d)
        _recreate_dir(d)

    # Дополнительно: чистим все подпапки в корневой директории reports/
    root_reports = ROOT / "reports"
    if root_reports.exists() and root_reports.is_dir():
        for child in root_reports.iterdir():
            if child.is_dir():
                _safe_rmtree(child)
        print(f"[CLEAN] All subdirectories in {root_reports} removed (root dir left in place)")


def main() -> None:
    print(f"[CLEAN] Project root: {ROOT}")
    clean_load_reports()
    print("[CLEAN] Done.")


if __name__ == "__main__":
    main()

