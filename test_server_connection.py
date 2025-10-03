#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к fake HTTP серверу
Помогает диагностировать проблемы с доступностью сервера в Docker
"""
import requests
import socket
import time
import sys

def test_server_connection(host="localhost", port=8888):
    """Тестирует подключение к серверу"""
    print(f"Testing connection to {host}:{port}")
    
    # 1. Проверяем, свободен ли порт
    print(f"1. Checking if port {port} is free...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   [ERROR] Port {port} is already in use")
            return False
        else:
            print(f"   [OK] Port {port} is free")
    except Exception as e:
        print(f"   [ERROR] Error checking port: {e}")
        return False
    
    # 2. Запускаем сервер
    print(f"2. Starting fake server on {host}:{port}...")
    try:
        from fake_http_server import create_fake_server
        server = create_fake_server(host, port)
        
        if server.start():
            print(f"   [OK] Server started successfully")
            time.sleep(1)  # Ждем запуска
        else:
            print(f"   [ERROR] Failed to start server")
            return False
    except Exception as e:
        print(f"   [ERROR] Error starting server: {e}")
        return False
    
    # 3. Тестируем HTTP запросы
    print(f"3. Testing HTTP requests...")
    test_urls = [
        f"http://localhost:{port}/users",
        f"http://127.0.0.1:{port}/users",
        f"http://{host}:{port}/users"
    ]
    
    success = False
    for url in test_urls:
        try:
            print(f"   Testing: {url}")
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"   [OK] Success! Status: {response.status_code}")
                print(f"   Response: {response.json()[:100]}...")
                success = True
                break
            else:
                print(f"   [ERROR] Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   [ERROR] Error: {e}")
    
    # 4. Останавливаем сервер
    print(f"4. Stopping server...")
    try:
        server.stop()
        print(f"   [OK] Server stopped")
    except Exception as e:
        print(f"   [ERROR] Error stopping server: {e}")
    
    return success

def main():
    """Основная функция"""
    print("=== Fake HTTP Server Connection Test ===")
    
    # Тестируем разные конфигурации
    configs = [
        ("localhost", 8888),
        ("127.0.0.1", 8888),
        ("0.0.0.0", 8888),
        ("localhost", 8889),
        ("127.0.0.1", 8889),
        ("0.0.0.0", 8889),
    ]
    
    for host, port in configs:
        print(f"\n--- Testing {host}:{port} ---")
        if test_server_connection(host, port):
            print(f"[SUCCESS] Server works on {host}:{port}")
            sys.exit(0)
        else:
            print(f"[FAILED] Server doesn't work on {host}:{port}")
    
    print(f"\n[ERROR] All configurations failed!")
    sys.exit(1)

if __name__ == "__main__":
    main()
