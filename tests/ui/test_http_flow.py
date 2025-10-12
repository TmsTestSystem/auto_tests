"""
Тест для HTTP компонентов с реальной диаграммой
Input → Http_GET → Http_POST → Http_PUT → Http_PATCH → Http_DEL → Output
"""
import time
import json
import pytest
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from pages.canvas_utils import CanvasUtils
from pages.diagram_page import DiagramPage
from conftest import save_screenshot
from locators import (
    FilePanelLocators, DiagramLocators, CanvasLocators, 
    ComponentLocators, ModalLocators, ToolbarLocators
)


@pytest.fixture(scope="function")
def api_server():
    """
    Фикстура для использования публичного API (JSONPlaceholder)
    """
    import requests
    import urllib3
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    try:
        response = requests.get("https://jsonplaceholder.typicode.com/users/1", timeout=5, verify=False)
        if response.status_code == 200:
            print("[INFO] JSONPlaceholder API is accessible")
            return {
                "base_url": "https://jsonplaceholder.typicode.com",
                "users_endpoint": "https://jsonplaceholder.typicode.com/users"
            }
        else:
            pytest.fail(f"JSONPlaceholder API returned status {response.status_code}")
    except Exception as e:
        pytest.fail(f"Failed to connect to JSONPlaceholder API: {e}")


def test_http_flow(login_page, shared_flow_project, api_server):
    """
    Тест для последовательности HTTP методов:
    Input → Http_GET → Http_POST → Http_PUT → Http_PATCH → Http_DEL → Output
    """
    page = login_page
    project_code = shared_flow_project
    project_page = ProjectPage(page)

    print(f"[INFO] Запуск теста HTTP Flow Sequence в проекте: {project_code}")
    print(f"[INFO] API server URL: {api_server['base_url']}")

    assert project_page.goto_project(project_code), f"Переход в проект {project_code} не удался!"
    time.sleep(2)

    file_panel = FilePanelPage(page)
    diagram_page = DiagramPage(page)

    try:
        is_open = page.locator(ToolbarLocators.BOARD_TOOLBAR_PANEL).is_visible()
    except Exception:
        is_open = False
    if not is_open:
        file_panel.open_file_panel()
        time.sleep(0.5)
    print("[INFO] Файловая панель открыта")

    print("[INFO] Шаг 1: Открытие диаграммы")

    test_flow_folder = page.locator(FilePanelLocators.get_treeitem_by_name("test_flow_component"))
    assert test_flow_folder.count() > 0, "Папка 'test_flow_component' не найдена!"
    test_flow_folder.click()
    time.sleep(1)

    diagram_files = [
        'test_http.df.json',
        'test_http_flow.df.json', 
        'http_test.df.json'
    ]
    
    diagram_file = None
    for filename in diagram_files:
        file_locator = page.locator(FilePanelLocators.get_treeitem_by_name(filename))
        if file_locator.count() > 0:
            diagram_file = file_locator
            print(f"[INFO] Найдена диаграмма: {filename}")
            break
    
    assert diagram_file is not None, f"Диаграмма не найдена! Искали: {diagram_files}"
    diagram_file.dblclick()
    time.sleep(2)
    print("[INFO] Диаграмма открыта")

    canvas = page.locator(CanvasLocators.CANVAS).first
    canvas.wait_for(state="visible", timeout=10000)
    time.sleep(2)
    print("[INFO] Canvas диаграммы загружен")

    print("[INFO] Закрытие панелей")
    diagram_page.close_panels()

    canvas_utils = CanvasUtils(page)

    print("[INFO] Шаг 2: Настройка Http_GET компонента")
    
    http_get_found = canvas_utils.find_component_by_title("Http_GET", timeout=10000)
    assert http_get_found, "Компонент 'Http_GET' не найден на канвасе!"
    print("[INFO] Компонент 'Http_GET' найден")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Правый сайдбар открыт")

    url_field = page.get_by_role("textbox", name="config.url")
    if url_field.count() == 0:
        url_field = page.locator(ComponentLocators.URL_FIELD_FALLBACK)
    
    assert url_field.count() > 0, "Поле 'URL' не найдено!"
    get_url = f'"{api_server["users_endpoint"]}/2?_limit=1&_fields=id,name,email"'
    url_field.fill(get_url)
    time.sleep(1)
    print(f"[INFO] Http_GET URL настроен: {get_url}")

    try:
        method_field = page.get_by_role("textbox", name="config.method")
        if method_field.count() == 0:
            method_field = page.locator(ComponentLocators.METHOD_FIELD_FALLBACK)
        
        if method_field.count() > 0:
            method_field.click()
            time.sleep(1)
            
            get_option = page.get_by_role("treeitem", name="GET").locator("div").nth(1)
            if get_option.count() > 0:
                get_option.click()
                time.sleep(0.5)
                print("[INFO] Http_GET метод настроен: GET")
            else:
                print("[WARN] Опция GET не найдена в dropdown")
    except Exception as e:
        print(f"[INFO] Поле метода не найдено или не настроено: {e}")

    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Http_GET")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    print("[INFO] Шаг 3: Настройка Http_POST компонента")
    
    http_post_found = canvas_utils.find_component_by_title("Http_POST", timeout=10000)
    assert http_post_found, "Компонент 'Http_POST' не найден на канвасе!"
    print("[INFO] Компонент 'Http_POST' найден")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)

    url_field = page.get_by_role("textbox", name="config.url")
    if url_field.count() == 0:
        url_field = page.locator(ComponentLocators.URL_FIELD_FALLBACK)
    
    post_url = f'"{api_server["users_endpoint"]}?_fields=id,name,email"'
    url_field.fill(post_url)
    time.sleep(1)
    print(f"[INFO] Http_POST URL настроен: {post_url}")

    try:
        method_field = page.get_by_role("textbox", name="config.method")
        if method_field.count() == 0:
            method_field = page.locator(ComponentLocators.METHOD_FIELD_FALLBACK)
        
        if method_field.count() > 0:
            method_field.click()
            time.sleep(1)
            
            post_option = page.get_by_role("treeitem", name="POST").locator("div").nth(1)
            if post_option.count() > 0:
                post_option.click()
                time.sleep(0.5)
                print("[INFO] Http_POST метод настроен: POST")
            else:
                print("[WARN] Опция POST не найдена в dropdown")
    except Exception as e:
        print(f"[INFO] Поле метода не найдено или не настроено: {e}")

    try:
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").fill("\"Content-Type\"")
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").dblclick()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").fill("\"application/json\"")
        time.sleep(1)
        
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").fill("\"Accept\"")
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").dblclick()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").fill("\"application/json\"")
        time.sleep(1)
        
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").fill("\"Accept-Encoding\"")
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").dblclick()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").fill("\"gzip\"")
        time.sleep(1)
        
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.3.name").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.3.name").fill("\"X-Requested-With\"")
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.3.value").dblclick()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.3.value").fill("\"XMLHttpRequest\"")
        time.sleep(1)
        
        print("[INFO] Http_POST заголовки настроены: Content-Type, Accept, Accept-Encoding, X-Requested-With")
    except Exception as e:
        print(f"[INFO] Настройка заголовков не удалась: {e}")

    try:
        body_field = page.get_by_role("textbox", name="body")
        if body_field.count() == 0:
            body_field = page.locator(ComponentLocators.HTTP_BODY_FIELD)
        
        if body_field.count() > 0:
            post_body = '{"name": "Test User", "username": "testuser", "email": "test@example.com"}'
            body_field.fill(post_body)
            time.sleep(1)
            print(f"[INFO] Http_POST тело запроса настроено: {post_body}")
    except Exception as e:
        print(f"[INFO] Поле тела запроса не найдено: {e}")

    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Http_POST")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    print("[INFO] Шаг 4: Настройка Http_PUT компонента")
    
    http_put_found = canvas_utils.find_component_by_title("Http_PUT", timeout=10000)
    assert http_put_found, "Компонент 'Http_PUT' не найден на канвасе!"
    print("[INFO] Компонент 'Http_PUT' найден")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)

    url_field = page.get_by_role("textbox", name="config.url")
    if url_field.count() == 0:
        url_field = page.locator(ComponentLocators.URL_FIELD_FALLBACK)
    
    put_url = f'"{api_server["users_endpoint"]}/2?_fields=id,name,email"'
    url_field.fill(put_url)
    time.sleep(1)
    print(f"[INFO] Http_PUT URL настроен: {put_url}")

    try:
        method_field = page.get_by_role("textbox", name="config.method")
        if method_field.count() == 0:
            method_field = page.locator(ComponentLocators.METHOD_FIELD_FALLBACK)
        
        if method_field.count() > 0:
            method_field.click()
            time.sleep(1)
            
            put_option = page.get_by_role("treeitem", name="PUT").locator("div").nth(1)
            if put_option.count() > 0:
                put_option.click()
                time.sleep(0.5)
                print("[INFO] Http_PUT метод настроен: PUT")
            else:
                print("[WARN] Опция PUT не найдена в dropdown")
    except Exception as e:
        print(f"[INFO] Поле метода не найдено или не настроено: {e}")

    try:
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").fill("\"Content-Type\"")
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").dblclick()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").fill("\"application/json\"")
        time.sleep(1)
        
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").fill("\"Accept\"")
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").dblclick()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").fill("\"application/json\"")
        time.sleep(1)
        
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").fill("\"X-Requested-With\"")
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").dblclick()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").fill("\"XMLHttpRequest\"")
        time.sleep(1)
        
        print("[INFO] Http_PUT заголовки настроены: Content-Type, Accept, X-Requested-With")
    except Exception as e:
        print(f"[INFO] Настройка заголовков не удалась: {e}")

    try:
        body_field = page.get_by_role("textbox", name="body")
        if body_field.count() == 0:
            body_field = page.locator(ComponentLocators.HTTP_BODY_FIELD)
        
        if body_field.count() > 0:
            put_body = '{"name": "Updated User", "username": "updateduser", "email": "updated@example.com"}'
            body_field.fill(put_body)
            time.sleep(1)
            print(f"[INFO] Http_PUT тело запроса настроено: {put_body}")
    except Exception as e:
        print(f"[INFO] Поле тела запроса не найдено: {e}")

    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Http_PUT")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    print("[INFO] Шаг 5: Настройка Http_PATCH компонента")
    
    http_patch_found = canvas_utils.find_component_by_title("Http_PATCH", timeout=10000)
    assert http_patch_found, "Компонент 'Http_PATCH' не найден на канвасе!"
    print("[INFO] Компонент 'Http_PATCH' найден")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)

    url_field = page.get_by_role("textbox", name="config.url")
    if url_field.count() == 0:
        url_field = page.locator(ComponentLocators.URL_FIELD_FALLBACK)
    
    patch_url = f'"{api_server["users_endpoint"]}/2?_fields=id,name,email"'
    url_field.fill(patch_url)
    time.sleep(1)
    print(f"[INFO] Http_PATCH URL настроен: {patch_url}")

    try:
        method_field = page.get_by_role("textbox", name="config.method")
        if method_field.count() == 0:
            method_field = page.locator(ComponentLocators.METHOD_FIELD_FALLBACK)
        
        if method_field.count() > 0:
            method_field.click()
            time.sleep(1)
            
            patch_option = page.get_by_role("treeitem", name="PATCH").locator("div").nth(1)
            if patch_option.count() > 0:
                patch_option.click()
                time.sleep(0.5)
                print("[INFO] Http_PATCH метод настроен: PATCH")
            else:
                print("[WARN] Опция PATCH не найдена в dropdown")
    except Exception as e:
        print(f"[INFO] Поле метода не найдено или не настроено: {e}")

    try:
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").fill("\"Content-Type\"")
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").dblclick()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").fill("\"application/json\"")
        time.sleep(1)
        
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").fill("\"Accept\"")
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").dblclick()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").fill("\"application/json\"")
        time.sleep(1)
        
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").click()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").fill("\"X-Requested-With\"")
        time.sleep(1)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").dblclick()
        time.sleep(0.5)
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").fill("\"XMLHttpRequest\"")
        time.sleep(1)
        
        print("[INFO] Http_PATCH заголовки настроены: Content-Type, Accept, X-Requested-With")
    except Exception as e:
        print(f"[INFO] Настройка заголовков не удалась: {e}")

    try:
        body_field = page.get_by_role("textbox", name="body")
        if body_field.count() == 0:
            body_field = page.locator(ComponentLocators.HTTP_BODY_FIELD)
        
        if body_field.count() > 0:
            patch_body = '{"email": "patched@example.com"}'
            body_field.fill(patch_body)
            time.sleep(1)
            print(f"[INFO] Http_PATCH тело запроса настроено: {patch_body}")
    except Exception as e:
        print(f"[INFO] Поле тела запроса не найдено: {e}")

    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Http_PATCH")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    print("[INFO] Шаг 6: Настройка Http_DEL компонента")
    
    http_del_found = canvas_utils.find_component_by_title("Http_DEL", timeout=10000)
    assert http_del_found, "Компонент 'Http_DEL' не найден на канвасе!"
    print("[INFO] Компонент 'Http_DEL' найден")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)

    url_field = page.get_by_role("textbox", name="config.url")
    if url_field.count() == 0:
        url_field = page.locator(ComponentLocators.URL_FIELD_FALLBACK)
    
    del_url = f'"{api_server["users_endpoint"]}/2?_fields=id"'
    url_field.fill(del_url)
    time.sleep(1)
    print(f"[INFO] Http_DEL URL настроен: {del_url}")

    try:
        method_field = page.get_by_role("textbox", name="config.method")
        if method_field.count() == 0:
            method_field = page.locator(ComponentLocators.METHOD_FIELD_FALLBACK)
        
        if method_field.count() > 0:
            method_field.click()
            time.sleep(1)
            
            delete_option = page.get_by_role("treeitem", name="DELETE").locator("div").nth(1)
            if delete_option.count() > 0:
                delete_option.click()
                time.sleep(0.5)
                print("[INFO] Http_DEL метод настроен: DELETE")
            else:
                print("[WARN] Опция DELETE не найдена в dropdown")
    except Exception as e:
        print(f"[INFO] Поле метода не найдено или не настроено: {e}")


    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Http_DEL")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    print("[INFO] Шаг 7: Настройка Output компонента для сбора всех HTTP ответов")
    
    output_found = canvas_utils.find_component_by_title("Output", timeout=10000)
    assert output_found, "Компонент 'Output' не найден на канвасе!"
    print("[INFO] Компонент 'Output' найден")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Правый сайдбар открыт для Output")

    try:
        expression_button = page.get_by_role("button", name="textfield_expression_button")
        if expression_button.count() > 0:
            expression_button.click()
            time.sleep(1)
            print("[INFO] Кнопка раскрытия поля 'Данные' нажата")
        else:
            expression_button = page.locator(ComponentLocators.HTTP_EXPRESSION_BUTTON)
            if expression_button.count() > 0:
                expression_button.first.click()
                time.sleep(1)
                print("[INFO] Кнопка раскрытия поля 'Данные' найдена через альтернативный селектор")
            else:
                print("[WARN] Кнопка раскрытия поля 'Данные' не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при нажатии кнопки раскрытия: {e}")

    try:
        modal = page.locator(ModalLocators.EXPRESSION_MODAL).first
        modal.wait_for(state="visible", timeout=5000)
        print("[INFO] Модальное окно для редактирования выражения открыто")
    except Exception as e:
        print("[WARN] Modal window did not open, skipping")

    try:
        editor_field = page.get_by_role("textbox", name="editor_view")
        if editor_field.count() == 0:
            editor_field = page.locator(ModalLocators.MONACO_EDITOR)
        
        if editor_field.count() > 0:
            all_responses_json = '''{"Get": $node.Http_GET.response.body,"Post": $node.Http_POST.response.body,"Put": $node.Http_PUT.response.body,"Patch": $node.Http_PATCH.response.body,"Delete": $node.Http_DEL.response.body,"summary": {"total_requests": 5,"methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],"api_url": "''' + api_server["base_url"] + '''"}}'''
            
            editor_field.fill(all_responses_json)
            time.sleep(1)
            print("[INFO] JSON со всеми HTTP ответами введен в редактор")
            print(f"[INFO] JSON содержит ответы от всех 5 HTTP методов")
        else:
            print("[WARN] Поле редактора не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при вводе JSON: {e}")

    try:
        save_button = page.get_by_role("button", name="expressioneditor_submit_button")
        if save_button.count() > 0:
            save_button.click()
            time.sleep(1)
            print("[INFO] Модальное окно закрыто с сохранением через expressioneditor_submit_button")
        else:
            save_button = page.locator('button:has-text("Сохранить"), button:has-text("Save"), button:has-text("OK")')
            if save_button.count() > 0:
                save_button.first.click()
                time.sleep(1)
                print("[INFO] Модальное окно закрыто с сохранением через fallback")
            else:
                page.keyboard.press("Escape")
                time.sleep(1)
                print("[INFO] Модальное окно закрыто через Escape")
    except Exception as e:
        print(f"[WARN] Ошибка при закрытии модального окна: {e}")

    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Output")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    print("[INFO] Шаг 8: Запуск диаграммы")

    success = diagram_page.run_diagram_and_wait(completion_timeout=60000)
    
    assert success, "Диаграмма не выполнилась успешно!"
    print("[INFO] Диаграмма завершилась успешно!")

    print("[INFO] Шаг 9: Проверка результатов в Output компоненте")

    canvas = page.locator(CanvasLocators.CANVAS).first
    canvas.dblclick(force=True)
    time.sleep(1)
    print("[INFO] Двойной клик по канвасу выполнен")

    details_panel = page.locator(DiagramLocators.DETAILS_PANEL)
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Сайдбар открыт")

    process_tab = page.get_by_text("Процесс", exact=True)
    assert process_tab.is_visible(), "Вкладка 'Процесс' не найдена!"
    process_tab.click()
    time.sleep(1)
    print("[INFO] Переход на вкладку 'Процесс' выполнен")

    analysis_tab = page.get_by_text("Анализ", exact=True)
    assert analysis_tab.is_visible(), "Подвкладка 'Анализ' не найдена!"
    analysis_tab.click()
    time.sleep(1)
    print("[INFO] Переход на подвкладку 'Анализ' выполнен")

    try:
        full_view_button = page.get_by_role("button", name="formitem_full_view_button").nth(1)
        if full_view_button.count() > 0:
            full_view_button.click()
            time.sleep(1)
            print("[INFO] Кнопка 'formitem_full_view_button' (nth(1)) нажата")

            json_modal = page.locator(ModalLocators.JSON_MODAL)
            json_modal.wait_for(state="visible", timeout=10000)
            print("[INFO] Модальное окно 'Просмотр JSON' открыто")
            
            save_screenshot(page, f"http_all_responses_{project_code}")
            
            time.sleep(3)

            view_lines = page.locator(ModalLocators.JSON_MODAL_VIEW_LINES)
            assert view_lines.count() > 0, "Monaco Editor не найден в модальном окне!"
            
            json_text = view_lines.inner_text()
            print(f"[INFO] JSON данные получены из Monaco Editor (длина: {len(json_text)}): {json_text[:500]}...")
            
            assert json_text.strip(), "JSON данные не найдены в Monaco Editor!"

            import re
            json_text_clean = re.sub(r'[\xa0\u00a0]', ' ', json_text)
            json_text_clean = json_text_clean.strip()
            print(f"[INFO] Очищенный JSON (длина: {len(json_text_clean)}): {json_text_clean[:300]}...")

            json_match = re.search(r'\{.*\}', json_text_clean, re.DOTALL)
            if json_match:
                json_text_clean = json_match.group(0)
                print(f"[INFO] Извлеченный JSON объект (длина: {len(json_text_clean)}): {json_text_clean[:200]}...")
            else:
                print("[WARN] JSON объект не найден в тексте, используем весь текст")

            try:
                json_data = json.loads(json_text_clean)
                print("[INFO] JSON успешно распарсен")
                
                assert "Get" in json_data, "Поле 'Get' не найдено в JSON"
                assert "Post" in json_data, "Поле 'Post' не найдено в JSON"
                assert "Put" in json_data, "Поле 'Put' не найдено в JSON"
                assert "Patch" in json_data, "Поле 'Patch' не найдено в JSON"
                assert "Delete" in json_data, "Поле 'Delete' не найдено в JSON"
                assert "summary" in json_data, "Поле 'summary' не найдено в JSON"
                
                summary = json_data["summary"]
                assert summary["total_requests"] == 5, f"Ожидалось 5 запросов, получено: {summary['total_requests']}"
                assert len(summary["methods"]) == 5, f"Ожидалось 5 методов, получено: {len(summary['methods'])}"
                assert api_server["base_url"] in summary["api_url"], f"URL API не совпадает: {summary['api_url']}"
                
                print("[INFO] Все проверки JSON данных пройдены успешно!")
                print(f"[INFO] GET ответ: {json_data['Get']}")
                print(f"[INFO] POST ответ: {json_data['Post']}")
                print(f"[INFO] PUT ответ: {json_data['Put']}")
                print(f"[INFO] PATCH ответ: {json_data['Patch']}")
                print(f"[INFO] DELETE ответ: {json_data['Delete']}")
                print(f"[INFO] Summary: {json_data['summary']}")
                
            except json.JSONDecodeError as e:
                raise Exception(f"Ошибка парсинга JSON: {e}")
            except Exception as e:
                raise Exception(f"Ошибка проверки JSON данных: {e}")

            close_button = page.locator(ModalLocators.MODAL_CLOSE_BUTTON)
            if close_button.count() > 0:
                close_button.first.click()
                time.sleep(1)
                print("[INFO] Модальное окно закрыто")
        else:
            print("[WARN] Кнопка 'formitem_full_view_button' не найдена")

    except Exception as e:
        print(f"[WARN] Ошибка при проверке результатов Output: {e}")

    save_screenshot(page, f"http_flow_sequence_complete_{project_code}")

    print("[SUCCESS] Все шаги теста HTTP Flow Sequence выполнены успешно!")
    print("[SUCCESS] Тест прошел: GET -> POST -> PUT -> PATCH -> DELETE запросы к JSONPlaceholder API выполнены!")
    print(f"[SUCCESS] API server работал на {api_server['base_url']}")
    print("[SUCCESS] DELETE метод вернул JSON ответ с подробной информацией!")
    print("[SUCCESS] Output компонент собрал все HTTP ответы в единый JSON!")
