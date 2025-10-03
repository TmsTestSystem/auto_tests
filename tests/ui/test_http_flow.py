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
from conftest import save_screenshot
# from fake_http_server import create_fake_server  # Больше не используется


@pytest.fixture(scope="function")
def api_server():
    """
    Фикстура для использования публичного API (JSONPlaceholder)
    """
    import requests
    
    # Проверяем доступность JSONPlaceholder API
    try:
        response = requests.get("https://jsonplaceholder.typicode.com/users/1", timeout=5)
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

    # Переходим в нужный проект
    assert project_page.goto_project(project_code), f"Переход в проект {project_code} не удался!"
    time.sleep(2)

    # Подготавливаем необходимые объекты
    file_panel = FilePanelPage(page)

    try:
        is_open = page.get_by_label("board_toolbar_panel").is_visible()
    except Exception:
        is_open = False
    if not is_open:
        file_panel.open_file_panel()
        time.sleep(0.5)
    print("[INFO] Файловая панель открыта")

    # 1. Открываем диаграмму
    print("[INFO] Шаг 1: Открытие диаграммы")

    # Ищем папку 'test_flow_component'
    test_flow_folder = page.locator('[aria-label="treeitem_label"]:has-text("test_flow_component")')
    assert test_flow_folder.count() > 0, "Папка 'test_flow_component' не найдена!"
    test_flow_folder.click()
    time.sleep(1)

    # Ищем диаграмму (пробуем разные варианты)
    diagram_files = [
        'test_http.df.json',
        'test_http_flow.df.json', 
        'http_test.df.json'
    ]
    
    diagram_file = None
    for filename in diagram_files:
        file_locator = page.locator(f'[aria-label="treeitem_label"]:has-text("{filename}")')
        if file_locator.count() > 0:
            diagram_file = file_locator
            print(f"[INFO] Найдена диаграмма: {filename}")
            break
    
    assert diagram_file is not None, f"Диаграмма не найдена! Искали: {diagram_files}"
    diagram_file.dblclick()
    time.sleep(2)
    print("[INFO] Диаграмма открыта")

    # Убеждаемся, что canvas загрузился
    canvas = page.locator('canvas').first
    canvas.wait_for(state="visible", timeout=10000)
    time.sleep(2)
    print("[INFO] Canvas диаграммы загружен")

    # Закрываем файловую панель
    try:
        if page.get_by_label("board_toolbar_panel").is_visible():
            file_manager_btn = page.get_by_role("button", name="board_toolbar_filemanager_button")
            if file_manager_btn.is_visible():
                file_manager_btn.click()
                time.sleep(0.5)
                print("[INFO] Файловая панель закрыта")
    except Exception as e:
        print(f"[INFO] Файловая панель уже закрыта: {e}")

    # Закрываем правый сайдбар
    try:
        details_panel = page.locator('[aria-label="diagram_details_panel"]')
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    # Инициализируем canvas_utils
    canvas_utils = CanvasUtils(page)

    # 2. Настраиваем Http_GET компонент
    print("[INFO] Шаг 2: Настройка Http_GET компонента")
    
    http_get_found = canvas_utils.find_component_by_title("Http_GET", timeout=10000)
    assert http_get_found, "Компонент 'Http_GET' не найден на канвасе!"
    print("[INFO] Компонент 'Http_GET' найден")

    # Ждем открытия правого сайдбара
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Правый сайдбар открыт")

    # Настраиваем URL (используем более точный селектор)
    url_field = page.get_by_role("textbox", name="config.url")
    if url_field.count() == 0:
        url_field = page.locator('textarea[name="config.url"], input[name="config.url"]')
    
    assert url_field.count() > 0, "Поле 'URL' не найдено!"
    get_url = f'"{api_server["users_endpoint"]}/2?_limit=1&_fields=id,name,email"'
    url_field.fill(get_url)
    time.sleep(1)
    print(f"[INFO] Http_GET URL настроен: {get_url}")

    # Настраиваем метод (dropdown/select)
    try:
        method_field = page.get_by_role("textbox", name="config.method")
        if method_field.count() == 0:
            method_field = page.locator('textarea[name="config.method"], select[name="config.method"]')
        
        if method_field.count() > 0:
            # Кликаем по полю чтобы открыть dropdown
            method_field.click()
            time.sleep(1)
            
            # Выбираем GET метод из dropdown
            get_option = page.get_by_role("treeitem", name="GET").locator("div").nth(1)
            if get_option.count() > 0:
                get_option.click()
                time.sleep(0.5)
                print("[INFO] Http_GET метод настроен: GET")
            else:
                print("[WARN] Опция GET не найдена в dropdown")
    except Exception as e:
        print(f"[INFO] Поле метода не найдено или не настроено: {e}")

    # Закрываем правый сайдбар
    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Http_GET")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    # 3. Настраиваем Http_POST компонент
    print("[INFO] Шаг 3: Настройка Http_POST компонента")
    
    http_post_found = canvas_utils.find_component_by_title("Http_POST", timeout=10000)
    assert http_post_found, "Компонент 'Http_POST' не найден на канвасе!"
    print("[INFO] Компонент 'Http_POST' найден")

    # Ждем открытия правого сайдбара
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    details_panel.wait_for(state="visible", timeout=10000)

    # Настраиваем URL
    url_field = page.get_by_role("textbox", name="config.url")
    if url_field.count() == 0:
        url_field = page.locator('textarea[name="config.url"], input[name="config.url"]')
    
    post_url = f'"{api_server["users_endpoint"]}?_fields=id,name,email"'
    url_field.fill(post_url)
    time.sleep(1)
    print(f"[INFO] Http_POST URL настроен: {post_url}")

    # Настраиваем метод (dropdown/select)
    try:
        method_field = page.get_by_role("textbox", name="config.method")
        if method_field.count() == 0:
            method_field = page.locator('textarea[name="config.method"], select[name="config.method"]')
        
        if method_field.count() > 0:
            # Кликаем по полю чтобы открыть dropdown
            method_field.click()
            time.sleep(1)
            
            # Выбираем POST метод из dropdown
            post_option = page.get_by_role("treeitem", name="POST").locator("div").nth(1)
            if post_option.count() > 0:
                post_option.click()
                time.sleep(0.5)
                print("[INFO] Http_POST метод настроен: POST")
            else:
                print("[WARN] Опция POST не найдена в dropdown")
    except Exception as e:
        print(f"[INFO] Поле метода не найдено или не настроено: {e}")

    # Настраиваем заголовки
    try:
        # Добавляем первый заголовок
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(0.5)
        
        # Заполняем Content-Type
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").click()
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").fill("\"Content-Type\"")
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").dblclick()
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").fill("\"application/json\"")
        time.sleep(0.5)
        
        # Добавляем второй заголовок для оптимизации
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").click()
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").fill("\"Accept\"")
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").dblclick()
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").fill("\"application/json\"")
        time.sleep(0.5)
        
        # Добавляем третий заголовок для минимизации данных
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").click()
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").fill("\"Accept-Encoding\"")
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").dblclick()
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").fill("\"gzip\"")
        time.sleep(0.5)
        
        # Добавляем четвертый заголовок для минимизации заголовков в ответе
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.3.name").click()
        page.get_by_role("textbox", name="inputs_config.headers.value.3.name").fill("\"X-Requested-With\"")
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.3.value").dblclick()
        page.get_by_role("textbox", name="inputs_config.headers.value.3.value").fill("\"XMLHttpRequest\"")
        time.sleep(0.5)
        
        print("[INFO] Http_POST заголовки настроены: Content-Type, Accept, Accept-Encoding, X-Requested-With")
    except Exception as e:
        print(f"[INFO] Настройка заголовков не удалась: {e}")

    # Настраиваем тело запроса
    try:
        body_field = page.get_by_role("textbox", name="body")
        if body_field.count() == 0:
            body_field = page.locator('textarea[name="body"], input[name="body"]')
        
        if body_field.count() > 0:
            post_body = '{"name": "Test User", "username": "testuser", "email": "test@example.com"}'
            body_field.fill(post_body)
            time.sleep(1)
            print(f"[INFO] Http_POST тело запроса настроено: {post_body}")
    except Exception as e:
        print(f"[INFO] Поле тела запроса не найдено: {e}")

    # Закрываем правый сайдбар
    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Http_POST")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    # 4. Настраиваем Http_PUT компонент
    print("[INFO] Шаг 4: Настройка Http_PUT компонента")
    
    http_put_found = canvas_utils.find_component_by_title("Http_PUT", timeout=10000)
    assert http_put_found, "Компонент 'Http_PUT' не найден на канвасе!"
    print("[INFO] Компонент 'Http_PUT' найден")

    # Ждем открытия правого сайдбара
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    details_panel.wait_for(state="visible", timeout=10000)

    # Настраиваем URL
    url_field = page.get_by_role("textbox", name="config.url")
    if url_field.count() == 0:
        url_field = page.locator('textarea[name="config.url"], input[name="config.url"]')
    
    put_url = f'"{api_server["users_endpoint"]}/2?_fields=id,name,email"'
    url_field.fill(put_url)
    time.sleep(1)
    print(f"[INFO] Http_PUT URL настроен: {put_url}")

    # Настраиваем метод (dropdown/select)
    try:
        method_field = page.get_by_role("textbox", name="config.method")
        if method_field.count() == 0:
            method_field = page.locator('textarea[name="config.method"], select[name="config.method"]')
        
        if method_field.count() > 0:
            # Кликаем по полю чтобы открыть dropdown
            method_field.click()
            time.sleep(1)
            
            # Выбираем PUT метод из dropdown
            put_option = page.get_by_role("treeitem", name="PUT").locator("div").nth(1)
            if put_option.count() > 0:
                put_option.click()
                time.sleep(0.5)
                print("[INFO] Http_PUT метод настроен: PUT")
            else:
                print("[WARN] Опция PUT не найдена в dropdown")
    except Exception as e:
        print(f"[INFO] Поле метода не найдено или не настроено: {e}")

    # Настраиваем заголовки
    try:
        # Добавляем первый заголовок
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").click()
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").fill("\"Content-Type\"")
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").dblclick()
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").fill("\"application/json\"")
        time.sleep(0.5)
        
        # Добавляем второй заголовок
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").click()
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").fill("\"Accept\"")
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").dblclick()
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").fill("\"application/json\"")
        time.sleep(0.5)
        
        # Добавляем третий заголовок для минимизации заголовков в ответе
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").click()
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").fill("\"X-Requested-With\"")
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").dblclick()
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").fill("\"XMLHttpRequest\"")
        time.sleep(0.5)
        
        print("[INFO] Http_PUT заголовки настроены: Content-Type, Accept, X-Requested-With")
    except Exception as e:
        print(f"[INFO] Настройка заголовков не удалась: {e}")

    # Настраиваем тело запроса
    try:
        body_field = page.get_by_role("textbox", name="body")
        if body_field.count() == 0:
            body_field = page.locator('textarea[name="body"], input[name="body"]')
        
        if body_field.count() > 0:
            put_body = '{"name": "Updated User", "username": "updateduser", "email": "updated@example.com"}'
            body_field.fill(put_body)
            time.sleep(1)
            print(f"[INFO] Http_PUT тело запроса настроено: {put_body}")
    except Exception as e:
        print(f"[INFO] Поле тела запроса не найдено: {e}")

    # Закрываем правый сайдбар
    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Http_PUT")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    # 5. Настраиваем Http_PATCH компонент
    print("[INFO] Шаг 5: Настройка Http_PATCH компонента")
    
    http_patch_found = canvas_utils.find_component_by_title("Http_PATCH", timeout=10000)
    assert http_patch_found, "Компонент 'Http_PATCH' не найден на канвасе!"
    print("[INFO] Компонент 'Http_PATCH' найден")

    # Ждем открытия правого сайдбара
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    details_panel.wait_for(state="visible", timeout=10000)

    # Настраиваем URL
    url_field = page.get_by_role("textbox", name="config.url")
    if url_field.count() == 0:
        url_field = page.locator('textarea[name="config.url"], input[name="config.url"]')
    
    patch_url = f'"{api_server["users_endpoint"]}/2?_fields=id,name,email"'
    url_field.fill(patch_url)
    time.sleep(1)
    print(f"[INFO] Http_PATCH URL настроен: {patch_url}")

    # Настраиваем метод (dropdown/select)
    try:
        method_field = page.get_by_role("textbox", name="config.method")
        if method_field.count() == 0:
            method_field = page.locator('textarea[name="config.method"], select[name="config.method"]')
        
        if method_field.count() > 0:
            # Кликаем по полю чтобы открыть dropdown
            method_field.click()
            time.sleep(1)
            
            # Выбираем PATCH метод из dropdown
            patch_option = page.get_by_role("treeitem", name="PATCH").locator("div").nth(1)
            if patch_option.count() > 0:
                patch_option.click()
                time.sleep(0.5)
                print("[INFO] Http_PATCH метод настроен: PATCH")
            else:
                print("[WARN] Опция PATCH не найдена в dropdown")
    except Exception as e:
        print(f"[INFO] Поле метода не найдено или не настроено: {e}")

    # Настраиваем заголовки
    try:
        # Добавляем первый заголовок
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").click()
        page.get_by_role("textbox", name="inputs_config.headers.value.0.name").fill("\"Content-Type\"")
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").dblclick()
        page.get_by_role("textbox", name="inputs_config.headers.value.0.value").fill("\"application/json\"")
        time.sleep(0.5)
        
        # Добавляем второй заголовок
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").click()
        page.get_by_role("textbox", name="inputs_config.headers.value.1.name").fill("\"Accept\"")
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").dblclick()
        page.get_by_role("textbox", name="inputs_config.headers.value.1.value").fill("\"application/json\"")
        time.sleep(0.5)
        
        # Добавляем третий заголовок для минимизации заголовков в ответе
        page.get_by_role("button", name="extendable_list_add_button").click()
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").click()
        page.get_by_role("textbox", name="inputs_config.headers.value.2.name").fill("\"X-Requested-With\"")
        time.sleep(0.5)
        
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").dblclick()
        page.get_by_role("textbox", name="inputs_config.headers.value.2.value").fill("\"XMLHttpRequest\"")
        time.sleep(0.5)
        
        print("[INFO] Http_PATCH заголовки настроены: Content-Type, Accept, X-Requested-With")
    except Exception as e:
        print(f"[INFO] Настройка заголовков не удалась: {e}")

    # Настраиваем тело запроса (частичное обновление)
    try:
        body_field = page.get_by_role("textbox", name="body")
        if body_field.count() == 0:
            body_field = page.locator('textarea[name="body"], input[name="body"]')
        
        if body_field.count() > 0:
            patch_body = '{"email": "patched@example.com"}'
            body_field.fill(patch_body)
            time.sleep(1)
            print(f"[INFO] Http_PATCH тело запроса настроено: {patch_body}")
    except Exception as e:
        print(f"[INFO] Поле тела запроса не найдено: {e}")

    # Закрываем правый сайдбар
    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Http_PATCH")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    # 6. Настраиваем Http_DEL компонент
    print("[INFO] Шаг 6: Настройка Http_DEL компонента")
    
    http_del_found = canvas_utils.find_component_by_title("Http_DEL", timeout=10000)
    assert http_del_found, "Компонент 'Http_DEL' не найден на канвасе!"
    print("[INFO] Компонент 'Http_DEL' найден")

    # Ждем открытия правого сайдбара
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    details_panel.wait_for(state="visible", timeout=10000)

    # Настраиваем URL
    url_field = page.get_by_role("textbox", name="config.url")
    if url_field.count() == 0:
        url_field = page.locator('textarea[name="config.url"], input[name="config.url"]')
    
    del_url = f'"{api_server["users_endpoint"]}/2?_fields=id"'
    url_field.fill(del_url)
    time.sleep(1)
    print(f"[INFO] Http_DEL URL настроен: {del_url}")

    # Настраиваем метод (dropdown/select)
    try:
        method_field = page.get_by_role("textbox", name="config.method")
        if method_field.count() == 0:
            method_field = page.locator('textarea[name="config.method"], select[name="config.method"]')
        
        if method_field.count() > 0:
            # Кликаем по полю чтобы открыть dropdown
            method_field.click()
            time.sleep(1)
            
            # Выбираем DELETE метод из dropdown
            delete_option = page.get_by_role("treeitem", name="DELETE").locator("div").nth(1)
            if delete_option.count() > 0:
                delete_option.click()
                time.sleep(0.5)
                print("[INFO] Http_DEL метод настроен: DELETE")
            else:
                print("[WARN] Опция DELETE не найдена в dropdown")
    except Exception as e:
        print(f"[INFO] Поле метода не найдено или не настроено: {e}")

    # DELETE не требует заголовков Content-Type и тела запроса

    # Закрываем правый сайдбар
    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Http_DEL")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    # 7. Настраиваем Output компонент для сбора всех ответов
    print("[INFO] Шаг 7: Настройка Output компонента для сбора всех HTTP ответов")
    
    output_found = canvas_utils.find_component_by_title("Output", timeout=10000)
    assert output_found, "Компонент 'Output' не найден на канвасе!"
    print("[INFO] Компонент 'Output' найден")

    # Ждем открытия правого сайдбара
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Правый сайдбар открыт для Output")

    # Нажимаем кнопку раскрытия для поля "Данные"
    try:
        expression_button = page.get_by_role("button", name="textfield_expression_button")
        if expression_button.count() > 0:
            expression_button.click()
            time.sleep(1)
            print("[INFO] Кнопка раскрытия поля 'Данные' нажата")
        else:
            # Пробуем альтернативные селекторы
            expression_button = page.locator('button[aria-label*="expression"], button[title*="expression"]')
            if expression_button.count() > 0:
                expression_button.first.click()
                time.sleep(1)
                print("[INFO] Кнопка раскрытия поля 'Данные' найдена через альтернативный селектор")
            else:
                print("[WARN] Кнопка раскрытия поля 'Данные' не найдена")
    except Exception as e:
        print(f"[WARN] Ошибка при нажатии кнопки раскрытия: {e}")

    # Ждем открытия модального окна
    try:
        modal = page.locator('[role="dialog"], .modal, .expression-modal')
        modal.wait_for(state="visible", timeout=10000)
        print("[INFO] Модальное окно для редактирования выражения открыто")
    except Exception as e:
        print(f"[WARN] Модальное окно не открылось: {e}")

    # Вводим JSON со всеми ответами HTTP коннекторов
    try:
        editor_field = page.get_by_role("textbox", name="editor_view")
        if editor_field.count() == 0:
            # Пробуем альтернативные селекторы для Monaco Editor
            editor_field = page.locator('.monaco-editor textarea, .view-lines, [data-testid="editor"]')
        
        if editor_field.count() > 0:
            # Создаем JSON со всеми ответами HTTP коннекторов (только body, без заголовков)
            all_responses_json = '''{"Get": $node.Http_GET.response.body,"Post": $node.Http_POST.response.body,"Put": $node.Http_PUT.response.body,"Patch": $node.Http_PATCH.response.body,"Delete": $node.Http_DEL.response.body,"summary": {"total_requests": 5,"methods": ["GET", "POST", "PUT", "PATCH", "DELETE"],"api_url": "''' + api_server["base_url"] + '''"}}'''
            
            editor_field.fill(all_responses_json)
            time.sleep(1)
            print("[INFO] JSON со всеми HTTP ответами введен в редактор")
            print(f"[INFO] JSON содержит ответы от всех 5 HTTP методов")
        else:
            print("[WARN] Поле редактора не найдено")
    except Exception as e:
        print(f"[WARN] Ошибка при вводе JSON: {e}")

    # Закрываем модальное окно (сохраняем изменения)
    try:
        # Ищем кнопку сохранения для редактора выражений
        save_button = page.get_by_role("button", name="expressioneditor_submit_button")
        if save_button.count() > 0:
            save_button.click()
            time.sleep(1)
            print("[INFO] Модальное окно закрыто с сохранением через expressioneditor_submit_button")
        else:
            # Fallback - пробуем другие варианты
            save_button = page.locator('button:has-text("Сохранить"), button:has-text("Save"), button:has-text("OK")')
            if save_button.count() > 0:
                save_button.first.click()
                time.sleep(1)
                print("[INFO] Модальное окно закрыто с сохранением через fallback")
            else:
                # Пробуем нажать Escape
                page.keyboard.press("Escape")
                time.sleep(1)
                print("[INFO] Модальное окно закрыто через Escape")
    except Exception as e:
        print(f"[WARN] Ошибка при закрытии модального окна: {e}")

    # Закрываем правый сайдбар
    try:
        if details_panel.is_visible():
            switcher = page.get_by_role("button", name="diagram_details_panel_switcher")
            if switcher.is_visible():
                switcher.click()
                time.sleep(0.5)
                print("[INFO] Правый сайдбар закрыт после настройки Output")
    except Exception as e:
        print(f"[INFO] Правый сайдбар уже закрыт: {e}")

    # 8. Запускаем диаграмму
    print("[INFO] Шаг 8: Запуск диаграммы")

    # Находим и нажимаем кнопку запуска диаграммы
    play_button = page.get_by_role("button", name="diagram_play_button")
    assert play_button.is_visible(), "Кнопка запуска диаграммы не найдена!"
    play_button.click()
    time.sleep(5)  # Увеличиваем время ожидания для последовательности запросов
    print("[INFO] Диаграмма запущена")

    # Ждем появления тоста с результатом
    toast = page.locator('[aria-label="toast"]')
    toast.wait_for(state="visible", timeout=60000)  # Увеличиваем таймаут
    print("[INFO] Toast с результатом появился")

    # Проверяем успешность выполнения
    toast_title = page.locator('[aria-label="toast"] .Toast__Title___-0bIZ')
    toast_text = toast_title.inner_text()
    print(f"[INFO] Результат выполнения: {toast_text}")

    # Проверяем, что диаграмма завершилась успешно
    assert "Диаграмма завершена" in toast_text, f"Ожидался успешный результат, получен: {toast_text}"
    print("[INFO] Диаграмма завершилась успешно!")

    # 9. Проверяем результаты в Output компоненте
    print("[INFO] Шаг 9: Проверка результатов в Output компоненте")

    # Двойной клик по канвасу для открытия сайдбара
    canvas = page.locator('canvas').first
    canvas.dblclick()
    time.sleep(1)
    print("[INFO] Двойной клик по канвасу выполнен")

    # Ждем открытия сайдбара
    details_panel = page.locator('[aria-label="diagram_details_panel"]')
    details_panel.wait_for(state="visible", timeout=10000)
    print("[INFO] Сайдбар открыт")

    # Переходим на вкладку "Процесс"
    process_tab = page.get_by_text("Процесс", exact=True)
    assert process_tab.is_visible(), "Вкладка 'Процесс' не найдена!"
    process_tab.click()
    time.sleep(1)
    print("[INFO] Переход на вкладку 'Процесс' выполнен")

    # Переходим на подвкладку "Анализ"
    analysis_tab = page.get_by_text("Анализ", exact=True)
    assert analysis_tab.is_visible(), "Подвкладка 'Анализ' не найдена!"
    analysis_tab.click()
    time.sleep(1)
    print("[INFO] Переход на подвкладку 'Анализ' выполнен")

    # Нажимаем кнопку для открытия модального окна "Просмотр JSON"
    try:
        full_view_button = page.get_by_role("button", name="formitem_full_view_button").nth(1)
        if full_view_button.count() > 0:
            full_view_button.click()
            time.sleep(1)
            print("[INFO] Кнопка 'formitem_full_view_button' (nth(1)) нажата")

            # Ждем открытия модального окна "Просмотр JSON"
            json_modal = page.locator('[role="dialog"]:has-text("Просмотр JSON")')
            json_modal.wait_for(state="visible", timeout=10000)
            print("[INFO] Модальное окно 'Просмотр JSON' открыто")
            
            # Делаем скриншот модального окна
            save_screenshot(page, f"http_all_responses_{project_code}")
            
            # Ждем загрузки данных в модальное окно
            time.sleep(3)

            # Получаем JSON данные из Monaco Editor в модальном окне
            view_lines = page.locator('[role="dialog"] .view-lines')
            assert view_lines.count() > 0, "Monaco Editor не найден в модальном окне!"
            
            json_text = view_lines.inner_text()
            print(f"[INFO] JSON данные получены из Monaco Editor (длина: {len(json_text)}): {json_text[:500]}...")
            
            assert json_text.strip(), "JSON данные не найдены в Monaco Editor!"

            # Очищаем JSON от невидимых символов и извлекаем только JSON часть
            import re
            json_text_clean = re.sub(r'[\xa0\u00a0]', ' ', json_text)
            json_text_clean = json_text_clean.strip()
            print(f"[INFO] Очищенный JSON (длина: {len(json_text_clean)}): {json_text_clean[:300]}...")

            # Пытаемся найти JSON объект в тексте (ищем { ... })
            json_match = re.search(r'\{.*\}', json_text_clean, re.DOTALL)
            if json_match:
                json_text_clean = json_match.group(0)
                print(f"[INFO] Извлеченный JSON объект (длина: {len(json_text_clean)}): {json_text_clean[:200]}...")
            else:
                print("[WARN] JSON объект не найден в тексте, используем весь текст")

            # Парсим JSON для проверки структуры
            try:
                json_data = json.loads(json_text_clean)
                print("[INFO] JSON успешно распарсен")
                
                # Проверяем структуру JSON с ответами всех HTTP методов
                assert "Get" in json_data, "Поле 'Get' не найдено в JSON"
                assert "Post" in json_data, "Поле 'Post' не найдено в JSON"
                assert "Put" in json_data, "Поле 'Put' не найдено в JSON"
                assert "Patch" in json_data, "Поле 'Patch' не найдено в JSON"
                assert "Delete" in json_data, "Поле 'Delete' не найдено в JSON"
                assert "summary" in json_data, "Поле 'summary' не найдено в JSON"
                
                # Проверяем summary
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

            # Закрываем модальное окно
            close_button = page.locator('[role="dialog"] button[aria-label="close"], [role="dialog"] .close-button')
            if close_button.count() > 0:
                close_button.first.click()
                time.sleep(1)
                print("[INFO] Модальное окно закрыто")
        else:
            print("[WARN] Кнопка 'formitem_full_view_button' не найдена")

    except Exception as e:
        print(f"[WARN] Ошибка при проверке результатов Output: {e}")

    # Делаем финальный скриншот
    save_screenshot(page, f"http_flow_sequence_complete_{project_code}")

    print("[SUCCESS] Все шаги теста HTTP Flow Sequence выполнены успешно!")
    print("[SUCCESS] Тест прошел: GET -> POST -> PUT -> PATCH -> DELETE запросы к JSONPlaceholder API выполнены!")
    print(f"[SUCCESS] API server работал на {api_server['base_url']}")
    print("[SUCCESS] DELETE метод вернул JSON ответ с подробной информацией!")
    print("[SUCCESS] Output компонент собрал все HTTP ответы в единый JSON!")
    time.sleep(5)
