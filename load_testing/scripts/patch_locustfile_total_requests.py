from __future__ import annotations

from pathlib import Path


def main() -> None:
    p = Path(__file__).resolve().parents[2] / "load_testing" / "locustfile.py"
    s = p.read_text(encoding="utf-8")

    # 1) add Semaphore import block after locust import
    needle = "from locust import HttpUser, task, between, events\n"
    block = (
        needle
        + "\n# Locust uses gevent; protect shared counters\n"
        + "try:\n"
        + "    from gevent.lock import Semaphore  # type: ignore\n"
        + "except Exception:  # pragma: no cover\n"
        + "    from threading import Lock as Semaphore  # type: ignore\n"
    )
    if needle in s and "protect shared counters" not in s:
        s = s.replace(needle, block, 1)

    # 2) add TOTAL_REQUESTS logic after LOAD_PROCESS_PATH
    needle2 = 'LOAD_PROCESS_PATH = os.getenv("LOAD_PROCESS_PATH", "test_que/test_1.df.json")\n'
    block2 = (
        needle2
        + "\n# Остановка теста по количеству выполненных запросов (а не по времени)\n"
        + 'TOTAL_REQUESTS_LIMIT = int(os.getenv("TOTAL_REQUESTS", "0") or "0")  # 0 = без лимита\n'
        + "_requests_done = 0\n"
        + "_requests_lock = Semaphore()\n\n\n"
        + "def _maybe_stop_runner(environment) -> None:\n"
        + "    if TOTAL_REQUESTS_LIMIT <= 0:\n"
        + "        return\n"
        + "    runner = getattr(environment, \"runner\", None)\n"
        + "    if runner is None:\n"
        + "        return\n"
        + "    try:\n"
        + "        runner.quit()\n"
        + "    except Exception:\n"
        + "        pass\n"
    )
    if needle2 in s and "TOTAL_REQUESTS_LIMIT" not in s:
        s = s.replace(needle2, block2, 1)

    # 3) increment counter after response JSON parsing, before requests.csv write
    needle3 = (
        "            except Exception:\n"
        "                # Не JSON — пропускаем\n"
        "                pass\n\n"
        "            # Запись в CSV для последующей корреляции данных\n"
    )
    block3 = (
        "            except Exception:\n"
        "                # Не JSON — пропускаем\n"
        "                pass\n\n"
        "            # Счётчик запросов и остановка по лимиту\n"
        "            if TOTAL_REQUESTS_LIMIT > 0:\n"
        "                global _requests_done\n"
        "                with _requests_lock:\n"
        "                    _requests_done += 1\n"
        "                    if _requests_done >= TOTAL_REQUESTS_LIMIT:\n"
        "                        _maybe_stop_runner(self.environment)\n\n"
        "            # Запись в CSV для последующей корреляции данных\n"
    )
    if needle3 in s and "Счётчик запросов" not in s:
        s = s.replace(needle3, block3, 1)

    p.write_text(s, encoding="utf-8")
    print(f"Patched: {p}")


if __name__ == "__main__":
    main()

