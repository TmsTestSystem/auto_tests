"""
Генератор HTML отчёта по групповой статистике компонентов (схлопнуто по базовому имени)
Показывает агрегированные метрики для групп компонентов (Assignment, DecisionTable и т.д.)
"""

import argparse
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
import statistics


def load_grouped_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """Загружает групповые данные"""
    rows = []
    if not csv_path.exists():
        return rows
    
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    
    return rows


def generate_grouped_html_report(grouped_rows: List[Dict[str, Any]], output_path: Path):
    """Генерирует HTML отчёт с групповой статистикой"""
    
    # Подготовка данных для таблицы
    table_rows = []
    for row in grouped_rows:
        group_base = row.get("group_title_base", "")
        example_title = row.get("example_title", "")
        count = int(row.get("count", 0) or 0)
        total_requests = int(row.get("total_requests", 0) or 0)
        avg = float(row.get("avg_ms", 0) or 0)
        min_val = float(row.get("min_ms", 0) or 0)
        max_val = float(row.get("max_ms", 0) or 0)
        median = float(row.get("median_ms", 0) or 0)
        stddev = float(row.get("stddev_ms", 0) or 0)
        avg_gap = row.get("avg_gap_ms", "") or ""
        min_gap = row.get("min_gap_ms", "") or ""
        max_gap = row.get("max_gap_ms", "") or ""
        median_gap = row.get("median_gap_ms", "") or ""
        runs_ms_raw = row.get("runs_ms", "") or ""
        runs_req_raw = row.get("runs_request_id", "") or ""
        
        try:
            runs_ms = [float(x) for x in runs_ms_raw.split(",") if x.strip() != ""]
        except Exception:
            runs_ms = []
        runs_req = [x for x in runs_req_raw.split(",") if x.strip() != ""]
        
        # Вычисляем коэффициент вариации (CV) для оценки стабильности
        cv = (stddev / avg * 100) if avg > 0 else 0
        
        table_rows.append({
            "group_base": group_base,
            "example_title": example_title,
            "component_type": row.get("component_type", "").split(".")[-1] if row.get("component_type") else "",
            "count": count,
            "total_requests": total_requests,
            "avg": avg,
            "min": min_val,
            "max": max_val,
            "median": median,
            "stddev": stddev,
            "cv": cv,
            "avg_gap": float(avg_gap) if avg_gap else None,
            "min_gap": float(min_gap) if min_gap else None,
            "max_gap": float(max_gap) if max_gap else None,
            "median_gap": float(median_gap) if median_gap else None,
            "runs_ms": runs_ms,
            "runs_req": runs_req,
        })
    
    # Не сортируем: оставляем порядок строк из component_timings_grouped.csv (порядок выполнения)
    
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Групповая статистика компонентов</title>
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
    .duration-low {{ color: #10b981; }}
    .gap-high {{ color: #dc2626; font-weight: 600; }}
    .gap-medium {{ color: #f59e0b; font-weight: 600; }}
    .gap-low {{ color: #10b981; }}
    select {{ padding: 8px 12px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; margin: 12px 0; }}
    .chart-container {{ position: relative; height: 400px; margin-top: 16px; }}
    .info {{ color: #6b7280; font-size: 12px; margin-top: 8px; }}
  </style>
</head>
<body>
  <h1>Групповая статистика компонентов</h1>
  <p class="info">Компоненты сгруппированы по базовому имени (без суффиксов _test1, _test2, _test3). Порядок — как в выполнении.</p>
  
  <div class="card">
    <h2>Статистика</h2>
    <div class="stats">
      <div class="stat-item">
        <div class="stat-value">{len(table_rows)}</div>
        <div class="stat-label">Групп компонентов</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{sum(r["count"] for r in table_rows)}</div>
        <div class="stat-label">Всего выполнений</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">{table_rows[0]["total_requests"] if table_rows else 0}</div>
        <div class="stat-label">Всего запросов</div>
      </div>
    </div>
  </div>
  
  <div class="card">
    <h2>Таблица групп компонентов</h2>
    <table>
      <thead>
        <tr>
          <th>Группа</th>
          <th>Пример</th>
          <th>Тип</th>
          <th>Выполнений</th>
          <th>Среднее (мс)</th>
          <th>Мин (мс)</th>
          <th>Макс (мс)</th>
          <th>Медиана (мс)</th>
          <th>Стд. откл. (мс)</th>
          <th>CV (%)</th>
          <th>Ср. задержка (мс)</th>
          <th>Мин задержка (мс)</th>
          <th>Макс задержка (мс)</th>
          <th>Мед. задержка (мс)</th>
        </tr>
      </thead>
      <tbody>
"""
    
    for row in table_rows:
        avg_class = "duration-high" if row["avg"] > 1000 else ("duration-medium" if row["avg"] > 100 else "duration-low")
        gap_avg = row["avg_gap"]
        gap_class = ""
        if gap_avg is not None:
            gap_class = "gap-high" if gap_avg > 100 else ("gap-medium" if gap_avg > 10 else "gap-low")
        
        html_content += f"""        <tr>
          <td><strong>{row["group_base"]}</strong></td>
          <td class="component-type">{row["example_title"]}</td>
          <td class="component-type">{row["component_type"]}</td>
          <td>{row["count"]} / {row["total_requests"]}</td>
          <td class="{avg_class}">{row["avg"]:.2f}</td>
          <td>{row["min"]:.2f}</td>
          <td>{row["max"]:.2f}</td>
          <td>{row["median"]:.2f}</td>
          <td>{row["stddev"]:.2f}</td>
          <td>{row["cv"]:.1f}</td>
          <td class="{gap_class}">{f"{gap_avg:.2f}" if gap_avg is not None else "—"}</td>
          <td>{f"{row['min_gap']:.2f}" if row["min_gap"] is not None else "—"}</td>
          <td>{f"{row['max_gap']:.2f}" if row["max_gap"] is not None else "—"}</td>
          <td>{f"{row['median_gap']:.2f}" if row["median_gap"] is not None else "—"}</td>
        </tr>
"""
    
    html_content += """      </tbody>
    </table>
  </div>
  
  <div class="card">
    <h2>График времени выполнения по прогонам</h2>
    <select id="componentSelect">
      <option value="">Выберите группу компонентов...</option>
"""
    
    for i, row in enumerate(table_rows):
        html_content += f'      <option value="{i}">{row["group_base"]} ({row["example_title"]})</option>\n'
    
    html_content += """    </select>
    <div class="chart-container">
      <canvas id="trendChart"></canvas>
    </div>
  </div>
  
  <script>
    const tableData = """ + json.dumps(table_rows, ensure_ascii=False) + """;
    let chart = null;
    
    // Инициализация графика при загрузке страницы (первый элемент)
    window.addEventListener('load', function() {
      if (typeof Chart === 'undefined') {
        console.error('Chart.js не загружен!');
        return;
      }
      
      const select = document.getElementById('componentSelect');
      if (select && tableData.length > 0) {
        select.value = '0';
        const event = new Event('change');
        select.dispatchEvent(event);
      }
    });
    
    document.getElementById('componentSelect').addEventListener('change', function(e) {
      const idx = parseInt(e.target.value);
      if (idx < 0 || idx >= tableData.length) {
        console.warn('Invalid index:', idx);
        return;
      }
      
      const row = tableData[idx];
      const runsMs = row.runs_ms || [];
      const runsReq = row.runs_req || [];
      
      if (runsMs.length === 0) {
        console.warn('No data for component:', row.group_base);
        return;
      }
      
      const ctx = document.getElementById('trendChart');
      if (!ctx) {
        console.error('Canvas element not found!');
        return;
      }
      const ctx2d = ctx.getContext('2d');
      
      if (chart) {
        chart.destroy();
      }
      
      chart = new Chart(ctx2d, {
        type: 'line',
        data: {
          labels: runsReq.map((r, i) => `Запрос ${i + 1} (${r})`),
          datasets: [{
            label: `Время выполнения ${row.group_base} (мс)`,
            data: runsMs,
            borderColor: 'rgb(59, 130, 246)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.1,
            pointRadius: 4,
            pointHoverRadius: 6,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: `Время выполнения группы "${row.group_base}" по прогонам`,
              font: { size: 16 }
            },
            legend: {
              display: true,
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              title: {
                display: true,
                text: 'Время выполнения (мс)'
              }
            },
            x: {
              title: {
                display: true,
                text: 'Номер прогона'
              }
            }
          }
        }
      });
    });
  </script>
</body>
</html>
"""
    
    output_path.write_text(html_content, encoding="utf-8")
    print(f"[GROUPED_REPORT] HTML отчёт сохранён: {output_path}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Генерирует HTML отчёт по групповой статистике компонентов")
    p.add_argument(
        "--report-dir",
        type=str,
        required=True,
        help="Путь к директории отчёта (содержит component_timings_grouped.csv)",
    )
    args = p.parse_args(argv)
    
    report_dir = Path(args.report_dir).resolve()
    grouped_csv = report_dir / "component_timings_grouped.csv"
    
    if not grouped_csv.exists():
        print(f"[ERROR] Файл не найден: {grouped_csv}")
        return
    
    grouped_rows = load_grouped_csv(grouped_csv)
    if not grouped_rows:
        print(f"[WARNING] Нет данных в {grouped_csv}")
        return
    
    output_html = report_dir / "component_timings_grouped_report.html"
    generate_grouped_html_report(grouped_rows, output_html)
    print(f"[SUCCESS] Отчёт создан: {output_html}")


if __name__ == "__main__":
    main()
