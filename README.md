# 🧪 Auto Test 2.0 - API Testing Suite

Комплексная система автоматизированного тестирования с поддержкой UI и API тестов, включая полное логирование и управление проектами.

## 🚀 Быстрый запуск

### API тесты
```bash
# Все API тесты
python -m pytest tests/api/ -v -s --test-host=local-192

# Конкретный API тест
python -m pytest tests/api/test_file_panel.py -v -s --test-host=local-192

# Туториал end-to-end
python -m pytest tests/api/test_tutorial.py::TestTutorialAPI::test_tutorial_end_to_end -v -s --test-host=local-192
```

### UI тесты
```bash
# Все UI тесты
python run_tests.py local-192 tests/ui/ -v

# Конкретный UI тест
python run_tests.py local-192 tests/ui/test_login.py -v
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
├── tests/                    # Тесты
│   ├── api/                 # API тесты
│   │   ├── test_api.py      # Полный цикл проекта
│   │   ├── test_file_panel.py # Файловая панель
│   │   └── test_tutorial.py # End-to-end туториал
│   └── ui/                  # UI тесты
├── api/                     # API клиенты
│   ├── file_panel_api.py    # Файловая панель API
│   └── project_process_log.py # Процессы и логи
├── pages/                   # Page Object Model
├── utils/                   # Утилиты
│   ├── custom_logger.py     # Кастомный логгер
│   ├── clear_logs.py        # Очистка логов
│   └── clear_projects.py    # Очистка проектов
├── logs/                    # Лог файлы (игнорируется Git)
├── conftest.py             # Pytest конфигурация
└── pytest.ini             # Настройки pytest
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
BASE_URL=http://192.168.0.7:3333  # Local 192
# BASE_URL=https://decision-flow-web-1.df-st1.cloud.b-pl.pro  # ST1
LOGIN=admin@balance-pl.ru
PASSWORD=admin
```

### 3. Запуск тестов

```bash
# Все API тесты
python -m pytest tests/api/ -v -s --test-host=local-192

# Все UI тесты
python run_tests.py local-192 tests/ui/ -v

# Конкретный тест
python -m pytest tests/api/test_file_panel.py::TestFilePanelCreation::test_create_folder -v -s --test-host=local-192
```

## 📋 Типы тестов

### 🔌 API тесты

#### `test_api.py` - Управление проектами
- **Полный цикл проекта**: создание → открытие → изменение → fetch → удаление
- **Проверка доступности**: ensure_exist, проверка в списке проектов
- **Обновление проекта**: изменение title, description
- **Git операции**: fetch с prune

#### `test_file_panel.py` - Файловая панель (12 тестов)
- **Создание файлов**: обычные, процессы (.df.json), структуры данных (.ds.json)
- **Создание файлов БД**: подключения (.db.json), таблицы решений (.dt.json)
- **Создание скриптов**: Python (.py), тесты (.test.json)
- **Операции с файлами**: переименование, удаление, чтение содержимого
- **Управление папками**: создание папок, получение дерева файлов

#### `test_tutorial.py` - End-to-end туториал
- **Импорт структуры данных**: tutorial.ds.json с Base64 контентом
- **Генерация Python классов**: автоматическое создание моделей
- **Импорт файлов туториала**: скрипты, тесты, процессы
- **Выполнение процесса**: TutorialProcess.df.json с тестовыми данными
- **Мониторинг job**: получение списка, деталей и событий

### 🖥️ UI тесты
- `test_login.py` - Авторизация
- `test_project_buttons.py` - Интерфейс проектов
- `test_data_struct.py` - Структуры данных
- `test_flow_*.py` - Flow компоненты
- `test_http_flow.py` - HTTP операции

## 📊 Логирование

### Кастомный логгер
Все API тесты используют кастомный логгер с файловым выводом:

```python
from custom_logger import setup_test_logger

def test_something():
    logger = setup_test_logger("my_test")
    logger.info("Начинаем тест")
    # ... тест код ...
    logger.close()
```

### Управление логами

```bash
# Показать информацию о логах
python utils/clear_logs.py info

# Удалить логи старше 7 дней
python utils/clear_logs.py clear 7

# Предварительный просмотр удаления
python utils/clear_logs.py clear 7 --dry-run

# Удалить все логи
python utils/clear_logs.py clear-all
```

### Структура логов
```
logs/
├── api_project_test_20251027_200314.log    # API проект тест
├── file_panel_test_20251027_200320.log     # Файловая панель (12 тестов)
└── tutorial_test_20251027_200325.log       # Туториал end-to-end
```

## 🔧 Конфигурация

### pytest.ini
```ini
[pytest]
addopts = -q --ignore=tests/ui/test_flow_backup.py -p pytest_host
markers =
    smoke: быстрые смоук-тесты
```

### conftest.py
- **Фикстуры проектов**: `api_project`, `tutorial_project`
- **API клиенты**: `file_panel_api`, `tutorial_file_panel_api`, `tutorial_process_log_api`
- **Конфигурация хостов**: автоматический выбор URL и cookies

## 📝 Примеры команд

### API тесты
```bash
# Все API тесты с подробным выводом
python -m pytest tests/api/ -v -s --test-host=local-192

# Только файловая панель
python -m pytest tests/api/test_file_panel.py -v -s --test-host=local-192

# Только туториал
python -m pytest tests/api/test_tutorial.py -v -s --test-host=local-192

# Конкретный тест
python -m pytest tests/api/test_file_panel.py::TestFilePanelCreation::test_create_folder -v -s --test-host=local-192
```

### UI тесты
```bash
# Все UI тесты
python run_tests.py local-192 tests/ui/ -v

# Конкретный UI тест
python run_tests.py local-192 tests/ui/test_login.py -v

# Smoke тесты
python run_tests.py st2 -m smoke -v
```

### Утилиты
```bash
# Очистка логов
python utils/clear_logs.py clear 7

# Очистка тестовых проектов
python utils/clear_projects.py

# Информация о логах
python utils/clear_logs.py info
```

## 🚨 Устранение проблем

### Ошибка подключения API
```bash
# Проверьте доступность хоста
curl -k http://192.168.0.7:3333/api/projects

# Проверьте .env файл
cat .env
```

### Ошибка авторизации
```bash
# Проверьте логин/пароль в .env
echo $LOGIN
echo $PASSWORD
```

### Проблемы с логами
```bash
# Проверьте папку логов
ls -la logs/

# Очистите старые логи
python utils/clear_logs.py clear 1
```

### Неправильный хост
```bash
# Убедитесь, что хост указан правильно
python -m pytest tests/api/ --collect-only --test-host=local-192
```

## 📈 Статистика тестов

### API тесты (15 тестов)
- ✅ **test_api.py**: 1 тест - полный цикл проекта
- ✅ **test_file_panel.py**: 12 тестов - файловая панель
- ✅ **test_tutorial.py**: 1 тест - end-to-end туториал
- ✅ **Время выполнения**: ~24 секунды
- ✅ **Логирование**: автоматическое в файлы

### Покрытие функциональности
- 🔧 **Управление проектами**: создание, изменение, удаление
- 📁 **Файловая панель**: все операции с файлами и папками
- 🎯 **Туториал**: полный цикл с процессами и мониторингом
- 📊 **Логирование**: структурированные логи с временными метками

## 🎯 Особенности

- **Общие лог файлы**: каждый тестовый файл пишет в один лог
- **Автоматическая очистка**: проекты удаляются после тестов
- **Гибкие хосты**: поддержка множества окружений
- **Структурированные логи**: временные метки и четкая структура
- **Утилиты управления**: очистка логов и проектов

---

*Версия: 2.0 - API Testing Suite*  
*Последнее обновление: 2025-10-27*