"""
Скрипт для анализа времени выполнения компонентов на диаграмме.

Анализирует метрики выполнения компонентов:
- Время выполнения каждого компонента
- Промежутки между выполнением компонентов
- Общее время выполнения диаграммы
"""

import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


def analyze_component_duration(components_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Анализирует длительность выполнения компонентов.
    
    Args:
        components_data: Список данных о компонентах
        
    Returns:
        Словарь с метриками анализа
    """
    if not components_data:
        return {}
    
    durations = [comp.get("duration_ms", 0) for comp in components_data]
    
    return {
        "min_duration_ms": min(durations),
        "max_duration_ms": max(durations),
        "avg_duration_ms": sum(durations) / len(durations),
        "total_duration_ms": sum(durations),
        "components_count": len(components_data)
    }


def analyze_component_intervals(components_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Анализирует промежутки между выполнением компонентов.
    
    Args:
        components_data: Список данных о компонентах, отсортированный по времени
        
    Returns:
        Список промежутков между компонентами
    """
    intervals = []
    
    for i in range(len(components_data) - 1):
        current = components_data[i]
        next_comp = components_data[i + 1]
        
        current_end = current.get("end_time")
        next_start = next_comp.get("start_time")
        
        if current_end and next_start:
            # Вычисление интервала (требует парсинга времени)
            interval = {
                "from_component": current.get("component_name"),
                "to_component": next_comp.get("component_name"),
                "interval_ms": None  # TODO: вычислить интервал
            }
            intervals.append(interval)
    
    return intervals


def load_metrics_from_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Загружает метрики из CSV файла.
    
    Args:
        csv_path: Путь к CSV файлу с метриками
        
    Returns:
        Список словарей с данными метрик
    """
    metrics = []
    
    if not csv_path.exists():
        print(f"Файл {csv_path} не найден")
        return metrics
    
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            metrics.append(row)
    
    return metrics


def load_metrics_from_json(json_path: Path) -> List[Dict[str, Any]]:
    """
    Загружает метрики из JSON файла.
    
    Args:
        json_path: Путь к JSON файлу с метриками
        
    Returns:
        Список словарей с данными метрик
    """
    if not json_path.exists():
        print(f"Файл {json_path} не найден")
        return []
    
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "components" in data:
            return data["components"]
        return [data]


def generate_report(metrics_data: List[Dict[str, Any]], output_path: Path):
    """
    Генерирует отчет по метрикам компонентов.
    
    Args:
        metrics_data: Данные метрик
        output_path: Путь для сохранения отчета
    """
    analysis = analyze_component_duration(metrics_data)
    intervals = analyze_component_intervals(metrics_data)
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": analysis,
        "intervals": intervals,
        "components": metrics_data
    }
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"Отчет сохранен в {output_path}")


if __name__ == "__main__":
    # Пример использования
    # TODO: Добавить парсинг аргументов командной строки
    # TODO: Добавить загрузку данных из реальных источников
    print("Скрипт для анализа метрик компонентов")
    print("TODO: Реализовать полную функциональность")
