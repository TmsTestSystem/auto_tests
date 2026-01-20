"""
HTML отчёт:
- График/таблица: как растёт время выполнения диаграммы от запроса к запросу

Источник: diagram_timings.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def load_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Генерация HTML отчёта по времени диаграммы")
    p.add_argument("--report-dir", required=True)
    args = p.parse_args(argv)
    report_dir = Path(args.report_dir).resolve()

    rows = load_csv(report_dir / "diagram_timings.csv")
    if not rows:
        print("[DIAGRAM_REPORT] No diagram_timings.csv rows")
        return

    labels = [f"Run {r.get('run_idx')}" for r in rows]
    durations = [float(r.get("diagram_duration_ms") or 0) for r in rows]
    gaps_sum = [float(r.get("gaps_sum_ms") or 0) for r in rows]
    comps_sum = [float(r.get("components_sum_ms") or 0) for r in rows]

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Diagram timings</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 16px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 12px; }}
    th, td {{ border: 1px solid #eee; padding: 6px 8px; text-align: left; }}
    th {{ background: #fafafa; position: sticky; top: 0; }}
  </style>
</head>
<body>
  <h1>Время выполнения диаграммы по прогонам</h1>
  <div class="card">
    <div style="position: relative; height: 360px; width: 100%;">
      <canvas id="chart"></canvas>
    </div>
  </div>

  <div class="card">
    <h2>Таблица (в порядке прогонов)</h2>
    <table>
      <thead>
        <tr>
          <th>run_idx</th>
          <th>request_id</th>
          <th>job_uuid</th>
          <th>diagram_duration_ms</th>
          <th>gaps_sum_ms</th>
          <th>components_sum_ms</th>
          <th>gaps_share_pct</th>
          <th>components_count</th>
        </tr>
      </thead>
      <tbody>
"""
    for r in rows:
        html += (
            f"<tr><td>{r.get('run_idx')}</td>"
            f"<td><code>{(r.get('request_id') or '')[:8]}</code></td>"
            f"<td><code>{(r.get('job_uuid') or '')[:8]}</code></td>"
            f"<td>{r.get('diagram_duration_ms')}</td>"
            f"<td>{r.get('gaps_sum_ms')}</td>"
            f"<td>{r.get('components_sum_ms')}</td>"
            f"<td>{r.get('gaps_share_pct')}</td>"
            f"<td>{r.get('components_count')}</td></tr>\n"
        )
    html += """      </tbody>
    </table>
  </div>

  <script>
    window.addEventListener('load', function() {
      if (typeof Chart === 'undefined') return;
      const labels = """ + json.dumps(labels, ensure_ascii=False) + """;
      const data = """ + json.dumps(durations, ensure_ascii=False) + """;
      const gaps = """ + json.dumps(gaps_sum, ensure_ascii=False) + """;
      const comps = """ + json.dumps(comps_sum, ensure_ascii=False) + """;
      const ctx = document.getElementById('chart').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: { labels, datasets: [
          { label: 'diagram_duration_ms', data, borderColor: 'rgba(59,130,246,1)', backgroundColor:'rgba(59,130,246,0.08)', fill: false, tension: 0.25 },
          { label: 'gaps_sum_ms', data: gaps, borderColor: 'rgba(16,185,129,1)', backgroundColor:'rgba(16,185,129,0.08)', fill: false, tension: 0.25 },
          { label: 'components_sum_ms', data: comps, borderColor: 'rgba(245,158,11,1)', backgroundColor:'rgba(245,158,11,0.08)', fill: false, tension: 0.25 },
        ]},
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, title: { display: true, text: 'ms' }}}}
      });
    });
  </script>
</body>
</html>"""

    out = report_dir / "diagram_timings_report.html"
    out.write_text(html, encoding="utf-8")
    print(f"[DIAGRAM_REPORT] Wrote {out}")


if __name__ == "__main__":
    main()

