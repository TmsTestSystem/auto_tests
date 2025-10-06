# 🧪 Auto Test 2.0

Простая система автоматизированного тестирования с выбором хоста.

## 🚀 Быстрый запуск

```bash
# Запуск тестов на вашем хосте
python run_tests.py http://192.168.0.7:3333/ -v

# Запуск тестов на хосте st1
python run_tests.py st1 -v

# Запуск тестов на локальном хосте
python run_tests.py local-a -v

# Запуск конкретного теста
python run_tests.py st1 tests/ui/test_login.py -v
```

## 🎯 Доступные хосты

| Хост | Описание | URL |
|------|----------|-----|
| `st1` | Stage 1 | https://decision-flow-web-1.df-st1.cloud.b-pl.pro |
| `st2` | Stage 2 | https://decision-flow-web-1.df-st2.cloud2.b-pl.pro |
| `st3` | Stage 3 | https://decision-flow-frontend-st3.df-st.b-pl.cloud2 |
| `st4` | Stage 4 | https://decision-flow-web-1.df-st4.cloud2.b-pl.pro |
| `local-a` | Local A | http://localhost:3333 |
| `local-b` | Local B | http://localhost:3334 |
| `local-c` | Local C | http://localhost:3335 |
| `local-192` | Local 192 | http://192.168.0.7:3333 |

## 📁 Структура проекта

```
auto-test2_0/
├── pytest_host.py          # Плагин для выбора хоста
├── .env                     # Конфигурация хостов
├── tests/                   # Тесты
│   ├── api/                # API тесты
│   └── ui/                 # UI тесты
├── pages/                  # Page Object Model
└── utils/                  # Утилиты
```

## 🛠️ Установка и настройка

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Настройка хоста

Отредактируйте файл `.env` и раскомментируйте нужный `BASE_URL`:

```env
# Выберите хост, раскомментировав одну строку:
BASE_URL=https://decision-flow-web-1.df-st1.cloud.b-pl.pro  # ST1
# BASE_URL=http://localhost:3333  # Local A
```

### 3. Запуск тестов

```bash
# Все UI тесты
python run_tests.py st1 tests/ui/ -v

# Конкретный тест
python run_tests.py local-a tests/ui/test_login.py

# Smoke тесты
python run_tests.py st2 -m smoke -v
```

## 📋 Типы тестов

### UI тесты
- `test_login.py` - Авторизация
- `test_project_buttons.py` - Интерфейс проектов
- `test_data_struct.py` - Структуры данных
- `test_flow_*.py` - Flow компоненты
- `test_http_flow.py` - HTTP операции

### API тесты
- `test_api.py` - API endpoints

## 🔧 Конфигурация

### pytest.ini
```ini
[pytest]
addopts = -q --ignore=tests/ui/test_flow_backup.py -p pytest_host
markers =
    smoke: быстрые смоук-тесты
```

### .env файл
```env
BASE_URL=https://decision-flow-web-1.df-st1.cloud.b-pl.pro
LOGIN=admin@balance-pl.ru
PASSWORD=admin
```

## 📝 Примеры команд

```bash
# Быстрая проверка
python run_tests.py st1 -x --tb=short

# Подробный вывод
python run_tests.py local-a -v -s --tb=long

# Параллельный запуск
python run_tests.py st2 -n 4 -v

# Только сбор тестов
python run_tests.py st1 --collect-only
```

## 🚨 Устранение проблем

### Ошибка подключения
```bash
# Проверьте доступность хоста
ping decision-flow-web-1.df-st1.cloud.b-pl.pro

# Проверьте .env файл
cat .env
```

### Неправильный хост
```bash
# Убедитесь, что хост указан правильно
python run_tests.py st1 --collect-only
```

---

*Версия: 2.0 - Упрощенная*  
*Последнее обновление: $(date)*