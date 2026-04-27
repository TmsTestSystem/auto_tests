"""
UI-тест для проверки встроенного Python-интерпретатора через простую диаграмму
Input → Function → Output.

Подход:
- используем тот же проект, что и flow-тесты (fixture flow_project);
- перед запуском диаграммы импортируем один готовый Python-скрипт
  (scripts/math_functions.py) в проект через OpenAPI (`/files/import`);
- открываем диаграмму test_flow_component/test_func.df.json;
- выполняем её с функцией interpreter_diagnostics;
- проверяем:
  * что в консоли есть [PY_TIMER]-логи с duration_ms;
  * что Output настроен на $node.Function.result.
"""

import base64
import json
import os
import re
import time

import pytest
import requests
from playwright.sync_api import TimeoutError

from api.file_panel_api import FilePanelAPI
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.diagram_page import DiagramPage
from locators import FilePanelLocators, ComponentLocators
from conftest import (
    wait_for_canvas_with_refresh,
    get_api_base_url,
    get_auth_cookies,
    get_project_by_code,
)


def _ide_branch(page, project_code: str) -> str:
    """Ветка IDE: из URL (/branch/main|master) или из карточки проекта — иначе main."""
    u = getattr(page, "url", None) or ""
    m = re.search(r"/branch/([^/?#]+)", u)
    if m:
        return m.group(1)
    prj = get_project_by_code(project_code)
    if prj:
        b = prj.get("default_branch") or prj.get("defaultBranch")
        if b:
            return str(b)
    return "main"


def _select_math_functions_for_function_component(page) -> None:
    """
    В модалке выбора файла выбирает math_functions.py.
    Папку scripts не трогаем: в модалке она обычно уже раскрыта; лишний клик по папке может свернуть дерево.
    """
    timeout_ms = 20_000
    candidates = [
        page.locator(FilePanelLocators.get_treeitem_by_path("scripts/math_functions.py")),
        page.get_by_role("treeitem", name="/scripts/math_functions.py"),
        page.get_by_role("treeitem", name="math_functions.py"),
        page.locator(FilePanelLocators.get_treeitem_by_name("math_functions.py")),
        page.locator('[aria-label="treeitem_label"]').filter(has_text="math_functions.py"),
    ]
    last_err: Exception | None = None
    for loc in candidates:
        try:
            first = loc.first
            first.wait_for(state="visible", timeout=timeout_ms)
            if first.count() > 0:
                first.click()
                print("[PY_INT] Выбран math_functions.py в модалке")
                return
        except Exception as e:
            last_err = e
            continue
    raise TimeoutError(
        f"math_functions.py не найден в дереве модалки: {last_err!r}"
    ) from last_err


def _import_math_functions_via_api(project_code: str, *, page=None, branch: str | None = None) -> str:
    """
    Импортирует локальный scripts/math_functions.py в проект через OpenAPI.
    Скрипт кладётся по пути /scripts/math_functions.py в той же ветке, что открыта в IDE (main/master).

    Returns:
        Имя ветки, в которую писали (нужно для bps/call).
    """
    if branch is None:
        branch = _ide_branch(page, project_code)
    print(f"[PY_INT] Импорт math_functions в ветку API/IDE: {branch}")

    script_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "scripts",
        "math_functions.py",
    )
    with open(script_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("ascii")

    api = FilePanelAPI(project_code, branch=branch)
    
    # Создаём папку /scripts, если её нет
    try:
        api.create_folder("scripts", parent_path="/")
        print(f"[PY_INT] Папка /scripts создана через API")
    except requests.exceptions.HTTPError as e:
        if "already exists" in str(e) or (hasattr(e, 'response') and e.response.status_code == 409):
            print(f"[PY_INT] Папка /scripts уже существует")
        else:
            raise
    
    print(f"[PY_INT] Импортируем math_functions.py в проект {project_code} через API...")
    api.import_file("/scripts/math_functions.py", content_b64)
    return branch


def _get_output_data_field(page):
    field = page.get_by_role("textbox", name="inputs_config.data.value")
    if field.count() == 0:
        field = page.get_by_role("textbox", name="config.data")
    if field.count() == 0:
        field = page.locator(ComponentLocators.DATA_VALUE_FALLBACK)
    return field.first


def _patch_test_func_diagram_via_api(
    project_code: str,
    branch: str,
    process_path: str,
    output_value: str,
    function_inputs: dict | None = None,
) -> None:
    """Fallback for current UI builds where Output data field is hidden from Playwright."""
    api = FilePanelAPI(project_code, branch=branch)
    raw_content = api.get_file_content(process_path)
    diagram = json.loads(raw_content)

    output_patched = False
    function_patched = function_inputs is None
    for component in diagram.get("components", []):
        if component.get("title") == "Output":
            inputs_config = component.setdefault("inputs_config", {})
            data_config = inputs_config.setdefault("data", {})
            data_config["value"] = output_value
            output_patched = True
        elif component.get("title") == "Function" and function_inputs is not None:
            inputs_config = component.setdefault("inputs_config", {})
            for input_name, input_value in function_inputs.items():
                input_config = inputs_config.setdefault(input_name, {})
                input_config["value"] = input_value
            function_patched = True

    if not output_patched:
        raise AssertionError(f"Компонент Output не найден в {process_path}")
    if not function_patched:
        raise AssertionError(f"Компонент Function не найден в {process_path}")

    content = json.dumps(diagram, ensure_ascii=False, indent=2).encode("utf-8")
    api.import_file(process_path, base64.b64encode(content).decode("ascii"))
    print(f"[PY_INT] test_func.df.json обновлён через API: Output={output_value}")


FUNCS_TO_TEST = [
    "process_mixed_types",
    "interpreter_diagnostics",
    "cpu_stress",
    "traceback_demo",
    "big_structure",
    "timezone_demo",
    "recursion_demo",
]


@pytest.mark.ui
@pytest.mark.parametrize("func_name", FUNCS_TO_TEST)
def test_python_interpritator_flow(login_page, flow_project, func_name):
    """
    Базовая проверка Python-интерпретатора через диаграмму Input → Function → Output.

    Шаги:
    - открыть проект с test_flow_component;
    - открыть диаграмму test_func.df.json;
    - дождаться загрузки canvas;
    - выполнить диаграмму;
    - проверить, что:
        * в консоли есть логи от функции process_mixed_types из math_functions.py;
        * Output настроен на $node.Function.result.
    """
    page, project_code = flow_project
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    diagram_page = DiagramPage(page)

    print(f"[PY_INT] Проверяем Python-интерпретатор в проекте: {project_code}, функция: {func_name}")

    assert project_page.goto_project(project_code), f"Не удалось открыть проект {project_code}"
    time.sleep(2)

    # Импортируем scripts/math_functions.py в ту же ветку, что в URL IDE (иначе файл не виден в модалке)
    git_branch = _import_math_functions_via_api(project_code, page=page)

    # Открываем файловую панель и диаграмму test_func.df.json
    file_panel.open_file_panel()
    time.sleep(1)

    test_flow_component_folder = page.locator(FilePanelLocators.get_treeitem_by_name("test_flow_component"))
    assert test_flow_component_folder.count() > 0, "Папка 'test_flow_component' не найдена"
    test_flow_component_folder.first.click()
    time.sleep(1)

    test_func_file = page.locator(FilePanelLocators.get_treeitem_by_name("test_func.df.json"))
    assert test_func_file.count() > 0, "Файл 'test_func.df.json' не найден"
    test_func_file.first.dblclick()
    time.sleep(2)

    # Закрываем боковые панели, чтобы видеть canvas
    diagram_page.close_panels()
    time.sleep(1)

    # Ждём загрузки canvas с рефрешем
    assert wait_for_canvas_with_refresh(page, timeout=10000, max_refreshes=1), "Canvas не загрузился даже после рефреша"
    time.sleep(2)

    # 1) Настраиваем Function: скрипт + функция
    print(f"[PY_INT] Настраиваем компонент Function на вызов {func_name}")
    function_component = page.locator('text="Function"')
    assert function_component.count() > 0, "Компонент Function не найден на canvas"
    function_component.first.dblclick()
    time.sleep(1)

    # Привязываем к Function файл scripts/math_functions.py (как в test_flow_func)
    try:
        print("[PY_INT] Открываем модалку выбора Python скрипта")
        select_file_button = page.get_by_role("button", name="textfield_select_file_button")
        if select_file_button.is_visible():
            select_file_button.click()
            time.sleep(1)
            print("[PY_INT] Модалка выбора файла открыта")

            time.sleep(1.5)
            _select_math_functions_for_function_component(page)
            time.sleep(0.5)

            select_button = page.get_by_role("button", name="filemanager_select_button")
            assert select_button.is_visible(), "Кнопка выбора файла в модалке не найдена"
            select_button.click()
            time.sleep(1)
            print("[PY_INT] К компоненту Function привязан скрипт math_functions.py")
        else:
            print("[PY_INT][WARN] Кнопка выбора файла для Function не найдена")
    except Exception as e:
        pytest.fail(f"Не удалось привязать скрипт math_functions.py к Function: {e}")

    try:
        # Даем бэкенду подтянуть список функций из выбранного скрипта
        time.sleep(2)

        function_field = page.get_by_role("textbox", name="config.function")
        if not function_field.is_visible():
            pytest.fail("Поле config.function не отображается")

        # Открываем дропдаун с функциями: кликаем и, при необходимости, повторяем
        function_field.click()
        time.sleep(0.2)
        option = page.get_by_text(func_name, exact=False).first
        try:
            option.wait_for(state="visible", timeout=3000)
        except TimeoutError:
            # Дропдаун мог не открыться с первого клика — повторим
            function_field.click()
            time.sleep(0.2)
            option.wait_for(state="visible", timeout=3000)

        assert option.count() > 0, f"Функция {func_name} не найдена в списке доступных функций"
        option.click()
        time.sleep(0.5)
        print(f"[PY_INT] Функция {func_name} выбрана для компонента Function")
    except Exception as e:
        pytest.fail(f"Не удалось выбрать функцию {func_name}: {e}")

    # Если функция принимает аргументы (как process_mixed_types), заполняем их в Function
    if func_name == "process_mixed_types":
        print("[PY_INT] Заполняем аргументы для process_mixed_types")
        time.sleep(2)
        try:
            arg_a_field = page.get_by_role("textbox", name="inputs_config.a.value")
            if arg_a_field.is_visible():
                arg_a_field.click()
                time.sleep(0.5)
                arg_a_field.fill("42")
                # даём время на сохранение
                time.sleep(1.0)
                print("[PY_INT] Аргумент a (int): 42")
        except Exception as e:
            print(f"[PY_INT][WARN] Ошибка при заполнении аргумента a: {e}")

        try:
            arg_b_field = page.get_by_role("textbox", name="inputs_config.b.value")
            if arg_b_field.is_visible():
                arg_b_field.click()
                time.sleep(0.5)
                arg_b_field.fill('"Hello World"')
                time.sleep(1.0)
                print('[PY_INT] Аргумент b (str): "Hello World"')
        except Exception as e:
            print(f"[PY_INT][WARN] Ошибка при заполнении аргумента b: {e}")

        try:
            arg_c_field = page.get_by_role("textbox", name="inputs_config.c.value")
            if arg_c_field.is_visible():
                arg_c_field.click()
                time.sleep(0.5)
                arg_c_field.fill("3.14")
                time.sleep(1.0)
                print("[PY_INT] Аргумент c (float): 3.14")
        except Exception as e:
            print(f"[PY_INT][WARN] Ошибка при заполнении аргумента c: {e}")

        try:
            arg_d_field = page.get_by_role("textbox", name="inputs_config.d.value")
            if arg_d_field.is_visible():
                arg_d_field.click()
                time.sleep(0.5)
                arg_d_field.fill("true")
                time.sleep(1.0)
                print("[PY_INT] Аргумент d (bool): true")
        except Exception as e:
            print(f"[PY_INT][WARN] Ошибка при заполнении аргумента d: {e}")

        try:
            arg_e_field = page.get_by_role("textbox", name="inputs_config.e.value")
            if arg_e_field.is_visible():
                arg_e_field.click()
                time.sleep(0.5)
                arg_e_field.fill("[1, 2, 3, 4, 5]")
                # Даём бэку время сохранить последнее изменение
                time.sleep(1.5)
                print("[PY_INT] Аргумент e (list): [1, 2, 3, 4, 5]")
        except Exception as e:
            print(f"[PY_INT][WARN] Ошибка при заполнении аргумента e: {e}")

    # 2) Настраиваем Output до запуска диаграммы (точно как в test_flow_func)
    print("[PY_INT] Настраиваем компонент Output до запуска диаграммы")

    # Закрываем правый сайдбар (если открыт)
    try:
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher").first
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)
            print("[PY_INT] Правый сайдбар закрыт перед настройкой Output")
    except Exception as e:
        print(f"[PY_INT][WARN] Ошибка при закрытии правого сайдбара перед Output: {e}")

    # Кликаем по Output
    print("[PY_INT] Поиск и выбор компонента Output на canvas")
    output_component = page.locator('text="Output"')
    assert output_component.count() > 0, "Компонент Output не найден на canvas"
    output_component.first.click()
    time.sleep(1)

    # Открываем правый сайдбар для настройки Output
    print("[PY_INT] Открываем правый сайдбар для настройки Output")
    try:
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher").first
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)
            print("[PY_INT] Правый сайдбар открыт для настройки Output")
    except Exception as e:
        print(f"[PY_INT][WARN] Не удалось открыть правый сайдбар для Output: {e}")

    # Заполняем поле 'Данные'
    print("[PY_INT] Заполняем поле 'Данные' в Output значением $node.Function.result")
    function_inputs = None
    if func_name == "process_mixed_types":
        function_inputs = {
            "a": "42",
            "b": '"Hello World"',
            "c": "3.14",
            "d": "true",
            "e": "[1, 2, 3, 4, 5]",
        }
    try:
        data_field = _get_output_data_field(page)
        data_field.wait_for(state="visible", timeout=10000)
        data_field.fill("$node.Function.result")
        time.sleep(0.5)
        current_value = data_field.input_value()
        assert current_value.strip() == "$node.Function.result", (
            f"Ожидали '$node.Function.result' в поле данных Output, получили: {current_value!r}"
        )
        print("[PY_INT] Output настроен на $node.Function.result – результат Python-функции пробрасывается корректно")
        if function_inputs:
            _patch_test_func_diagram_via_api(
                project_code,
                git_branch,
                "/test_flow_component/test_func.df.json",
                "$node.Function.result",
                function_inputs,
            )
    except Exception as e:
        print(f"[PY_INT][WARN] Не удалось настроить поле 'Данные' через UI: {e}")
        _patch_test_func_diagram_via_api(
            project_code,
            git_branch,
            "/test_flow_component/test_func.df.json",
            "$node.Function.result",
            function_inputs,
        )
        page.reload(wait_until="networkidle")
        assert wait_for_canvas_with_refresh(page, timeout=10000, max_refreshes=1), (
            "Canvas не загрузился после API-настройки Output"
        )
        time.sleep(1)

    # Закрываем правый сайдбар перед запуском
    print("[PY_INT] Закрываем правый сайдбар перед запуском диаграммы")
    try:
        details_panel_switcher = page.get_by_role("button", name="diagram_details_panel_switcher").first
        if details_panel_switcher.is_visible():
            details_panel_switcher.click()
            time.sleep(1)
            print("[PY_INT] Правый сайдбар закрыт перед запуском")
    except Exception as e:
        print(f"[PY_INT][WARN] Ошибка при закрытии правого сайдбара перед запуском: {e}")

    # 3) Запускаем диаграмму и ждём успешного завершения
    diagram_wait_ms = 60_000
    if func_name in ("cpu_stress", "big_structure"):
        diagram_wait_ms = 300_000
    elif func_name in ("interpreter_diagnostics", "recursion_demo", "traceback_demo", "timezone_demo"):
        diagram_wait_ms = 120_000
    assert diagram_page.run_diagram(), "Диаграмма с Function не запустилась"
    assert diagram_page.wait_for_diagram_completion(timeout=diagram_wait_ms), (
        "Диаграмма с Function не завершилась"
    )
    print("[PY_INT] Диаграмма завершилась, результат будет проверен через API")

    # 4) Открываем панель вывода и вкладку "Консоль"
    # Несколько кнопок с одинаковым aria-label (Валидация / Консоль) — нужна именно «Консоль»
    try:
        console_toggle = page.locator(
            'button[aria-label="outputpanel_switch_button"][data-tooltip="Консоль"]'
        )
        if console_toggle.count() == 0:
            console_toggle = page.get_by_role("button", name="outputpanel_switch_button").nth(1)
        console_toggle.wait_for(state="visible", timeout=8000)
        console_toggle.click()
        time.sleep(1)
        print("[PY_INT] Панель вывода (Консоль) открыта")
    except Exception as e:
        print(f"[PY_INT][WARN] Не удалось открыть панель вывода: {e}")

    try:
        console_tab = page.get_by_text("Консоль")
        if console_tab.is_visible():
            console_tab.click()
            time.sleep(1)
            print("[PY_INT] Переключились на вкладку 'Консоль'")
    except Exception as e:
        print(f"[PY_INT][WARN] Не удалось переключиться на вкладку 'Консоль': {e}")

    # 5) Для функций, которые логируют тайминги, проверяем [PY_TIMER] в консоли
    if func_name in (
        "interpreter_diagnostics",
        "cpu_stress",
        "traceback_demo",
        "big_structure",
        "timezone_demo",
        "recursion_demo",
    ):
        try:
            time.sleep(2)
            console_output = page.locator(".OutputPanel__Body___ypo3o > div").first
            if not console_output.is_visible():
                console_output = page.locator('[class*="OutputPanel__Body"] > div').first
            if console_output.is_visible():
                console_text = console_output.text_content()
                print(f"[PY_INT] Текст консоли: {console_text}")
                assert "[PY_TIMER]" in console_text, "В консоли нет логов [PY_TIMER] от врапера выполнения Python-функций"
                assert "duration_ms=" in console_text, "В логах [PY_TIMER] нет duration_ms="
                print("[PY_INT] Консоль содержит логи [PY_TIMER] с временем выполнения Python-кода")
            else:
                pytest.fail("Консольный вывод не отображается")
        except Exception as e:
            pytest.fail(f"Ошибка при проверке консольного вывода: {e}")

    # 6) Дополнительно дёргаем процесс через OpenAPI и валидируем $node.Function.result
    print(f"[PY_INT] Вызываем процесс через OpenAPI для функции {func_name}")
    api_base = get_api_base_url()
    cookies = get_auth_cookies()

    process_path = "/test_flow_component/test_func.df.json"
    url = f"{api_base}/api/ide/{project_code}/branch/{git_branch}/bps/call?path={process_path}"

    # Тяжёлые функции — дольше считаются на бэкенде
    bps_timeout = 60
    if func_name in ("cpu_stress", "big_structure"):
        bps_timeout = 300
    elif func_name in ("interpreter_diagnostics", "recursion_demo", "traceback_demo", "timezone_demo"):
        bps_timeout = 120

    req_body = {
        "request_meta": {
            "object_id": "python_interpreter_check",
            "request_id": f"req_{func_name}",
            "tags": func_name,
        },
        # Диаграмма берет входы из Input-ноды, request_data ей не нужен
        "request_data": {},
    }

    resp = requests.post(url, json=req_body, cookies=cookies, verify=False, timeout=bps_timeout)
    print(f"[PY_INT] POST {url} -> {resp.status_code}: {resp.text[:500]}")
    assert resp.status_code == 200, f"Ожидали 200 от вызова процесса, получили {resp.status_code}: {resp.text}"

    resp_json = resp.json()
    assert resp_json.get("status") == "finished", f"Процесс завершился неуспешно: {resp_json}"

    result_data = ((resp_json.get("result") or {}).get("data")) or {}
    assert isinstance(result_data, dict), f"Ожидали dict в result.data, получили: {type(result_data)}"

    if func_name == "process_mixed_types":
        # Проверяем базовую структуру сложного объекта
        for key in ("integer_data", "string_data", "float_data", "boolean_data", "list_data", "summary"):
            assert key in result_data, f"В результате process_mixed_types нет ключа {key}: {result_data}"
        summary = result_data.get("summary") or {}
        assert summary.get("total_processed") == 5
        assert summary.get("has_collections") is True
        assert summary.get("has_primitives") is True
        print("[PY_INT] Ответ API для process_mixed_types успешно провалидирован")

    if func_name == "interpreter_diagnostics":
        # Проверяем, что все подпроверки отработали и overall_ok == True
        for key in ("simple_math", "imports_and_reuse", "heavy_cpu", "error_handling"):
            assert key in result_data, f"В результате interpreter_diagnostics нет ключа {key}: {result_data}"
            sub = result_data[key]
            assert isinstance(sub, dict) and "ok" in sub and "duration_ms" in sub, (
                f"Неверная структура блока {key}: {sub}"
            )
            assert sub["duration_ms"] >= 0, f"duration_ms для {key} должен быть неотрицательным"

        overall_ok = result_data.get("overall_ok")
        assert overall_ok is True, f"overall_ok должен быть True, получили: {overall_ok}"
        print("[PY_INT] Ответ API для interpreter_diagnostics успешно провалидирован")

    if func_name == "cpu_stress":
        # Структура такая же, как у _run_timed: ok/duration_ms/result/error
        for key in ("ok", "duration_ms", "result", "error"):
            assert key in result_data, f"В результате cpu_stress нет ключа {key}: {result_data}"
        assert result_data["ok"] is True, f"cpu_stress завершилась с ошибкой: {result_data}"
        assert result_data["duration_ms"] >= 0, (
            f"duration_ms для cpu_stress должен быть неотрицательным, получили: {result_data['duration_ms']}"
        )
        res = result_data.get("result") or {}
        assert isinstance(res, dict), f"Ожидали dict в result.result для cpu_stress, получили: {type(res)}"
        for key in ("sum_plain", "sum_squares", "approx", "hash_len", "count"):
            assert key in res, f"В результате cpu_stress.result нет ключа {key}: {res}"
        assert res["count"] == 10_000_000
        assert res["hash_len"] == 32  # длина sha256 в байтах
        print("[PY_INT] Ответ API для cpu_stress успешно провалидирован")

    if func_name == "traceback_demo":
        for key in ("ok", "duration_ms", "result", "error"):
            assert key in result_data, f"В результате traceback_demo нет ключа {key}: {result_data}"
        assert result_data["ok"] is True, f"traceback_demo завершилась с ошибкой: {result_data}"
        tb = (result_data.get("result") or {}).get("traceback")
        assert isinstance(tb, str) and "RuntimeError" in tb and "traceback demo" in tb, (
            f"В traceback_demo ожидаем текст traceback с RuntimeError, получили: {tb!r}"
        )
        print("[PY_INT] Ответ API для traceback_demo успешно провалидирован")

    if func_name == "big_structure":
        for key in ("ok", "duration_ms", "result", "error"):
            assert key in result_data, f"В результате big_structure нет ключа {key}: {result_data}"
        assert result_data["ok"] is True, f"big_structure завершилась с ошибкой: {result_data}"
        res = result_data.get("result") or {}
        assert isinstance(res, dict), f"Ожидали dict в result.result для big_structure, получили: {type(res)}"
        assert res.get("items_count", 0) >= 500_000, (
            f"items_count для big_structure слишком мал: {res.get('items_count')}"
        )
        assert isinstance(res.get("sample"), list) and len(res["sample"]) == 3, (
            f"В big_structure.sample ожидаем 3 элемента, получили: {res.get('sample')}"
        )
        print("[PY_INT] Ответ API для big_structure успешно провалидирован")

    if func_name == "timezone_demo":
        for key in ("ok", "duration_ms", "result", "error"):
            assert key in result_data, f"В результате timezone_demo нет ключа {key}: {result_data}"
        assert result_data["ok"] is True, f"timezone_demo завершилась с ошибкой: {result_data}"
        res = result_data.get("result") or {}
        assert isinstance(res, dict), f"Ожидали dict в result.result для timezone_demo, получили: {type(res)}"
        assert isinstance(res.get("utc_iso"), str) and "T" in res["utc_iso"], (
            f"Некорректный utc_iso в timezone_demo: {res.get('utc_iso')}"
        )
        assert isinstance(res.get("local_iso"), str) and "T" in res["local_iso"], (
            f"Некорректный local_iso в timezone_demo: {res.get('local_iso')}"
        )
        assert isinstance(res.get("delta_seconds"), (int, float)), "delta_seconds в timezone_demo должен быть числом"
        assert isinstance(res.get("utc_offset_seconds"), (int, float)), (
            "utc_offset_seconds в timezone_demo должен быть числом"
        )
        print("[PY_INT] Ответ API для timezone_demo успешно провалидирован")

    if func_name == "recursion_demo":
        for key in ("ok", "duration_ms", "result", "error"):
            assert key in result_data, f"В результате recursion_demo нет ключа {key}: {result_data}"
        assert result_data["ok"] is True, f"recursion_demo завершилась с ошибкой: {result_data}"
        res = result_data.get("result") or {}
        assert isinstance(res, dict), f"Ожидали dict в result.result для recursion_demo, получили: {type(res)}"
        depth = res.get("depth")
        total = res.get("sum")
        assert depth == 300, f"В recursion_demo ожидаем глубину 300, получили: {depth}"
        expected_sum = depth * (depth + 1) // 2
        assert total == expected_sum, (
            f"Неверная сумма в recursion_demo: ожидали {expected_sum}, получили: {total}"
        )
        print("[PY_INT] Ответ API для recursion_demo успешно провалидирован")


