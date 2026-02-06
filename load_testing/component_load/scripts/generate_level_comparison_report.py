"""
Генератор отчёта сравнения производительности компонентов по уровням (test1/test2/test3).

Сравнивает среднее время выполнения компонентов на разных уровнях вложенности
и показывает, на каком уровне компоненты выполняются быстрее/медленнее.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def load_aggregated_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """Загружает агрегированные данные компонентов"""
    rows = []
    if not csv_path.exists():
        return rows
    
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    return rows


def parse_level(level_str: str) -> Optional[int]:
    """Парсит уровень из строки (может быть пустой, "1", "2", "3" и т.д.)"""
    if not level_str or level_str.strip() == "":
        return None
    try:
        return int(level_str.strip())
    except (ValueError, TypeError):
        return None


def generate_level_comparison_report(rows: List[Dict[str, Any]], output_path: Path) -> None:
    """Генерирует HTML отчёт сравнения по уровням"""
    
    # Группируем компоненты по уровням
    by_level: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    no_level: List[Dict[str, Any]] = []
    
    for row in rows:
        level_str = row.get("component_title_level", "").strip()
        level = parse_level(level_str)
        
        # Парсим числовые значения
        try:
            avg_ms = float(row.get("avg_ms", 0) or 0)
            min_ms = float(row.get("min_ms", 0) or 0)
            max_ms = float(row.get("max_ms", 0) or 0)
            median_ms = float(row.get("median_ms", 0) or 0)
            count = int(row.get("count", 0) or 0)
        except (ValueError, TypeError):
            continue
        
        component_data = {
            "title": row.get("component_title", ""),
            "title_base": row.get("component_title_base", ""),
            "component_type": row.get("component_type", ""),
            "avg_ms": avg_ms,
            "min_ms": min_ms,
            "max_ms": max_ms,
            "median_ms": median_ms,
            "count": count,
            "total_requests": int(row.get("total_requests", 0) or 0),
        }
        
        if level is not None:
            by_level[level].append(component_data)
        else:
            no_level.append(component_data)
    
    # Вычисляем статистику по уровням
    level_stats: Dict[int, Dict[str, Any]] = {}
    for level in sorted(by_level.keys()):
        components = by_level[level]
        if not components:
            continue
        
        # Собираем все значения avg_ms для уровня
        all_avg = [c["avg_ms"] for c in components]
        all_median = [c["median_ms"] for c in components]
        all_min = [c["min_ms"] for c in components]
        all_max = [c["max_ms"] for c in components]
        
        # Общее количество выполнений на уровне
        total_count = sum(c["count"] for c in components)
        total_requests = components[0]["total_requests"] if components else 0
        
        level_stats[level] = {
            "level": level,
            "component_count": len(components),
            "total_executions": total_count,
            "total_requests": total_requests,
            "avg_avg_ms": statistics.mean(all_avg) if all_avg else 0,
            "median_avg_ms": statistics.median(all_avg) if all_avg else 0,
            "min_avg_ms": min(all_avg) if all_avg else 0,
            "max_avg_ms": max(all_avg) if all_avg else 0,
            "avg_median_ms": statistics.mean(all_median) if all_median else 0,
            "components": components,
        }
    
    # Сравнение между уровнями
    comparisons: List[Dict[str, Any]] = []
    levels_sorted = sorted(level_stats.keys())
    
    for i in range(len(levels_sorted) - 1):
        level1 = levels_sorted[i]
        level2 = levels_sorted[i + 1]
        stats1 = level_stats[level1]
        stats2 = level_stats[level2]
        
        avg1 = stats1["avg_avg_ms"]
        avg2 = stats2["avg_avg_ms"]
        
        if avg1 > 0:
            diff_percent = ((avg2 - avg1) / avg1) * 100
        else:
            diff_percent = 0
        
        faster = "test" + str(level1) if avg1 < avg2 else "test" + str(level2)
        slower = "test" + str(level2) if avg1 < avg2 else "test" + str(level1)
        
        comparisons.append({
            "level1": level1,
            "level2": level2,
            "avg1": avg1,
            "avg2": avg2,
            "diff_percent": diff_percent,
            "faster": faster,
            "slower": slower,
            "faster_avg": min(avg1, avg2),
            "slower_avg": max(avg1, avg2),
        })
    
    # Подготовка данных для графиков
    chart_levels = [f"test{level}" for level in levels_sorted]
    chart_avg_values = [level_stats[level]["avg_avg_ms"] for level in levels_sorted]
    chart_median_values = [level_stats[level]["avg_median_ms"] for level in levels_sorted]
    chart_component_counts = [level_stats[level]["component_count"] for level in levels_sorted]
    
    # Генерируем HTML
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Сравнение производительности по уровням (test1/test2/test3)</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 16px; background: #f9fafb; }}
    h1 {{ color: #111827; margin-bottom: 8px; }}
    h2 {{ margin-top: 24px; color: #374151; font-size: 18px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; background: white; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 12px; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 8px 10px; text-align: left; }}
    th {{ background: #f9fafb; position: sticky; top: 0; font-weight: 600; color: #374151; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    tr:hover {{ background: #f3f4f6; }}
    .comparison-box {{ background: #f0f9ff; border-left: 4px solid #0369a1; padding: 12px; margin: 12px 0; border-radius: 4px; }}
    .comparison-box.faster {{ background: #f0fdf4; border-left-color: #10b981; }}
    .comparison-box.slower {{ background: #fef2f2; border-left-color: #dc2626; }}
    .stat-value {{ font-size: 20px; font-weight: bold; color: #0369a1; }}
    .stat-label {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
    .chart-container {{ position: relative; height: 400px; margin-top: 16px; }}
    .info {{ color: #6b7280; font-size: 12px; margin-top: 8px; }}
    .level-badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
    .level-1 {{ background: #dbeafe; color: #1e40af; }}
    .level-2 {{ background: #fef3c7; color: #92400e; }}
    .level-3 {{ background: #fce7f3; color: #9f1239; }}
    .positive {{ color: #10b981; font-weight: 600; }}
    .negative {{ color: #dc2626; font-weight: 600; }}
  </style>
</head>
<body>
  <h1>Сравнение производительности по уровням (test1/test2/test3)</h1>
  <p class="info">Сравнение среднего времени выполнения компонентов на разных уровнях вложенности.</p>
  
  <div class="card">
    <h2>Ключевые выводы</h2>
"""
    
    # Добавляем выводы по сравнениям
    for comp in comparisons:
        faster_level = comp["faster"]
        slower_level = comp["slower"]
        diff = comp["diff_percent"]
        faster_avg = comp["faster_avg"]
        slower_avg = comp["slower_avg"]
        
        if abs(diff) < 1:
            conclusion = f"<strong>{faster_level}</strong> и <strong>{slower_level}</strong> выполняются примерно одинаково (разница менее 1%)"
            box_class = ""
        else:
            conclusion = f"На уровне <strong>{faster_level}</strong> компоненты выполняются <strong>быстрее</strong> чем на уровне <strong>{slower_level}</strong> на {abs(diff):.1f}%"
            box_class = "faster" if diff < 0 else "slower"
        
        html_content += f"""
    <div class="comparison-box {box_class}">
      <div style="font-size: 14px; margin-bottom: 8px;">
        <span class="level-badge level-{comp['level1']}">test{comp['level1']}</span> 
        vs 
        <span class="level-badge level-{comp['level2']}">test{comp['level2']}</span>
      </div>
      <div style="font-size: 13px; color: #374151;">
        {conclusion}
      </div>
      <div style="font-size: 11px; color: #6b7280; margin-top: 4px;">
        test{comp['level1']}: {faster_avg:.2f} мс (среднее) | test{comp['level2']}: {slower_avg:.2f} мс (среднее)
      </div>
    </div>
"""
    
    html_content += """  </div>
  
  <div class="card">
    <h2>График: среднее время выполнения по уровням</h2>
    <div class="chart-container">
      <canvas id="avgChart"></canvas>
    </div>
  </div>
  
  <div class="card">
    <h2>График: медианное время выполнения по уровням</h2>
    <div class="chart-container">
      <canvas id="medianChart"></canvas>
    </div>
  </div>
  
  <div class="card">
    <h2>График: количество компонентов по уровням</h2>
    <div class="chart-container">
      <canvas id="countChart"></canvas>
    </div>
  </div>
  
  <div class="card">
    <h2>Статистика по уровням</h2>
    <table>
      <thead>
        <tr>
          <th>Уровень</th>
          <th>Кол-во компонентов</th>
          <th>Всего выполнений</th>
          <th>Среднее время (мс)</th>
          <th>Медианное время (мс)</th>
          <th>Мин время (мс)</th>
          <th>Макс время (мс)</th>
        </tr>
      </thead>
      <tbody>
"""
    
    for level in sorted(level_stats.keys()):
        stats = level_stats[level]
        html_content += f"""        <tr>
          <td><span class="level-badge level-{level}">test{level}</span></td>
          <td>{stats['component_count']}</td>
          <td>{stats['total_executions']}</td>
          <td><strong>{stats['avg_avg_ms']:.2f}</strong></td>
          <td>{stats['avg_median_ms']:.2f}</td>
          <td>{stats['min_avg_ms']:.2f}</td>
          <td>{stats['max_avg_ms']:.2f}</td>
        </tr>
"""
    
    html_content += """      </tbody>
    </table>
  </div>
  
  <div class="card">
    <h2>Детальная таблица: компоненты по уровням</h2>
    <table>
      <thead>
        <tr>
          <th>Уровень</th>
          <th>Компонент</th>
          <th>Базовое имя</th>
          <th>Тип</th>
          <th>Выполнений</th>
          <th>Среднее (мс)</th>
          <th>Мин (мс)</th>
          <th>Макс (мс)</th>
          <th>Медиана (мс)</th>
        </tr>
      </thead>
      <tbody>
"""
    
    for level in sorted(level_stats.keys()):
        stats = level_stats[level]
        for comp in sorted(stats["components"], key=lambda c: c["avg_ms"], reverse=True):
            html_content += f"""        <tr>
          <td><span class="level-badge level-{level}">test{level}</span></td>
          <td><code>{comp['title']}</code></td>
          <td>{comp['title_base']}</td>
          <td class="info">{comp['component_type'].split('.')[-1] if comp['component_type'] else ''}</td>
          <td>{comp['count']} / {comp['total_requests']}</td>
          <td><strong>{comp['avg_ms']:.2f}</strong></td>
          <td>{comp['min_ms']:.2f}</td>
          <td>{comp['max_ms']:.2f}</td>
          <td>{comp['median_ms']:.2f}</td>
        </tr>
"""
    
    html_content += """      </tbody>
    </table>
  </div>
  
  <script>
    window.addEventListener('load', function() {
      if (typeof Chart === 'undefined') {
        console.error('Chart.js не загружен!');
        return;
      }
      
      const levels = """ + json.dumps(chart_levels, ensure_ascii=False) + """;
      const avgValues = """ + json.dumps(chart_avg_values, ensure_ascii=False) + """;
      const medianValues = """ + json.dumps(chart_median_values, ensure_ascii=False) + """;
      const componentCounts = """ + json.dumps(chart_component_counts, ensure_ascii=False) + """;
      
      // График среднего времени
      const ctx1 = document.getElementById('avgChart').getContext('2d');
      new Chart(ctx1, {{
        type: 'bar',
        data: {{
          labels: levels,
          datasets: [{{
            label: 'Среднее время выполнения (мс)',
            data: avgValues,
            backgroundColor: ['rgba(59, 130, 246, 0.6)', 'rgba(251, 191, 36, 0.6)', 'rgba(236, 72, 153, 0.6)'],
            borderColor: ['rgba(59, 130, 246, 1)', 'rgba(251, 191, 36, 1)', 'rgba(236, 72, 153, 1)'],
            borderWidth: 2,
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            title: {{
              display: true,
              text: 'Среднее время выполнения компонентов по уровням',
              font: {{ size: 16 }}
            }},
            legend: {{
              display: false
            }}
          }},
          scales: {{
            y: {{
              beginAtZero: true,
              title: {{
                display: true,
                text: 'Время выполнения (мс)'
              }}
            }},
            x: {{
              title: {{
                display: true,
                text: 'Уровень вложенности'
              }}
            }}
          }}
        }}
      }});
      
      // График медианного времени
      const ctx2 = document.getElementById('medianChart').getContext('2d');
      new Chart(ctx2, {{
        type: 'bar',
        data: {{
          labels: levels,
          datasets: [{{
            label: 'Медианное время выполнения (мс)',
            data: medianValues,
            backgroundColor: ['rgba(59, 130, 246, 0.6)', 'rgba(251, 191, 36, 0.6)', 'rgba(236, 72, 153, 0.6)'],
            borderColor: ['rgba(59, 130, 246, 1)', 'rgba(251, 191, 36, 1)', 'rgba(236, 72, 153, 1)'],
            borderWidth: 2,
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            title: {{
              display: true,
              text: 'Медианное время выполнения компонентов по уровням',
              font: {{ size: 16 }}
            }},
            legend: {{
              display: false
            }}
          }},
          scales: {{
            y: {{
              beginAtZero: true,
              title: {{
                display: true,
                text: 'Время выполнения (мс)'
              }}
            }},
            x: {{
              title: {{
                display: true,
                text: 'Уровень вложенности'
              }}
            }}
          }}
        }}
      }});
      
      // График количества компонентов
      const ctx3 = document.getElementById('countChart').getContext('2d');
      new Chart(ctx3, {{
        type: 'bar',
        data: {{
          labels: levels,
          datasets: [{{
            label: 'Количество компонентов',
            data: componentCounts,
            backgroundColor: ['rgba(59, 130, 246, 0.6)', 'rgba(251, 191, 36, 0.6)', 'rgba(236, 72, 153, 0.6)'],
            borderColor: ['rgba(59, 130, 246, 1)', 'rgba(251, 191, 36, 1)', 'rgba(236, 72, 153, 1)'],
            borderWidth: 2,
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            title: {{
              display: true,
              text: 'Количество компонентов по уровням',
              font: {{ size: 16 }}
            }},
            legend: {{
              display: false
            }}
          }},
          scales: {{
            y: {{
              beginAtZero: true,
              title: {{
                display: true,
                text: 'Количество компонентов'
              }}
            }},
            x: {{
              title: {{
                display: true,
                text: 'Уровень вложенности'
              }}
            }}
          }}
        }}
      }});
    });
  </script>
</body>
</html>
"""
    
    output_path.write_text(html_content, encoding="utf-8")
    print(f"[LEVEL_COMPARISON] HTML отчёт сохранён: {output_path}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Генерирует отчёт сравнения производительности по уровням (test1/test2/test3)")
    p.add_argument(
        "--report-dir",
        type=str,
        required=True,
        help="Путь к директории отчёта (содержит component_timings_aggregated.csv)",
    )
    args = p.parse_args(argv)
    
    report_dir = Path(args.report_dir).resolve()
    aggregated_csv = report_dir / "component_timings_aggregated.csv"
    
    if not aggregated_csv.exists():
        print(f"[ERROR] Файл не найден: {aggregated_csv}")
        return
    
    rows = load_aggregated_csv(aggregated_csv)
    if not rows:
        print(f"[WARNING] Нет данных в {aggregated_csv}")
        return
    
    output_html = report_dir / "level_comparison_report.html"
    generate_level_comparison_report(rows, output_html)
    print(f"[SUCCESS] Отчёт создан: {output_html}")


if __name__ == "__main__":
    main()
