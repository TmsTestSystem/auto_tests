"""
HTML отчёт по GAP между соседними компонентами.

Источник: component_gaps.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="HTML отчёт по GAP между компонентами")
    p.add_argument("--report-dir", required=True)
    args = p.parse_args(argv)
    report_dir = Path(args.report_dir).resolve()

    rows = load_csv(report_dir / "component_gaps.csv")
    if not rows:
        print("[GAPS_REPORT] No component_gaps.csv rows")
        return

    # агрегируем по паре (from -> to): список gap_ms по прогонам
    by_pair: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for r in rows:
        f = r.get("from_component_title", "") or ""
        t = r.get("to_component_title", "") or ""
        g = r.get("gap_ms")
        try:
            gv = float(g)
        except Exception:
            continue
        by_pair[(f, t)].append(gv)

    # порядок: как впервые встретились в rows
    seen = set()
    pairs_order: List[Tuple[str, str]] = []
    for r in rows:
        key = (r.get("from_component_title", "") or "", r.get("to_component_title", "") or "")
        if key not in seen:
            seen.add(key)
            pairs_order.append(key)

    # данные для выбора
    pairs_json = []
    for (f, t) in pairs_order:
        gaps = by_pair.get((f, t), [])
        if not gaps:
            continue
        pairs_json.append({"from": f, "to": t, "gaps": gaps})

    html = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Component gaps</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 16px; }
    .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 12px; }
    th, td { border: 1px solid #eee; padding: 6px 8px; text-align: left; }
    th { background: #fafafa; position: sticky; top: 0; }
    select { min-width: 520px; padding: 6px 10px; border: 1px solid #e5e7eb; border-radius: 6px; }
  </style>
</head>
<body>
  <h1>GAP между соседними компонентами</h1>
  <div class="card">
    <p>Выбери пару соседних компонентов — увидишь m (gap_ms) по каждому прогону.</p>
    <div style="display:flex; gap: 12px; align-items:center; flex-wrap: wrap;">
      <label for="pairSelect"><strong>Пара:</strong></label>
      <select id="pairSelect"></select>
    </div>
    <div style="position: relative; height: 360px; width: 100%; margin-top: 14px;">
      <canvas id="chart"></canvas>
    </div>
  </div>

  <div class="card">
    <h2>Сырые записи (первые 200)</h2>
    <table>
      <thead><tr>
        <th>request_id</th><th>from</th><th>to</th><th>gap_ms</th>
      </tr></thead>
      <tbody>
"""
    for r in rows[:200]:
        html += (
            f"<tr><td><code>{(r.get('request_id') or '')[:8]}</code></td>"
            f"<td>{r.get('from_component_title','')}</td>"
            f"<td>{r.get('to_component_title','')}</td>"
            f"<td>{r.get('gap_ms','')}</td></tr>\n"
        )
    html += """      </tbody>
    </table>
  </div>

  <script>
    window.addEventListener('load', function() {
      if (typeof Chart === 'undefined') return;
      const pairs = """ + json.dumps(pairs_json, ensure_ascii=False) + """;
      const select = document.getElementById('pairSelect');
      const canvas = document.getElementById('chart');
      if (!select || !canvas) return;
      const ctx = canvas.getContext('2d');

      pairs.forEach((p, idx) => {
        const opt = document.createElement('option');
        opt.value = String(idx);
        opt.textContent = `${p.from} -> ${p.to}`;
        select.appendChild(opt);
      });

      let chart = null;
      function render(idx) {
        const p = pairs[idx];
        const labels = p.gaps.map((_, i) => `Run ${i+1}`);
        if (chart) chart.destroy();
        chart = new Chart(ctx, {
          type: 'line',
          data: { labels, datasets: [{ label: 'gap_ms', data: p.gaps, borderColor: 'rgba(16,185,129,1)', backgroundColor:'rgba(16,185,129,0.1)', fill: true, tension: 0.25 }]},
          options: { responsive: true, maintainAspectRatio: false, scales: { y: { title: { display: true, text: 'ms' }}}}
        });
      }
      select.addEventListener('change', (e) => render(Number(e.target.value)));
      render(0);
    });
  </script>
</body>
</html>"""

    out = report_dir / "component_gaps_report.html"
    out.write_text(html, encoding="utf-8")
    print(f"[GAPS_REPORT] Wrote {out}")


if __name__ == "__main__":
    main()

