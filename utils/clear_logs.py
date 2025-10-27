"""
Утилита для очистки лог файлов
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta


def clear_logs(older_than_days: int = 7, dry_run: bool = False):
    """
    Очищает лог файлы старше указанного количества дней
    
    Args:
        older_than_days: Удалить файлы старше N дней (по умолчанию 7)
        dry_run: Если True, только показывает что будет удалено, не удаляет
    """
    logs_dir = Path(__file__).parent.parent / "logs"
    
    if not logs_dir.exists():
        print(f"[INFO] Папка логов {logs_dir} не существует")
        return
    
    cutoff_date = datetime.now() - timedelta(days=older_than_days)
    deleted_count = 0
    total_size = 0
    
    print(f"[CLEAR_LOGS] Очистка логов старше {older_than_days} дней (до {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')})")
    
    if dry_run:
        print("[DRY_RUN] Режим предварительного просмотра - файлы НЕ будут удалены")
    
    for log_file in logs_dir.glob("*.log"):
        try:
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            file_size = log_file.stat().st_size
            
            if file_mtime < cutoff_date:
                print(f"[DELETE] {log_file.name} ({file_size} байт, {file_mtime.strftime('%Y-%m-%d %H:%M:%S')})")
                
                if not dry_run:
                    log_file.unlink()
                
                deleted_count += 1
                total_size += file_size
            else:
                print(f"[KEEP] {log_file.name} ({file_size} байт, {file_mtime.strftime('%Y-%m-%d %H:%M:%S')})")
                
        except Exception as e:
            print(f"[ERROR] Ошибка при обработке файла {log_file.name}: {e}")
    
    if deleted_count > 0:
        if dry_run:
            print(f"[DRY_RUN_RESULT] Будет удалено: {deleted_count} файлов, {total_size} байт")
        else:
            print(f"[SUCCESS] Удалено: {deleted_count} файлов, освобождено {total_size} байт")
    else:
        print(f"[INFO] Нет файлов для удаления")


def clear_all_logs(dry_run: bool = False):
    """
    Удаляет все лог файлы
    
    Args:
        dry_run: Если True, только показывает что будет удалено, не удаляет
    """
    logs_dir = Path(__file__).parent.parent / "logs"
    
    if not logs_dir.exists():
        print(f"[INFO] Папка логов {logs_dir} не существует")
        return
    
    log_files = list(logs_dir.glob("*.log"))
    
    if not log_files:
        print("[INFO] Нет лог файлов для удаления")
        return
    
    total_size = sum(f.stat().st_size for f in log_files)
    
    print(f"[CLEAR_ALL_LOGS] Удаление всех {len(log_files)} лог файлов ({total_size} байт)")
    
    if dry_run:
        print("[DRY_RUN] Режим предварительного просмотра - файлы НЕ будут удалены")
        for log_file in log_files:
            file_size = log_file.stat().st_size
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            print(f"[DELETE] {log_file.name} ({file_size} байт, {file_mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        print(f"[DRY_RUN_RESULT] Будет удалено: {len(log_files)} файлов, {total_size} байт")
    else:
        deleted_count = 0
        for log_file in log_files:
            try:
                log_file.unlink()
                deleted_count += 1
            except Exception as e:
                print(f"[ERROR] Ошибка при удалении файла {log_file.name}: {e}")
        
        print(f"[SUCCESS] Удалено: {deleted_count} файлов, освобождено {total_size} байт")


def show_logs_info():
    """Показывает информацию о лог файлах"""
    logs_dir = Path(__file__).parent.parent / "logs"
    
    if not logs_dir.exists():
        print(f"[INFO] Папка логов {logs_dir} не существует")
        return
    
    log_files = list(logs_dir.glob("*.log"))
    
    if not log_files:
        print("[INFO] Нет лог файлов")
        return
    
    total_size = sum(f.stat().st_size for f in log_files)
    oldest_file = min(log_files, key=lambda f: f.stat().st_mtime)
    newest_file = max(log_files, key=lambda f: f.stat().st_mtime)
    
    print(f"[LOGS_INFO] Найдено {len(log_files)} лог файлов")
    print(f"[LOGS_INFO] Общий размер: {total_size} байт ({total_size / 1024:.1f} KB)")
    print(f"[LOGS_INFO] Самый старый: {oldest_file.name} ({datetime.fromtimestamp(oldest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')})")
    print(f"[LOGS_INFO] Самый новый: {newest_file.name} ({datetime.fromtimestamp(newest_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')})")
    
    print("\n[LOGS_LIST] Список файлов:")
    for log_file in sorted(log_files, key=lambda f: f.stat().st_mtime, reverse=True):
        file_size = log_file.stat().st_size
        file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        print(f"  {log_file.name} ({file_size} байт, {file_mtime.strftime('%Y-%m-%d %H:%M:%S')})")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "info":
            show_logs_info()
        elif command == "clear":
            days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            dry_run = "--dry-run" in sys.argv
            clear_logs(days, dry_run)
        elif command == "clear-all":
            dry_run = "--dry-run" in sys.argv
            clear_all_logs(dry_run)
        else:
            print("Использование:")
            print("  python clear_logs.py info                    - показать информацию о логах")
            print("  python clear_logs.py clear [дни] [--dry-run] - удалить логи старше N дней")
            print("  python clear_logs.py clear-all [--dry-run]   - удалить все логи")
            print("  python clear_logs.py                          - показать эту справку")
    else:
        print("Утилита для очистки лог файлов")
        print("\nКоманды:")
        print("  info                    - показать информацию о логах")
        print("  clear [дни] [--dry-run] - удалить логи старше N дней (по умолчанию 7)")
        print("  clear-all [--dry-run]   - удалить все логи")
        print("\nПримеры:")
        print("  python clear_logs.py info")
        print("  python clear_logs.py clear 3")
        print("  python clear_logs.py clear 7 --dry-run")
        print("  python clear_logs.py clear-all --dry-run")
        print("  python clear_logs.py clear-all")
