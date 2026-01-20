"""
Генератор HTML отчёта по агрегированной статистике компонентов
Показывает, как меняется время выполнения компонентов под нагрузкой
"""

import argparse
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
import statistics


def load_aggregated_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """Загружает агрегированные данные"""
    rows = []
    if not csv_path.exists():
        return rows
    
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    return rows


def load_component_timings(csv_path: Path) -> List[Dict[str, Any]]:
    """Загружает детальные данные по компонентам"""
    rows = []
    if not csv_path.exists():
        return rows
    
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    return rows


def generate_aggregated_html_report(aggregated_rows: List[Dict[str, Any]], detailed_rows: List[Dict[str, Any]], output_path: Path):
    """Генерирует HTML отчёт с агрегированной статистикой"""
    
    # Группируем детальные данные по компонентам и запросам для построения трендов
    by_component_by_request: Dict[str, Dict[str, float]] = {}
    request_order: List[str] = []
    
    for row in detailed_rows:
        title = row.get("component_title", "")
        request_id = row.get("request_id", "")
        if not title or not request_id:
            continue
        
        if request_id not in request_order:
            request_order.append(request_id)
        
        if title not in by_component_by_request:
            by_component_by_request[title] = {}
        
        try:
            duration = float(row.get("duration_ms", 0) or 0)
            # Если для этого запроса уже есть значение, берём среднее (на случай нескольких выполнений)
            if request_id in by_component_by_request[title]:
                by_component_by_request[title][request_id] = (
                    by_component_by_request[title][request_id] + duration
                ) / 2
            else:
                by_component_by_request[title][request_id] = duration
        except (ValueError, TypeError):
            pass
    
    # Подготовка данных для таблицы + массив прогонов по компоненту (для графика)
    table_rows = []
    for row in aggregated_rows:
        title = row.get("component_title", "")
        count = int(row.get("count", 0) or 0)
        total_requests = int(row.get("total_requests", 0) or 0)
        avg = float(row.get("avg_ms", 0) or 0)
        min_val = float(row.get("min_ms", 0) or 0)
        max_val = float(row.get("max_ms", 0) or 0)
        median = float(row.get("median_ms", 0) or 0)
        stddev = float(row.get("stddev_ms", 0) or 0)
        runs_ms_raw = row.get("runs_ms", "") or ""
        runs_req_raw = row.get("runs_request_id", "") or ""
        try:
            runs_ms = [float(x) for x in runs_ms_raw.split(",") if x.strip() != ""]
        except Exception:
            runs_ms = []
        runs_req = [x for x in runs_req_raw.split(",") if x.strip() != ""]
        
        # Вычисляем коэффициент вариации (CV) для оценки стабильности
        cv = (stddev / avg * 100) if avg > 0 else 0
        
        # Задержки между компонентами
        avg_gap_raw = row.get("avg_gap_ms", "") or ""
        min_gap_raw = row.get("min_gap_ms", "") or ""
        max_gap_raw = row.get("max_gap_ms", "") or ""
        median_gap_raw = row.get("median_gap_ms", "") or ""
        
        avg_gap = float(avg_gap_raw) if avg_gap_raw else None
        min_gap = float(min_gap_raw) if min_gap_raw else None
        max_gap = float(max_gap_raw) if max_gap_raw else None
        median_gap = float(median_gap_raw) if median_gap_raw else None
        
        table_rows.append({
            "title": title,
            "title_base": row.get("component_title_base", "") or title,
            "title_level": row.get("component_title_level", ""),
            "title_path": row.get("component_title_path", ""),
            "component_type": row.get("component_type", "").split(".")[-1] if row.get("component_type") else "",
            "count": count,
            "total_requests": total_requests,
            "avg": avg,
            "min": min_val,
            "max": max_val,
            "median": median,
            "stddev": stddev,
            "cv": cv,
            "avg_gap": avg_gap,
            "min_gap": min_gap,
            "max_gap": max_gap,
            "median_gap": median_gap,
            "trend_data": by_component_by_request.get(title, {}),
            "runs_ms": runs_ms,
            "runs_req": runs_req,
        })
    
    # Не сортируем: оставляем порядок строк из component_timings_aggregated.csv (порядок выполнения)
    
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Агрегированная статистика компонентов</title>
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
    .component-type {{ color: #6b7280; font-size: 11px; }}
    .duration-high {{ color: #dc2626; font-weight: 600; }}
    .duration-medium {{ color: #f59e0b; font-weight: 600; }}
    .duration-low {{ color: #059669; }}
    .cv-high {{ color: #dc2626; font-weight: 600; }}
    .cv-medium {{ color: #f59e0b; }}
    .cv-low {{ color: #059669; }}
    .chart-container {{ position: relative; height: 300px; width: 100%; margin-bottom: 32px; }}
  </style>
</head>
<body>
  <h1>Агрегированная статистика компонентов под нагрузкой</h1>
  
  <div class="card">
    <h2>Описание метрик</h2>
    <ul style="line-height: 1.8;">
      <li><strong>count</strong> — количество выполнений компонента</li>
      <li><strong>avg_ms</strong> — среднее время выполнения в миллисекундах</li>
      <li><strong>min_ms / max_ms</strong> — минимальное и максимальное время выполнения</li>
      <li><strong>median_ms</strong> — медианное время выполнения</li>
      <li><strong>stddev_ms</strong> — стандартное отклонение (показывает разброс значений)</li>
      <li><strong>CV %</strong> — коэффициент вариации (stddev/avg * 100). Чем выше, тем менее стабильно выполнение компонента</li>
      <li><strong>Задержки (gap)</strong> — время между завершением предыдущего компонента и началом текущего. Показывает интервалы между компонентами в порядке выполнения.</li>
    </ul>
  </div>

  <div class="card">
    <h2>Таблица статистики по компонентам</h2>
    <p>Компоненты отображаются в порядке выполнения (как на диаграмме).</p>
    <table>
      <thead>
        <tr>
          <th>Компонент</th>
          <th>Группа</th>
          <th>Уровень</th>
          <th>Путь</th>
          <th>Тип</th>
          <th>Выполнений</th>
          <th>Всего запросов</th>
          <th>Среднее (мс)</th>
          <th>Мин (мс)</th>
          <th>Макс (мс)</th>
          <th>Медиана (мс)</th>
          <th>Стд. откл. (мс)</th>
          <th>CV %</th>
          <th>Ср. задержка (мс)</th>
          <th>Мин задержка (мс)</th>
          <th>Макс задержка (мс)</th>
          <th>Мед. задержка (мс)</th>
        </tr>
      </thead>
      <tbody>
"""
    
    for row in table_rows:
        avg = row["avg"]
        cv = row["cv"]
        
        # Определяем класс для среднего времени
        if avg > 1000:
            avg_class = "duration-high"
        elif avg > 100:
            avg_class = "duration-medium"
        else:
            avg_class = "duration-low"
        
        # Определяем класс для CV
        if cv > 50:
            cv_class = "cv-high"
        elif cv > 20:
            cv_class = "cv-medium"
        else:
            cv_class = "cv-low"
        
        # Определяем класс для задержек
        avg_gap = row.get("avg_gap")
        if avg_gap is not None:
            if avg_gap > 100:
                gap_class = "duration-high"
            elif avg_gap > 10:
                gap_class = "duration-medium"
            else:
                gap_class = "duration-low"
        else:
            gap_class = ""
        
        html_content += f"""        <tr>
          <td><strong>{row['title']}</strong></td>
          <td><code style="font-size: 10px;">{row['title_base']}</code></td>
          <td class="component-type">{row['title_level']}</td>
          <td class="component-type">{row['title_path']}</td>
          <td class="component-type">{row['component_type']}</td>
          <td>{row['count']}</td>
          <td>{row['total_requests']}</td>
          <td class="{avg_class}">{avg:.2f}</td>
          <td>{row['min']:.2f}</td>
          <td>{row['max']:.2f}</td>
          <td>{row['median']:.2f}</td>
          <td>{row['stddev']:.2f}</td>
          <td class="{cv_class}">{cv:.1f}%</td>
          <td class="{gap_class}">{f"{avg_gap:.2f}" if avg_gap is not None else "—"}</td>
          <td>{f"{row['min_gap']:.2f}" if row.get("min_gap") is not None else "—"}</td>
          <td>{f"{row['max_gap']:.2f}" if row.get("max_gap") is not None else "—"}</td>
          <td>{f"{row['median_gap']:.2f}" if row.get("median_gap") is not None else "—"}</td>
        </tr>
"""
    
    html_content += """      </tbody>
    </table>
  </div>

  <div class="card">
    <h2>График: значения каждого прогона (для любого компонента)</h2>
    <p>Выбери компонент — увидишь время выполнения по каждому прогону (например, 50 точек для 50 прогонов).</p>
    <div style="display:flex; gap: 12px; align-items:center; flex-wrap: wrap;">
      <label for="componentSelect"><strong>Компонент:</strong></label>
      <select id="componentSelect" style="min-width: 420px; padding: 6px 10px; border: 1px solid #e5e7eb; border-radius: 6px;"></select>
    </div>
    <div class="chart-container" style="margin-top: 14px;">
      <canvas id="runsChart"></canvas>
    </div>
    <p style="color:#6b7280; font-size: 12px; margin-top: 8px;">
      Источник: колонка <code>runs_ms</code> из <code>component_timings_aggregated.csv</code> (значения через запятую).
    </p>
  </div>

  <script>
    window.addEventListener('load', function() {
      if (typeof Chart === 'undefined') {
        console.error('Chart.js не загружен!');
        return;
      }

      const components = %COMPONENTS_JSON%;
      const select = document.getElementById('componentSelect');
      const ctx = document.getElementById('runsChart');
      if (!select || !ctx) return;

      // fill select
      components.forEach((c, idx) => {
        const opt = document.createElement('option');
        opt.value = String(idx);
        opt.textContent = `${c.title} (${c.count} runs, avg=${c.avg.toFixed(2)}ms)`;
        select.appendChild(opt);
      });

      let chart = null;
      function render(idx) {
        const c = components[idx];
        const labels = c.runs_ms.map((_, i) => `Run ${i+1}`);
        const data = c.runs_ms;
        if (chart) chart.destroy();
        chart = new Chart(ctx, {
          type: 'line',
          data: {
            labels,
            datasets: [{
              label: 'duration_ms',
              data,
              borderColor: 'rgba(59, 130, 246, 1)',
              backgroundColor: 'rgba(59, 130, 246, 0.10)',
              borderWidth: 2,
              fill: true,
              tension: 0.25,
              pointRadius: 2,
              pointHoverRadius: 5,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              title: { display: true, text: c.title }
            },
            scales: {
              y: { beginAtZero: true, title: { display: true, text: 'ms' } },
              x: { title: { display: true, text: 'run' } }
            }
          }
        });
      }

      select.addEventListener('change', (e) => render(Number(e.target.value)));
      render(0);
    });
  </script>
</body>
</html>"""

    # Встраиваем данные компонентов прямо в HTML (чтобы можно было открыть файл локально)
    components_json = []
    for r in table_rows:
        if not r["runs_ms"]:
            continue
        components_json.append({
            "title": r["title"],
            "count": r["count"],
            "avg": r["avg"],
            "runs_ms": r["runs_ms"],
        })
    html_content = html_content.replace("%COMPONENTS_JSON%", json.dumps(components_json, ensure_ascii=False))
    
    with output_path.open("w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"[AGGREGATED_REPORT] HTML отчёт сохранён: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Генерация агрегированного HTML отчёта по метрикам компонентов")
    parser.add_argument("--report-dir", type=str, required=True, help="Директория с отчётами")
    args = parser.parse_args()
    
    report_dir = Path(args.report_dir)
    aggregated_csv = report_dir / "component_timings_aggregated.csv"
    detailed_csv = report_dir / "component_timings.csv"
    html_path = report_dir / "component_timings_aggregated_report.html"
    
    if not aggregated_csv.exists():
        print(f"[ERROR] Файл не найден: {aggregated_csv}")
        print(f"[INFO] Сначала запустите build_component_timings.py для создания агрегированного CSV")
        return
    
    aggregated_rows = load_aggregated_csv(aggregated_csv)
    detailed_rows = load_component_timings(detailed_csv)
    
    if not aggregated_rows:
        print(f"[WARNING] Агрегированный CSV файл пуст")
        return
    
    generate_aggregated_html_report(aggregated_rows, detailed_rows, html_path)
    print(f"[SUCCESS] Отчёт создан: {html_path}")


if __name__ == "__main__":
    main()
