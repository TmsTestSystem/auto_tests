"""
Генератор HTML отчёта по метрикам компонентов из component_timings.csv
"""

import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any


def load_component_timings(csv_path: Path) -> List[Dict[str, Any]]:
    """Загружает данные из component_timings.csv"""
    rows = []
    if not csv_path.exists():
        return rows
    
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    return rows


def format_duration_ms(value: str) -> str:
    """Форматирует длительность в миллисекундах для отображения"""
    try:
        val = float(value)
        if val < 1:
            return f"{val:.3f}"
        elif val < 1000:
            return f"{val:.2f}"
        else:
            return f"{val:.1f}"
    except (ValueError, TypeError):
        return value or ""


def format_gap_ms(value: str) -> str:
    """Форматирует интервал между компонентами"""
    if not value or value.strip() == "":
        return ""
    try:
        val = float(value)
        if val < 0:
            return f"<span style='color: #dc2626;'>{val:.2f}</span>"
        elif val < 1:
            return f"{val:.3f}"
        else:
            return f"{val:.2f}"
    except (ValueError, TypeError):
        return value


def generate_html_report(rows: List[Dict[str, Any]], output_path: Path):
    """Генерирует HTML отчёт"""
    
    # Статистика
    total_components = len(rows)
    unique_requests = len(set(r.get("request_id", "") for r in rows))
    unique_jobs = len(set(r.get("job_uuid", "") for r in rows))
    
    # Группировка по request_id для графиков
    by_request: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        req_id = row.get("request_id", "")
        if req_id:
            by_request.setdefault(req_id, []).append(row)
    
    # Подготовка данных для таблицы (добавляем level/path если есть)
    table_rows = []
    for i, row in enumerate(rows, 1):
        duration = format_duration_ms(row.get("duration_ms", ""))
        gap = format_gap_ms(row.get("gap_from_prev_ms", ""))
        level = row.get("component_title_level", "")
        path = row.get("component_title_path", "")
        table_rows.append({
            "num": i,
            "request_id": row.get("request_id", ""),
            "component_title": row.get("component_title", ""),
            "component_path": path,
            "component_level": level,
            "component_type": row.get("component_type", "").split(".")[-1] if row.get("component_type") else "",
            "duration_ms": duration,
            "gap_from_prev_ms": gap,
            "component_key": row.get("component_key", "")[:8] + "..." if len(row.get("component_key", "")) > 8 else row.get("component_key", ""),
        })
    
    # Подготовка данных для графиков (по request_id)
    chart_data = []
    for req_id, comps in sorted(by_request.items()):
        labels = [c.get("component_title", "") for c in comps]
        durations = [float(c.get("duration_ms", 0) or 0) for c in comps]
        gaps = [float(c.get("gap_from_prev_ms", 0) or 0) for c in comps]
        chart_data.append({
            "request_id": req_id[:8] + "...",
            "labels": labels,
            "durations": durations,
            "gaps": gaps,
        })
    
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Метрики компонентов</title>
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
    .stats {{ display: flex; gap: 24px; margin: 16px 0; }}
    .stat-item {{ padding: 12px; background: #f0f9ff; border-radius: 6px; }}
    .stat-value {{ font-size: 24px; font-weight: bold; color: #0369a1; }}
    .stat-label {{ font-size: 12px; color: #64748b; margin-top: 4px; }}
    .component-type {{ color: #6b7280; font-size: 11px; }}
    .duration-high {{ color: #dc2626; font-weight: 600; }}
    .duration-medium {{ color: #f59e0b; font-weight: 600; }}
    .duration-low {{ color: #059669; }}
  </style>
</head>
<body>
  <h1>Метрики выполнения компонентов</h1>
  
  <div class="stats">
    <div class="stat-item">
      <div class="stat-value">{total_components}</div>
      <div class="stat-label">Всего компонентов</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">{unique_requests}</div>
      <div class="stat-label">Уникальных запросов</div>
    </div>
    <div class="stat-item">
      <div class="stat-value">{unique_jobs}</div>
      <div class="stat-label">Уникальных jobs</div>
    </div>
  </div>

  <div class="card">
    <h2>Описание метрик</h2>
    <p><strong>duration_ms</strong> — время выполнения компонента в миллисекундах (разница между статусами "done" и "in_progress" из событий).</p>
    <p><strong>gap_from_prev_ms</strong> — интервал между завершением предыдущего компонента и началом текущего в последовательности выполнения. Отрицательные значения означают перекрытие по времени (параллельное выполнение).</p>
    <p><strong>component_type</strong> — тип компонента (краткое имя класса).</p>
    <p><strong>component_key</strong> — уникальный идентификатор компонента на диаграмме.</p>
  </div>

  <div class="card">
    <h2>Таблица компонентов</h2>
    <p>Показано {total_components} компонентов из {total_components} записей.</p>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>Request ID</th>
          <th>Компонент</th>
          <th>Иерархия</th>
          <th>Тип</th>
          <th>Длительность (мс)</th>
          <th>Интервал от предыдущего (мс)</th>
          <th>Component Key</th>
        </tr>
      </thead>
      <tbody>
"""
    
    for row in table_rows:
        duration_val = row["duration_ms"]
        try:
            dur_float = float(duration_val)
            if dur_float > 1000:
                duration_class = "duration-high"
            elif dur_float > 100:
                duration_class = "duration-medium"
            else:
                duration_class = "duration-low"
        except (ValueError, TypeError):
            duration_class = ""
        
        html_content += f"""        <tr>
          <td>{row['num']}</td>
          <td><code style="font-size: 10px;">{row['request_id'][:8]}...</code></td>
          <td><strong>{row['component_title']}</strong></td>
          <td><span style="color:#6b7280; font-size: 11px;">{row['component_path'] or ''}</span></td>
          <td class="component-type">{row['component_type']}</td>
          <td class="{duration_class}">{duration_val}</td>
          <td>{row['gap_from_prev_ms']}</td>
          <td><code style="font-size: 10px;">{row['component_key']}</code></td>
        </tr>
"""
    
    html_content += """      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>Графики по запросам</h2>
    <p>Графики показывают длительность выполнения каждого компонента в рамках одного запроса.</p>
"""
    
    for i, chart in enumerate(chart_data[:5]):  # Ограничиваем до 5 графиков
        html_content += f"""
    <h3 style="margin-top: 24px; font-size: 14px;">Запрос: {chart['request_id']}</h3>
    <div style="position: relative; height: 300px; width: 100%; margin-bottom: 32px;">
      <canvas id="chart{i}"></canvas>
    </div>
"""
    
    html_content += """  </div>

  <script>
    window.addEventListener('load', function() {
      if (typeof Chart === 'undefined') {
        console.error('Chart.js не загружен!');
        return;
      }
"""
    
    for i, chart in enumerate(chart_data[:5]):
        html_content += f"""
      // График {i}
      const ctx{i} = document.getElementById('chart{i}');
      if (ctx{i}) {{
        new Chart(ctx{i}, {{
          type: 'bar',
          data: {{
            labels: {repr(chart['labels'])},
            datasets: [{{
              label: 'Длительность (мс)',
              data: {repr(chart['durations'])},
              backgroundColor: 'rgba(59, 130, 246, 0.5)',
              borderColor: 'rgba(59, 130, 246, 1)',
              borderWidth: 1
            }}]
          }},
          options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
              y: {{
                beginAtZero: true,
                title: {{
                  display: true,
                  text: 'Длительность (мс)'
                }}
              }},
              x: {{
                title: {{
                  display: true,
                  text: 'Компоненты'
                }}
              }}
            }}
          }}
        }});
      }}
"""
    
    html_content += """    });
  </script>
</body>
</html>"""
    
    with output_path.open("w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"[COMPONENT_REPORT] HTML отчёт сохранён: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Генерация HTML отчёта по метрикам компонентов")
    parser.add_argument("--report-dir", type=str, required=True, help="Директория с отчётами (должна содержать component_timings.csv)")
    args = parser.parse_args()
    
    report_dir = Path(args.report_dir)
    csv_path = report_dir / "component_timings.csv"
    html_path = report_dir / "component_timings_report.html"
    
    if not csv_path.exists():
        print(f"[ERROR] Файл не найден: {csv_path}")
        return
    
    rows = load_component_timings(csv_path)
    if not rows:
        print(f"[WARNING] CSV файл пуст или не содержит данных")
        return
    
    generate_html_report(rows, html_path)
    print(f"[SUCCESS] Отчёт создан: {html_path}")


if __name__ == "__main__":
    main()
