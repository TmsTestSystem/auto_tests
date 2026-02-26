# Запуск нагрузочного теста

## Базовое использование

```bash
cd load_testing/load
python run.py -u 10 -r 10 -t 60
```

## Параметры

- `-u, --users` - количество одновременных пользователей (по умолчанию: 100)
- `-r, --spawn-rate` - скорость создания пользователей в секунду (по умолчанию: 50)
- `-t, --duration` - длительность теста в секундах
- `-n, --num-requests` - общее количество запросов (вместо длительности)
- `-H, --host` - целевой хост для тестирования (по умолчанию: `local-192`)

## Алиасы хостов

Можно использовать алиасы вместо полных URL (как в `conftest.py`):

- `st1` - https://decision-flow-frontend-st1.df-st.b-pl.cloud2
- `st2` - https://decision-flow-frontend-st2.df-st.b-pl.cloud2
- `st3` - https://decision-flow-frontend-st3.df-st.b-pl.cloud2
- `st4` - https://decision-flow-web-1.df-st4.cloud2.b-pl.pro
- `local-a` - http://localhost:3333
- `local-b` - http://localhost:3334
- `local-c` - http://localhost:3335
- `local-192` - http://192.168.0.7:3333 (по умолчанию)
- `local-192-https` - https://192.168.0.7/ (только для этой машины)

Также можно указать полный URL напрямую: `http://192.168.1.100:3333`

## Примеры запуска на разных стендах

### Локальный стенд (по умолчанию)
```bash
python run.py -u 10 -r 10 -t 60
# или явно указать алиас
python run.py -u 10 -r 10 -t 60 -H local-192
```

### Удалённые стенды (через алиасы)
```bash
# Стенд st1
python run.py -u 10 -r 10 -t 60 -H st1

# Стенд st2
python run.py -u 10 -r 10 -t 60 -H st2

# Стенд st3
python run.py -u 10 -r 10 -t 60 -H st3

# Стенд st4
python run.py -u 10 -r 10 -t 60 -H st4
```

### Локальные стенды (через алиасы)
```bash
# local-a (localhost:3333)
python run.py -u 10 -r 10 -t 60 -H local-a

# local-b (localhost:3334)
python run.py -u 10 -r 10 -t 60 -H local-b

# local-c (localhost:3335)
python run.py -u 10 -r 10 -t 60 -H local-c
```

### Произвольный хост (полный URL)
```bash
python run.py -u 10 -r 10 -t 60 -H http://192.168.1.100:3333
```

### Тест на определённое количество запросов
```bash
python run.py -u 10 -r 10 -n 1000 -H st1
```

### Длительный тест (10 минут)
```bash
python run.py -u 10 -r 10 -t 600 -H st2
```

## Результаты

После выполнения теста результаты сохраняются в:
- `load_testing/load/reports/YYYYMMDD_HHMMSS/`
  - `comparison_report.html` - HTML отчёт с графиками и таблицами
  - `comparison_table.csv` - CSV с выборочными данными (каждый 15-й запрос)
  - `comparison_table_full.csv` - CSV со всеми данными
  - `locust_report.html` - стандартный отчёт Locust

## Требования

- Python 3.8+
- Locust установлен и доступен в PATH (`pip install locust`)
- Все зависимости из `requirements.txt` установлены
- Доступ к целевому хосту для API вызовов и нагрузочного тестирования

## Установка на Ubuntu/Linux

```bash
# Установить зависимости
pip install -r requirements.txt

# Или установить только необходимое для нагрузочного теста
pip install locust requests urllib3

# Проверить, что locust доступен
locust --version
```

## Примечания

- Код полностью кроссплатформенный и работает на Windows, Linux и macOS
- Хост, указанный через `-H` (алиас или полный URL), используется как для API вызовов (создание проекта, импорт), так и для нагрузочного тестирования
- Алиасы хостов соответствуют тем же, что используются в `conftest.py` для UI тестов
- Перед тестом автоматически создаётся проект и импортируется `test_load-branch-main.zip`
- После теста проект автоматически удаляется
- CSV файлы используют разделитель `;` и кодировку UTF-8 с BOM для совместимости с Excel
