def process_mixed_types(a: int, b: str, c: float, d: bool, e):
    """
    Функция для обработки разных типов данных
    Принимает аргументы разных типов: int, str, float, bool, list (без типизации)
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