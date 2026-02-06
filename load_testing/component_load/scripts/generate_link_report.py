"""
Генератор HTML отчёта по link_event (link_events.csv).

Показывает:
- агрегированную таблицу по path и статусам
- график количества link_event по запросам (request_id)
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List


def load_link_events(csv_path: Path) -> List[Dict[str, Any]]:
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def generate_link_html_report(rows: List[Dict[str, Any]], output_path: Path) -> None:
    # агрегаты по path и длительности
    by_path_total: Counter[str] = Counter()
    by_path_status: Dict[str, Counter[str]] = defaultdict(Counter)
    by_path_durations: Dict[str, List[float]] = defaultdict(list)

    # по request_id — средняя длительность всех link'ов
    by_request_durations: Dict[str, List[float]] = defaultdict(list)

    for r in rows:
        path = (r.get("path") or "").strip() or "(empty)"
        status_start = (r.get("status_start") or "").strip() or "(empty)"
        rid = (r.get("request_id") or "").strip() or "(empty)"

        by_path_total[path] += 1
        by_path_status[path][status_start] += 1

        dur_raw = r.get("duration_ms") or ""
        try:
            dur = float(dur_raw) if str(dur_raw).strip() != "" else None
        except Exception:
            dur = None

        if dur is not None:
            by_path_durations[path].append(dur)
            by_request_durations[rid].append(dur)

    # таблица по path (в порядке убывания total)
    table_paths = []
    all_statuses = sorted({s for c in by_path_status.values() for s in c.keys()})
    for path, total in by_path_total.most_common():
        status_counts = by_path_status[path]
        durs = by_path_durations.get(path, [])
        if durs:
            avg_d = sum(durs) / len(durs)
            min_d = min(durs)
            max_d = max(durs)
        else:
            avg_d = min_d = max_d = None
        row = {
            "path": path,
            "total": total,
            "statuses": {s: status_counts.get(s, 0) for s in all_statuses},
            "avg_ms": avg_d,
            "min_ms": min_d,
            "max_ms": max_d,
        }
        table_paths.append(row)

    # график по request_id (средняя длительность link'ов в запросе)
    request_order: List[str] = []
    for r in rows:
        rid = (r.get("request_id") or "").strip() or "(empty)"
        if rid not in request_order:
            request_order.append(rid)
    chart_labels = [rid[:8] if rid != "(empty)" else rid for rid in request_order]
    chart_values: List[float] = []
    for rid in request_order:
        durs = by_request_durations.get(rid, [])
        if durs:
            chart_values.append(sum(durs) / len(durs))
        else:
            chart_values.append(0.0)

    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Link events report</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 16px; background: #f9fafb; }}
    h1 {{ color: #111827; margin-bottom: 8px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; background: white; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 12px; }}
    th, td {{ border: 1px solid #e5e7eb; padding: 8px 10px; text-align: left; }}
    th {{ background: #f9fafb; position: sticky; top: 0; font-weight: 600; color: #374151; }}
    tr:nth-child(even) {{ background: #fafafa; }}
    tr:hover {{ background: #f3f4f6; }}
    .muted {{ color: #6b7280; font-size: 12px; }}
    .chart-container {{ position: relative; height: 320px; width: 100%; }}
    code {{ font-size: 11px; }}
  </style>
</head>
<body>
  <h1>Link events (link_event) отчёт</h1>
  <p class="muted">Источник: <code>link_events.csv</code>. Всего уникальных link по job: <b>{len(rows)}</b>.</p>

  <div class="card">
    <h2>График: средняя длительность link_event по запросам</h2>
    <p class="muted">Ось X — request_id (первые 8 символов), Y — среднее время выполнения link'ов (ms) в этом запросе.</p>
    <div class="chart-container">
      <canvas id="linksByRequest"></canvas>
    </div>
  </div>

  <div class="card">
    <h2>Таблица: распределение link_event по path, статусам и времени выполнения</h2>
    <table>
      <thead>
        <tr>
          <th>path</th>
          <th>total</th>
          {''.join([f'<th>status={s}</th>' for s in all_statuses])}
          <th>avg_ms</th>
          <th>min_ms</th>
          <th>max_ms</th>
        </tr>
      </thead>
      <tbody>
"""

    for r in table_paths:
        html_content += f"<tr><td><code>{r['path']}</code></td><td>{r['total']}</td>"
        for s in all_statuses:
            html_content += f"<td>{r['statuses'][s]}</td>"
        if r["avg_ms"] is not None:
            html_content += f"<td>{r['avg_ms']:.3f}</td><td>{r['min_ms']:.3f}</td><td>{r['max_ms']:.3f}</td>"
        else:
            html_content += "<td>—</td><td>—</td><td>—</td>"
        html_content += "</tr>\n"

    html_content += """      </tbody>
    </table>
  </div>

"""
    
    # Показываем детальные данные по каждой линке (ограничиваем до 1000 для производительности браузера)
    detail_rows = rows[:1000]
    
    html_content += f"""  <div class="card">
    <h2>Детальная таблица: время выполнения каждой линки</h2>
    <p class="muted">Показано {len(detail_rows)} из {len(rows)} линков. Для удобства просмотра таблица ограничена первыми 1000 записями. Полные данные доступны в CSV.</p>
    <p class="muted"><strong>duration_ms</strong> - реальное время работы стрелки (от окончания from_component до начала to_component). <strong>duration_from_events_ms</strong> - время из событий link_event (может включать задержки).</p>
    <table>
      <thead>
        <tr>
          <th>#</th>
          <th>request_id</th>
          <th>link_key</th>
          <th>path</th>
          <th>from_component</th>
          <th>from_duration_ms</th>
          <th>to_component</th>
          <th>to_duration_ms</th>
          <th>link_duration_ms</th>
          <th>link_from_events_ms</th>
          <th>status_start</th>
          <th>status_end</th>
        </tr>
      </thead>
      <tbody>
"""
    
    for i, r in enumerate(detail_rows, 1):
        request_id = (r.get("request_id") or "").strip()
        link_key = (r.get("link_key") or "").strip()
        path = (r.get("path") or "").strip()
        from_component = (r.get("from_component") or "").strip()
        to_component = (r.get("to_component") or "").strip()
        from_duration = (r.get("from_component_duration_ms") or "").strip()
        to_duration = (r.get("to_component_duration_ms") or "").strip()
        status_start = (r.get("status_start") or "").strip()
        status_end = (r.get("status_end") or "").strip()
        duration_ms = (r.get("duration_ms") or "").strip()
        duration_from_events = (r.get("duration_from_events_ms") or "").strip()
        
        # Вычисляем процент от времени компонентов для анализа
        try:
            link_dur = float(duration_ms) if duration_ms else None
            from_dur = float(from_duration) if from_duration else None
            to_dur = float(to_duration) if to_duration else None
            events_dur = float(duration_from_events) if duration_from_events else None
            
            # Подсветка, если время стрелки подозрительно большое
            link_class = ""
            if link_dur and from_dur:
                ratio = (link_dur / from_dur) * 100 if from_dur > 0 else 0
                if ratio > 50:
                    link_class = "duration-high"
                elif ratio > 20:
                    link_class = "duration-medium"
            
            events_class = ""
            if events_dur and from_dur:
                ratio = (events_dur / from_dur) * 100 if from_dur > 0 else 0
                if ratio > 50:
                    events_class = "duration-high"
                elif ratio > 20:
                    events_class = "duration-medium"
        except (ValueError, TypeError):
            link_class = ""
            events_class = ""
        
        html_content += f"""        <tr>
          <td>{i}</td>
          <td><code style="font-size: 10px;">{request_id[:8] if request_id else ""}</code></td>
          <td><code style="font-size: 10px;">{link_key[:8] if link_key else ""}</code></td>
          <td><code>{path}</code></td>
          <td><code>{from_component or "—"}</code></td>
          <td>{from_duration or "—"}</td>
          <td><code>{to_component or "—"}</code></td>
          <td>{to_duration or "—"}</td>
          <td class="{link_class}"><strong>{duration_ms if duration_ms else "—"}</strong></td>
          <td class="{events_class}">{duration_from_events if duration_from_events else "—"}</td>
          <td>{status_start or "—"}</td>
          <td>{status_end or "—"}</td>
        </tr>
"""

    html_content += """      </tbody>
    </table>
  </div>

  <script>
    window.addEventListener('load', function() {
      if (typeof Chart === 'undefined') return;
      const labels = %LABELS%;
      const values = %VALUES%;
      const ctx = document.getElementById('linksByRequest').getContext('2d');
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels,
          datasets: [{
            label: 'link_event count',
            data: values,
            backgroundColor: 'rgba(59, 130, 246, 0.35)',
            borderColor: 'rgba(59, 130, 246, 1)',
            borderWidth: 1,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: { ticks: { maxRotation: 45, minRotation: 0 } },
            y: { beginAtZero: true, title: { display: true, text: 'count' } }
          }
        }
      });
    });
  </script>
</body>
</html>
"""

    html_content = html_content.replace("%LABELS%", json.dumps(chart_labels, ensure_ascii=False))
    html_content = html_content.replace("%VALUES%", json.dumps(chart_values, ensure_ascii=False))

    with output_path.open("w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"[LINK_REPORT] HTML отчёт сохранён: {output_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Генерация HTML отчёта по link_event")
    p.add_argument("--report-dir", type=str, required=True, help="Директория с отчётами")
    args = p.parse_args()

    report_dir = Path(args.report_dir)
    csv_path = report_dir / "link_events.csv"
    out_path = report_dir / "link_events_report.html"

    rows = load_link_events(csv_path)
    if not rows:
        print(f"[LINK_REPORT] Файл пуст или не найден: {csv_path}")
        return
    generate_link_html_report(rows, out_path)


if __name__ == "__main__":
    main()

