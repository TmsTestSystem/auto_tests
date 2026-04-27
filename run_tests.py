#!/usr/bin/env python3
"""
Простой скрипт для запуска тестов с выбором хоста
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("Использование: python run_tests.py <хост> [аргументы pytest]")
        print("\nПримеры:")
        print("  python run_tests.py https://192.168.0.10/")
        print("  python run_tests.py st1 -v")
        print("  python run_tests.py local-a tests/ui/test_login.py")
        sys.exit(1)
    
    host_arg = sys.argv[1]
    pytest_args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Маппинг хостов на URL
    host_urls = {
        "st1": "https://decision-flow-frontend-st1.df-st.b-pl.cloud2",
        "st2": "https://decision-flow-frontend-st2.df-st.b-pl.cloud2", 
        "st3": "https://decision-flow-frontend-st3.df-st.b-pl.cloud2",
        "st4": "https://decision-flow-web-1.df-st4.cloud2.b-pl.pro",
        "local-a": "http://192.168.0.10:3333",
        "local-b": "http://localhost:3334", 
        "local-c": "http://localhost:3335",
        # HTTP-порт логинит, но не принимает session cookie на API (/api/projects -> 401).
        "local-192": "https://192.168.0.10/",
        "local-192-https": "https://192.168.0.10/"
    }
    
    # Определяем URL хоста
    if host_arg.startswith("http://") or host_arg.startswith("https://"):
        base_url = host_arg.rstrip("/")
        host_id = "custom"
    elif host_arg in host_urls:
        base_url = host_urls[host_arg]
        host_id = host_arg
    else:
        available_hosts = ", ".join(host_urls.keys())
        print(f"Ошибка: Неизвестный хост '{host_arg}'")
        print(f"Доступные хосты: {available_hosts}")
        print("Или используйте полный URL: https://192.168.0.10/")
        sys.exit(1)
    
    # Обновляем .env файл
    env_path = Path(__file__).parent / ".env"
    mailhog_url = None
    if env_path.exists():
        try:
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("MAILHOG_URL="):
                    mailhog_url = line.split("=", 1)[1]
                    break
        except OSError:
            pass
    if not mailhog_url and host_id in ("local-192", "local-192-https"):
        mailhog_url = "http://192.168.0.10:8025"

    env_content = f"""# Конфигурация хостов для тестирования
# Автоматически обновлено для хоста: {host_id}

BASE_URL={base_url}
LOGIN=admin@balance-pl.ru
PASSWORD=admin

DATABASE_URL=$env.DATABASE_URL
REPO_URL_FLOW=git@gitlab.infra.b-pl.pro:ilya.kurilin/qa_auto_test.git
"""
    if mailhog_url:
        env_content += f"MAILHOG_URL={mailhog_url}\n"
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print(f"[HOST] Выбран хост: {host_id}")
    print(f"[URL] BASE_URL установлен: {base_url}")
    print(f"[ARGS] Аргументы pytest: {pytest_args}")
    
    # Запускаем pytest
    host_option = []
    if host_id != "custom" and not any(arg.startswith("--test-host") for arg in pytest_args):
        host_option = [f"--test-host={host_id}"]
    cmd = ["python", "-m", "pytest"] + host_option + pytest_args
    print(f"[CMD] Выполняется: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n[INFO] Тестирование прервано пользователем")
        sys.exit(1)

if __name__ == "__main__":
    main()
