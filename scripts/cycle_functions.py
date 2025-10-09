"""
Функции для циклических операций
"""

def count_to_n(n):
    """
    Считает от 1 до n и возвращает список чисел
    """
    print(f"[CYCLE] Начинаем счет от 1 до {n}")
    result = []
    for i in range(1, n + 1):
        result.append(i)
        print(f"[CYCLE] Текущее значение: {i}")
    print(f"[CYCLE] Счет завершен, результат: {result}")
    return result

def factorial(n):
    """
    Вычисляет факториал числа n
    """
    print(f"[CYCLE] Вычисляем факториал для {n}")
    result = 1
    for i in range(1, n + 1):
        result *= i
        print(f"[CYCLE] Шаг {i}: {result}")
    print(f"[CYCLE] Факториал {n} = {result}")
    return result

def fibonacci(n):
    """
    Вычисляет n-ное число Фибоначчи
    """
    print(f"[CYCLE] Вычисляем {n}-ное число Фибоначчи")
    if n <= 1:
        return n
    
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, a + b
        print(f"[CYCLE] Шаг {i}: {b}")
    
    print(f"[CYCLE] {n}-ное число Фибоначчи = {b}")
    return b

def process_list_with_cycle(data_list):
    """
    Обрабатывает список данных в цикле
    """
    print(f"[CYCLE] Обрабатываем список: {data_list}")
    result = []
    for i, item in enumerate(data_list):
        processed_item = item * 2 if isinstance(item, (int, float)) else str(item).upper()
        result.append(processed_item)
        print(f"[CYCLE] Элемент {i}: {item} -> {processed_item}")
    
    print(f"[CYCLE] Обработка завершена, результат: {result}")
    return result

def while_loop_example(max_iterations):
    """
    Пример работы цикла while
    """
    print(f"[CYCLE] Запускаем while цикл до {max_iterations} итераций")
    counter = 0
    result = []
    
    while counter < max_iterations:
        counter += 1
        result.append(counter)
        print(f"[CYCLE] While итерация {counter}")
    
    print(f"[CYCLE] While цикл завершен, результат: {result}")
    return result
