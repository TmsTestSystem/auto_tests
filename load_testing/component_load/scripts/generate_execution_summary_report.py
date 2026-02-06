"""
Генератор отчёта по каждому прогону: время стрелок vs время компонентов.

Показывает для каждого request_id:
- Суммарное время выполнения всех компонентов
- Суммарное время работы всех стрелок
- Соотношение времени стрелок к времени компонентов
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def load_component_timings(csv_path: Path) -> List[Dict[str, Any]]:
    """Загружает component_timings.csv"""
    rows = []
    if not csv_path.exists():
        return rows
    
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    return rows


def load_link_events(csv_path: Path) -> List[Dict[str, Any]]:
    """Загружает link_events.csv"""
    rows = []
    if not csv_path.exists():
        return rows
    
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    return rows


def generate_execution_summary_report(
    component_rows: List[Dict[str, Any]],
    link_rows: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """Генерирует HTML отчёт сравнения времени стрелок и компонентов по прогонам"""
    
    # Группируем по request_id
    by_request: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "request_id": "",
        "components_count": 0,
        "components_total_ms": 0.0,
        "links_count": 0,
        "links_total_ms": 0.0,
        "links_from_events_total_ms": 0.0,
    })
    
    # Суммируем время компонентов
    for row in component_rows:
        request_id = (row.get("request_id") or "").strip()
        if not request_id:
            continue
        
        try:
            duration_ms = float(row.get("duration_ms", 0) or 0)
            if duration_ms > 0:
                by_request[request_id]["request_id"] = request_id
                by_request[request_id]["components_count"] += 1
                by_request[request_id]["components_total_ms"] += duration_ms
        except (ValueError, TypeError):
            continue
    
    # Суммируем время стрелок
    for row in link_rows:
        request_id = (row.get("request_id") or "").strip()
        if not request_id:
            continue
        
        try:
            # Используем реальное время стрелки (duration_ms), если есть
            duration_ms = float(row.get("duration_ms", 0) or 0)
            duration_from_events = float(row.get("duration_from_events_ms", 0) or 0)
            
            if duration_ms > 0:
                by_request[request_id]["links_count"] += 1
                by_request[request_id]["links_total_ms"] += duration_ms
            elif duration_from_events > 0:
                # Если нет реального времени, используем время из событий
                by_request[request_id]["links_count"] += 1
                by_request[request_id]["links_from_events_total_ms"] += duration_from_events
        except (ValueError, TypeError):
            continue
    
    # Преобразуем в список и сортируем по request_id
    summary_rows = []
    for request_id, data in sorted(by_request.items()):
        components_total = data["components_total_ms"]
        links_total = data["links_total_ms"] or data["links_from_events_total_ms"]
        
        # Вычисляем соотношение
        links_percent = (links_total / components_total * 100) if components_total > 0 else 0
        total_time = components_total + links_total
        
        summary_rows.append({
            "request_id": request_id,
            "components_count": data["components_count"],
            "components_total_ms": components_total,
            "links_count": data["links_count"],
            "links_total_ms": links_total,
            "links_percent": links_percent,
            "total_time_ms": total_time,
        })
    
    if not summary_rows:
        print(f"[EXECUTION_SUMMARY] Нет данных для отчёта")
        return
    
    # Подготовка данных для графиков
    request_ids = [r["request_id"][:8] for r in summary_rows]
    components_times = [r["components_total_ms"] for r in summary_rows]
    links_times = [r["links_total_ms"] for r in summary_rows]
    total_times = [r["total_time_ms"] for r in summary_rows]
    links_percents = [r["links_percent"] for r in summary_rows]
    
    # Статистика
    avg_components = sum(components_times) / len(components_times) if components_times else 0
    avg_links = sum(links_times) / len(links_times) if links_times else 0
    avg_total = sum(total_times) / len(total_times) if total_times else 0
    avg_links_percent = sum(links_percents) / len(links_percents) if links_percents else 0
    
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Сводка выполнения: стрелки vs компоненты</title>
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
    .stats {{ display: flex; gap: 24px; margin: 16px 0; flex-wrap: wrap; }}
    .stat-item {{ padding: 12px; background: #f0f9ff; border-radius: 6px; min-width: 120px; }}
    .stat-value {{ font-size: 24px; font-weight: bold; color: #0369a1; }}
    .stat-label {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
    .chart-container {{ position: relative; height: 400px; margin-top: 16px; }}
    .info {{ color: #6b7280; font-size: 12px; margin-top: 8px; }}
    .components-time {{ color: #10b981; font-weight: 600; }}
    .links-time {{ color: #f59e0b; font-weight: 600; }}
    .total-time {{ color: #3b82f6; font-weight: 600; }}
    .percent-high {{ color: #dc2626; font-weight: 600; }}
    .percent-medium {{ color: #f59e0b; font-weight: 600; }}
    .percent-low {{ color: #10b981; }}
  </style>
</head>
<body>
  <h1>Сводка выполнения: стрелки vs компоненты</h1>
  <p class="info">Сравнение времени выполнения компонентов и времени работы стрелок для каждого прогона (request_id).</p>
  
  <div class="card">
    <h2>Общая статистика</h2>
    <div class="stats">
      <div class="stat-item">
        <div class="stat-value">{len(summary_rows)}</div>
        <div class="stat-label">Прогонов</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{avg_components:.1f} мс</div>
        <div class="stat-label">Среднее время компонентов</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{avg_links:.1f} мс</div>
        <div class="stat-label">Среднее время стрелок</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{avg_total:.1f} мс</div>
        <div class="stat-label">Среднее общее время</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{avg_links_percent:.1f}%</div>
        <div class="stat-label">Средний % времени стрелок</div>
      </div>
    </div>
  </div>
  
  <div class="card">
    <h2>График: время компонентов и стрелок по прогонам</h2>
    <div class="chart-container">
      <canvas id="timeChart"></canvas>
    </div>
  </div>
  
  <div class="card">
    <h2>График: процент времени стрелок от общего времени</h2>
    <div class="chart-container">
      <canvas id="percentChart"></canvas>
    </div>
  </div>
  
  <div class="card">
    <h2>Таблица: детальная сводка по каждому прогону</h2>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>request_id</th>
          <th>Компонентов</th>
          <th>Время компонентов (мс)</th>
          <th>Стрелок</th>
          <th>Время стрелок (мс)</th>
          <th>% стрелок</th>
          <th>Общее время (мс)</th>
        </tr>
      </thead>
      <tbody>
"""
    
    for i, row in enumerate(summary_rows, 1):
        request_id = row["request_id"]
        components_time = row["components_total_ms"]
        links_time = row["links_total_ms"]
        links_percent = row["links_percent"]
        total_time = row["total_time_ms"]
        
        # Класс для процента
        percent_class = ""
        if links_percent > 50:
            percent_class = "percent-high"
        elif links_percent > 20:
            percent_class = "percent-medium"
        else:
            percent_class = "percent-low"
        
        html_content += f"""        <tr>
          <td>{i}</td>
          <td><code style="font-size: 10px;">{request_id[:8]}</code></td>
          <td>{row['components_count']}</td>
          <td class="components-time">{components_time:.2f}</td>
          <td>{row['links_count']}</td>
          <td class="links-time">{links_time:.2f}</td>
          <td class="{percent_class}">{links_percent:.1f}%</td>
          <td class="total-time">{total_time:.2f}</td>
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
      
      const requestIds = """ + json.dumps(request_ids, ensure_ascii=False) + """;
      const componentsTimes = """ + json.dumps(components_times, ensure_ascii=False) + """;
      const linksTimes = """ + json.dumps(links_times, ensure_ascii=False) + """;
      const totalTimes = """ + json.dumps(total_times, ensure_ascii=False) + """;
      const linksPercents = """ + json.dumps(links_percents, ensure_ascii=False) + """;
      
      // График времени компонентов и стрелок
      const ctx1 = document.getElementById('timeChart').getContext('2d');
      new Chart(ctx1, {{
        type: 'bar',
        data: {{
          labels: requestIds,
          datasets: [
            {{
              label: 'Время компонентов (мс)',
              data: componentsTimes,
              backgroundColor: 'rgba(16, 185, 129, 0.6)',
              borderColor: 'rgba(16, 185, 129, 1)',
              borderWidth: 2,
            }},
            {{
              label: 'Время стрелок (мс)',
              data: linksTimes,
              backgroundColor: 'rgba(245, 158, 11, 0.6)',
              borderColor: 'rgba(245, 158, 11, 1)',
              borderWidth: 2,
            }},
            {{
              label: 'Общее время (мс)',
              data: totalTimes,
              backgroundColor: 'rgba(59, 130, 246, 0.3)',
              borderColor: 'rgba(59, 130, 246, 1)',
              borderWidth: 2,
              type: 'line',
              pointRadius: 4,
            }}
          ]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            title: {{
              display: true,
              text: 'Время выполнения компонентов и стрелок по прогонам',
              font: {{ size: 16 }}
            }},
            legend: {{
              display: true
            }}
          }},
          scales: {{
            y: {{
              beginAtZero: true,
              title: {{
                display: true,
                text: 'Время (мс)'
              }}
            }},
            x: {{
              title: {{
                display: true,
                text: 'Номер прогона (request_id)'
              }}
            }}
          }}
        }}
      }});
      
      // График процента времени стрелок
      const ctx2 = document.getElementById('percentChart').getContext('2d');
      new Chart(ctx2, {{
        type: 'line',
        data: {{
          labels: requestIds,
          datasets: [{{
            label: '% времени стрелок от общего времени',
            data: linksPercents,
            borderColor: 'rgba(245, 158, 11, 1)',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6,
            tension: 0.1,
          }}]
        }},
        options: {{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {{
            title: {{
              display: true,
              text: 'Процент времени стрелок от общего времени выполнения',
              font: {{ size: 16 }}
            }},
            legend: {{
              display: true
            }}
          }},
          scales: {{
            y: {{
              beginAtZero: true,
              title: {{
                display: true,
                text: 'Процент (%)'
              }}
            }},
            x: {{
              title: {{
                display: true,
                text: 'Номер прогона (request_id)'
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
    print(f"[EXECUTION_SUMMARY] HTML отчёт сохранён: {output_path}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Генерирует отчёт сравнения времени стрелок и компонентов по прогонам")
    p.add_argument(
        "--report-dir",
        type=str,
        required=True,
        help="Путь к директории отчёта (содержит component_timings.csv и link_events.csv)",
    )
    args = p.parse_args(argv)
    
    report_dir = Path(args.report_dir).resolve()
    component_csv = report_dir / "component_timings.csv"
    link_csv = report_dir / "link_events.csv"
    
    if not component_csv.exists():
        print(f"[ERROR] Файл не найден: {component_csv}")
        return
    
    if not link_csv.exists():
        print(f"[WARNING] Файл не найден: {link_csv}, будут показаны только компоненты")
    
    component_rows = load_component_timings(component_csv)
    link_rows = load_link_events(link_csv)
    
    if not component_rows:
        print(f"[WARNING] Нет данных в {component_csv}")
        return
    
    output_html = report_dir / "execution_summary_report.html"
    generate_execution_summary_report(component_rows, link_rows, output_html)
    print(f"[SUCCESS] Отчёт создан: {output_html}")


if __name__ == "__main__":
    main()
