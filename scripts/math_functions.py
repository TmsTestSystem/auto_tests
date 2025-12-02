import datetime
import hashlib
import json
import math
import random
import time
from typing import Any, Dict


def process_mixed_types(a: int, b: str, c: float, d: bool, e):
    """
    Функция для обработки разных типов данных
    Принимает аргументы разных типов: int, str, float, bool, list (без типизации)

    ВАЖНО: эта функция уже используется в UI‑тестах (test_flow_func),
    поэтому её поведение сохраняем как есть, чтобы не ломать существующие проверки.
    """
    print(f"[FUNCTION] Получены аргументы:")
    print(f"[FUNCTION] a (int): {a}")
    print(f"[FUNCTION] b (str): {b}")
    print(f"[FUNCTION] c (float): {c}")
    print(f"[FUNCTION] d (bool): {d}")
    print(f"[FUNCTION] e (list): {e}")
    
    result = {
        "integer_data": {
            "value": a,
            "type": "int",
            "processed": {
                "absolute": abs(a),
                "squared": a ** 2,
                "is_even": a % 2 == 0,
                "is_positive": a > 0,
                "factorial": 1 if a <= 1 else a * (a-1) if a <= 2 else "too_large"
            }
        },
        "string_data": {
            "value": b,
            "type": "str",
            "processed": {
                "length": len(b),
                "upper": b.upper(),
                "lower": b.lower(),
                "words": len(b.split()),
                "is_numeric": b.isdigit(),
                "reversed": b[::-1]
            }
        },
        "float_data": {
            "value": c,
            "type": "float",
            "processed": {
                "absolute": abs(c),
                "rounded": round(c, 2),
                "ceiling": int(c) + (1 if c > int(c) else 0),
                "floor": int(c),
                "is_whole": c == int(c)
            }
        },
        "boolean_data": {
            "value": d,
            "type": "bool",
            "processed": {
                "opposite": not d,
                "as_string": str(d),
                "as_number": 1 if d else 0,
                "as_int": int(d)
            }
        },
        "list_data": {
            "value": e,
            "type": "list",
            "processed": {
                "length": len(e),
                "sum": sum(e) if all(isinstance(x, (int, float)) for x in e) else None,
                "first": e[0] if len(e) > 0 else None,
                "last": e[-1] if len(e) > 0 else None,
                "reversed": e[::-1] if len(e) > 0 else []
            }
        },
        "summary": {
            "total_processed": 5,
            "types_processed": ["int", "str", "float", "bool", "list"],
            "has_collections": True,
            "has_primitives": True
        }
    }
    
    print(f"[FUNCTION] Результат обработки: {result}")
    return result


def _run_timed(func, *args, **kwargs) -> Dict[str, Any]:
    """
    Вспомогательный врапер для замера времени выполнения Python‑функций.
    Возвращает структуру:
    {
        "ok": bool,
        "duration_ms": float,
        "result": Any | None,
        "error": str | None
    }
    """
    start = time.perf_counter()
    try:
        res = func(*args, **kwargs)
        ok = True
        error = None
    except Exception as e:  # pragma: no cover - защитный код
        res = None
        ok = False
        error = repr(e)
    duration_ms = (time.perf_counter() - start) * 1000.0
    print(f"[PY_TIMER] func={func.__name__} ok={ok} duration_ms={duration_ms:.2f}")
    return {
        "ok": ok,
        "duration_ms": duration_ms,
        "result": res,
        "error": error,
    }


def _check_imports_and_reuse() -> bool:
    """Проверка базовых импортов и переиспользования функций/модулей."""
    # Импорты уже наверху файла, здесь просто используем
    data = {"x": 1, "y": [1, 2, 3], "ts": datetime.datetime.utcnow().isoformat()}
    dumped = json.dumps(data)
    loaded = json.loads(dumped)
    assert loaded["x"] == 1
    assert sum(loaded["y"]) == 6
    # math / random
    val = math.sqrt(16) + random.randint(0, 0)
    assert val == 4.0
    return True


def _heavy_cpu(n: int = 200_000) -> int:
    """Небольшая CPU‑нагрузка: считаем sha256 в цикле."""
    payload = b"x" * 1024
    h = payload
    for _ in range(n):
        h = hashlib.sha256(h).digest()
    # Возвращаем только длину хеша, чтобы не тащить бинарь
    return len(h)


def _simple_math() -> bool:
    """Простые математические проверки для smoke‑теста."""
    assert 1 + 1 == 2
    assert 2 ** 10 == 1024
    assert abs(-3.5) == 3.5
    return True


def interpreter_diagnostics() -> Dict[str, Any]:
    """
    Комплексная проверка Python‑интерпретатора.

    Покрывает:
    - базовую математику;
    - импорты и переиспользование модулей;
    - CPU‑нагруженный код;
    - обработку исключений.

    Возвращает структуру с таймингами и флагами ok/error, которую
    можно пробросить в Output через $node.Function.result.
    """
    results: Dict[str, Any] = {}

    results["simple_math"] = _run_timed(_simple_math)
    results["imports_and_reuse"] = _run_timed(_check_imports_and_reuse)
    results["heavy_cpu"] = _run_timed(_heavy_cpu, 50_000)

    def _raise_error():
        raise ValueError("intentional error")

    results["error_handling"] = _run_timed(_raise_error)

    results["overall_ok"] = all(
        v["ok"] for k, v in results.items() if k != "error_handling"
    )
    return results


def cpu_stress() -> Dict[str, Any]:
    """
    Явная нагрузочная функция для интерпретатора.

    Делает:
    - создаёт большой список чисел;
    - считает суммы и суммы квадратов через генераторы;
    - дополнительно гоняет sha256 в цикле через _heavy_cpu.

    Возвращает структуру такого же формата, как _run_timed:
    {
        "ok": bool,
        "duration_ms": float,
        "result": { ... агрегированные значения ... },
        "error": str | None
    }
    """

    def _workload() -> Dict[str, Any]:
        data = list(range(500_000))

        sum_plain = sum(data)
        sum_squares = sum(x * x for x in data)

        approx = 0.0
        for i in range(0, len(data), 250):
            approx += math.sqrt(data[i] + 1) * 0.5

        hash_len = _heavy_cpu(500_000)

        return {
            "sum_plain": sum_plain,
            "sum_squares": sum_squares,
            "approx": approx,
            "hash_len": hash_len,
            "count": len(data),
        }

    return _run_timed(_workload)