import argparse
import datetime as dt
import os
import pathlib
import subprocess
import sys

BASE_DIR = pathlib.Path(__file__).parent.resolve()
PROJ_DIR = BASE_DIR.parent.resolve()
DEFAULT_COMPARE = PROJ_DIR / "compare_jobs_vs_events.py"


def find_compare_script() -> pathlib.Path:
    candidates = [
        DEFAULT_COMPARE,
        BASE_DIR / "compare_jobs_vs_events.py",
        PROJ_DIR / "compare_jobs_vs_events.py",
    ]
    for p in candidates:
        if p.exists():
            return p
    # Fallback: search recursively up to project root
    for p in PROJ_DIR.rglob("compare_jobs_vs_events.py"):
        return p
    raise FileNotFoundError("compare_jobs_vs_events.py not found in project. Place it at project root.")


def run(users: int, spawn_rate: int, duration_sec: int, host: str) -> None:
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = BASE_DIR / "reports" / ts
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Run Locust with HTML report
    cmd = [
        "locust",
        "-f",
        str(BASE_DIR / "locustfile.py"),
        "--headless",
        "-u",
        str(users),
        "-r",
        str(spawn_rate),
        "-t",
        f"{duration_sec}s",
        "--host",
        host,
        "--only-summary",
        "--html",
        str(out_dir / "locust_report.html"),
    ]
    subprocess.run(cmd, cwd=str(BASE_DIR), check=True)

    # 2) Generate comparison report into the same folder
    compare_script = find_compare_script()
    env = os.environ.copy()
    env["BASE_DIR"] = str(BASE_DIR)
    env["REPORT_DIR"] = str(out_dir)
    # Hidden default filters for compact report; adjustable here without CLI flags
    default_args = [
        "--bucket-ms", "20",
        "--samples-per-bucket", "3",
        "--limit", "500",
        # Example: keep both deltas columns by default; columns arg optional
        # "--columns", "request_id,delta_started_at_vs_object_id_ms,delta_finished_at_vs_response_end_ms,started_at,object_id,finished_at,response_end,job_duration",
    ]
    subprocess.run([sys.executable, str(compare_script), *default_args], cwd=str(BASE_DIR), env=env, check=True)

    print(f"Done. Reports: {out_dir}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Run locust load and generate comparison report")
    p.add_argument("--users", "-u", type=int, default=100, help="Concurrent users")
    p.add_argument("--spawn-rate", "-r", type=int, default=50, help="Spawn rate")
    p.add_argument("--duration", "-t", type=int, default=60, help="Duration in seconds")
    p.add_argument("--host", "-H", type=str, default="http://192.168.0.7:3333", help="Target host")
    args = p.parse_args(argv)
    run(args.users, args.spawn_rate, args.duration, args.host)



if __name__ == "__main__":
    main()
