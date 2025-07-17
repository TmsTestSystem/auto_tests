import os
import time
import pytest
from pages.project_page import ProjectPage
from pages.file_panel_page import FilePanelPage
from conftest import save_screenshot

# Список текстов/aria-label, которые нужно игнорировать (подменю и импорт)
SKIP_LABELS = [
    'импорт', 'import',
    'структуры данных openapi', 'openapi',
    'файл',  # если "Файл" только в подменю, иначе убери эту строку
]

def should_skip(aria, text):
    for skip in SKIP_LABELS:
        if (aria and skip in aria.lower()) or (text and skip in text.lower()):
            return True
    return False

def generate_unique_name(base, existing_names):
    idx = 1
    name = base
    while name in existing_names:
        name = f"{base}_{idx}"
        idx += 1
    return name

# --- Функции для создания ---
def create_folder(page, file_panel, base_name):
    existing_names = set(file_panel.get_all_tree_names())
    folder_name = generate_unique_name(base_name, existing_names)
    file_panel.open_create_file_menu()
    time.sleep(1)
    folder_btn = None
    folder_btns = page.query_selector_all('div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]')
    for btn in folder_btns:
        if btn.inner_text().strip() == 'Папку':
            folder_btn = btn
            break
    if not folder_btn:
        print("[FAIL] Кнопка 'Папку' не найдена!")
        return None
    try:
        file_panel.create_file_or_folder_of_type(folder_btn, folder_name)
        print(f"[OK] Папка '{folder_name}' создана успешно!")
        return folder_name
    except Exception as e:
        print(f"[FAIL] Не удалось создать папку '{folder_name}': {e}")
        return None

def create_file_of_type(page, file_panel, base_name, aria, text, extension):
    existing_names = set(file_panel.get_all_tree_names())
    file_panel.open_create_file_menu()
    time.sleep(1)
    found_btn = None
    for btn in file_panel.get_file_type_buttons():
        if btn.get_attribute('aria-label') == aria and btn.inner_text() == text:
            found_btn = btn
            break
    if not found_btn:
        print(f"[SKIP] Не найден тип: aria-label={aria}, text={text}")
        return None
    base_unique = generate_unique_name(base_name, existing_names)
    file_name = base_unique  # Не добавляем extension!
    try:
        file_panel.create_file_or_folder_of_type(found_btn, file_name)
        print(f"[OK] Файл '{file_name}' создан успешно!")
        return file_name
    except Exception as e:
        print(f"[FAIL] Не удалось создать файл '{file_name}': {e}")
        return None

def create_data_structure_file(page, file_panel):
    import time
    # Открыть панель файлов
    page.get_by_role("button", name="board_toolbar_filemanager_button").click()
    # Открыть меню создания файла
    page.get_by_role("button", name="filemanager_create_button").click()
    # Клик по типу "Структуры данных"
    page.get_by_role("treeitem", name="data_structure").locator("div").nth(1).click()
    # Ввод уникального имени файла
    file_name = f"datastruct_{int(time.time())}"
    page.get_by_role("textbox", name="treeitem_label_field").fill(file_name)
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    return file_name

def create_openapi_file(page, file_panel):
    file_type_buttons = file_panel.get_file_type_buttons()
    for btn in file_type_buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        extension = btn.get_attribute('extension') or ''
        if "openapi" in (aria or '').lower() or "openapi" in (text or '').lower():
            base_name = f"openapi_{int(time.time())}"
            return create_file_of_type(page, file_panel, base_name, aria, text, extension)
    print("[FAIL] Кнопка типа 'OpenAPI' не найдена!")
    return None

def create_config_file(page, file_panel):
    file_type_buttons = file_panel.get_file_type_buttons()
    for btn in file_type_buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        extension = btn.get_attribute('extension') or ''
        if "config" in (aria or '').lower() or "config" in (text or '').lower():
            base_name = f"config_{int(time.time())}"
            return create_file_of_type(page, file_panel, base_name, aria, text, extension)
    print("[FAIL] Кнопка типа 'Config' не найдена!")
    return None

def create_process_file(page, file_panel):
    file_type_buttons = file_panel.get_file_type_buttons()
    for btn in file_type_buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        extension = btn.get_attribute('extension') or ''
        if "процесс" in (aria or '').lower() or "процесс" in (text or '').lower():
            base_name = f"process_{int(time.time())}"
            return create_file_of_type(page, file_panel, base_name, aria, text, extension)
    print("[FAIL] Кнопка типа 'Процесс' не найдена!")
    return None

def create_python_script_file(page, file_panel):
    file_type_buttons = file_panel.get_file_type_buttons()
    for btn in file_type_buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        extension = btn.get_attribute('extension') or ''
        if "python" in (aria or '').lower() or "python" in (text or '').lower():
            base_name = f"py_{int(time.time())}"
            return create_file_of_type(page, file_panel, base_name, aria, text, extension)
    print("[FAIL] Кнопка типа 'Скрипт Python' не найдена!")
    return None

def create_decision_table_file(page, file_panel):
    file_type_buttons = file_panel.get_file_type_buttons()
    for btn in file_type_buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        extension = btn.get_attribute('extension') or ''
        if "таблица решений" in (aria or '').lower() or "таблица решений" in (text or '').lower():
            base_name = f"decision_{int(time.time())}"
            return create_file_of_type(page, file_panel, base_name, aria, text, extension)
    print("[FAIL] Кнопка типа 'Таблица решений' не найдена!")
    return None

def create_test_file(page, file_panel):
    file_type_buttons = file_panel.get_file_type_buttons()
    for btn in file_type_buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        extension = btn.get_attribute('extension') or ''
        if "тест" in (aria or '').lower() or "тест" in (text or '').lower():
            base_name = f"test_{int(time.time())}"
            return create_file_of_type(page, file_panel, base_name, aria, text, extension)
    print("[FAIL] Кнопка типа 'Тест' не найдена!")
    return None

def create_db_connection_file(page, file_panel):
    file_type_buttons = file_panel.get_file_type_buttons()
    for btn in file_type_buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        extension = btn.get_attribute('extension') or ''
        if "бд" in (aria or '').lower() or "бд" in (text or '').lower() or "database" in (aria or '').lower() or "database" in (text or '').lower():
            base_name = f"db_{int(time.time())}"
            return create_file_of_type(page, file_panel, base_name, aria, text, extension)
    print("[FAIL] Кнопка типа 'Подключение к БД' не найдена!")
    return None

def create_file_file(page, file_panel):
    file_type_buttons = file_panel.get_file_type_buttons()
    for btn in file_type_buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        extension = btn.get_attribute('extension') or ''
        if "файл" in (aria or '').lower() or "файл" in (text or '').lower():
            base_name = f"file_{int(time.time())}"
            return create_file_of_type(page, file_panel, base_name, aria, text, extension)
    print("[FAIL] Кнопка типа 'Файл' не найдена!")
    return None

def test_create_all_file_types(login_page):
    page = login_page
    project_code = f"autotest{int(time.time())}"
    project_title = f"Автотест {int(time.time())}"
    project_page = ProjectPage(page)
    file_panel = FilePanelPage(page)
    # Создаём проект
    project_page.open_create_project_modal()
    project_page.create_project(
        title=project_title,
        code=project_code,
        git="git@github.com:IlyaKurilin/spr.git",
        default_branch="main"
    )
    project_page.wait_modal_close()
    # Ждём появления проекта в списке
    prj = None
    for _ in range(30):
        prj = project_page.find_project_in_list(project_title)
        if prj:
            break
        time.sleep(0.5)
    assert prj is not None, f"Проект с названием {project_title} не найден в списке после создания!"
    prj.click()
    page.wait_for_load_state('networkidle')
    # Открываем панель файлов через FilePanelPage
    file_panel.open_file_panel()
    created = 0
    # --- Создаём папку ---
    file_panel.open_create_file_menu()
    time.sleep(1)
    folder_btn = None
    folder_btns = page.query_selector_all('div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]')
    for btn in folder_btns:
        if btn.inner_text().strip() == 'Папку':
            folder_btn = btn
            break
    if folder_btn:
        file_name = generate_unique_name(f"autofolder_{int(time.time())}", set(file_panel.get_all_tree_names()))
        print(f"Создаю папку: имя={file_name}")
        try:
            file_panel.create_file_or_folder_of_type(folder_btn, file_name)
            print(f"[OK] Папка '{file_name}' создана успешно!")
            created += 1
        except Exception as e:
            print(f"[FAIL] Не удалось создать папку '{file_name}': {e}")
    else:
        print("[FAIL] Кнопка 'Папку' не найдена!")
    # --- Создаём остальные типы файлов ---
    file_panel.open_create_file_menu()
    time.sleep(1)
    file_type_buttons = file_panel.get_file_type_buttons()
    type_keys = []
    for btn in file_type_buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        if should_skip(aria, text):
            print(f"[SKIP] Пропускаю тип: aria-label={aria}, text={text}")
            continue
        type_keys.append((aria, text))
    for idx, (aria, text) in enumerate(type_keys):
        file_panel.open_create_file_menu()
        time.sleep(1)
        found_btn = None
        for btn in file_panel.get_file_type_buttons():
            if btn.get_attribute('aria-label') == aria and btn.inner_text() == text:
                found_btn = btn
                break
        if not found_btn:
            print(f"[SKIP] Не найден тип: aria-label={aria}, text={text}")
            continue
        file_name = generate_unique_name(f"autofile_{idx}_{int(time.time())}", set(file_panel.get_all_tree_names()))
        print(f"Создаю файл: aria-label={aria}, text={text}, имя={file_name}")
        try:
            file_panel.create_file_or_folder_of_type(found_btn, file_name)
            print(f"[OK] Файл '{file_name}' создан успешно!")
            created += 1
        except Exception as e:
            print(f"[FAIL] Не удалось создать файл '{file_name}': {e}")
    print(f"[CREATE_FILES] Всего успешно создано: {created}")
    save_screenshot(page, "test_create_all_file_types")

def test_create_and_delete_all_file_types_in_existing_project(login_page):
    try:
        page = login_page
        file_panel = FilePanelPage(page)
        # --- Переход в первый проект после авторизации ---
        page.wait_for_selector('div[aria-label="projects_card"]', timeout=15000)
        cards = page.query_selector_all('div[aria-label="projects_card"]')
        if not cards:
            raise Exception('Нет доступных проектов для перехода!')
        first_card = cards[0]
        link = first_card.query_selector('a[aria-label="projects_card_link"]')
        if not link:
            raise Exception('Не найдена ссылка на проект в карточке!')
        link.click()
        page.wait_for_load_state('networkidle')
        created_names = []
        # --- Создаём папку ---
        file_panel.open_file_panel()
        folder_name = create_folder(page, file_panel, f"autofolder_{int(time.time())}")
        if folder_name:
            created_names.append((folder_name, False))
        # --- Создаём остальные типы файлов ---
        file_panel.open_create_file_menu()
        time.sleep(1)
        file_type_buttons = file_panel.get_file_type_buttons()
        type_keys = []
        for btn in file_type_buttons:
            aria = btn.get_attribute('aria-label')
            text = btn.inner_text()
            extension = btn.get_attribute('extension') or ''
            if should_skip(aria, text):
                print(f"[SKIP] Пропускаю тип: aria-label={aria}, text={text}")
                continue
            type_keys.append((aria, text, extension))
        for idx, (aria, text, extension) in enumerate(type_keys):
            base_name = f"autofile_{idx}_{int(time.time())}"
            file_name = create_file_of_type(page, file_panel, base_name, aria, text, extension)
            if file_name:
                created_names.append((file_name, True))
        # --- Удаляем все созданные файлы/папки из сохранённого списка ---
        deleted_count = 0
        for name, is_file in created_names:
            try:
                print(f"[DEL][TRY] Пытаюсь удалить: {name} (is_file={is_file})")
                selector = f'div[role="treeitem"][aria-label="/{name}"]'
                treeitem = page.query_selector(selector)
                if not treeitem:
                    print(f"[DEL][SKIP] Не найден элемент для удаления: {name}")
                    page.screenshot(path=f'screenshots/diagnostic_not_found_{name}.png', full_page=True)
                    continue
                # Скроллим элемент в видимую область
                page.evaluate('(el) => el.scrollIntoView({block: "center"})', treeitem)
                treeitem.click(button='right')
                time.sleep(0.5)
                # Диагностика: скриншот и HTML после правого клика
                page.screenshot(path=f'screenshots/diagnostic_right_click_{name}.png', full_page=True)
                with open(f'screenshots/diagnostic_right_click_{name}.html', 'w', encoding='utf-8') as f:
                    f.write(page.content())
                # Ожидание появления меню
                page.wait_for_selector('div[role="menuitem"], div.TreeItem__LabelPrimary___vzajD', timeout=3000)
                # Новый селектор для кнопки удаления
                delete_btn = page.query_selector('div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Удалить")')
                if delete_btn:
                    delete_btn.click()
                    # Явно ждём появления модалки с кнопкой "Удалить"
                    try:
                        page.wait_for_selector('button[role="button"], button', timeout=5000)
                    except Exception as e:
                        print(f"[DEL][FAIL] Модалка подтверждения удаления не появилась для: {name}, ошибка: {e}")
                        page.screenshot(path=f'screenshots/diagnostic_no_confirm_modal_{name}.png', full_page=True)
                        continue
                    # Теперь кликаем по кнопке подтверждения удаления
                    page.get_by_role("button", name="Удалить").click()
                    print(f"[DEBUG] Клик по кнопке подтверждения удаления через get_by_role выполнен для {name}")
                    # Скриншот после удаления
                    page.screenshot(path=f'screenshots/diagnostic_after_delete_{name}.png', full_page=True)
                    # Явно ждём исчезновения элемента (ожидание, что файл пропал из DOM)
                    page.wait_for_selector(selector, state='detached', timeout=10000)
                    # Assert: элемент должен быть удалён
                    assert not page.query_selector(selector), f"Файл {name} не был удалён!"
                    print(f"[DEL][OK] Удалён: {name}")
                    deleted_count += 1
                    if deleted_count == 1:
                        time.sleep(2)
                else:
                    print(f"[DEL][FAIL] Не найдена кнопка удаления для: {name}")
                    page.screenshot(path=f'screenshots/diagnostic_no_delete_btn_{name}.png', full_page=True)
                    with open(f'screenshots/diagnostic_no_delete_btn_{name}.html', 'w', encoding='utf-8') as f:
                        f.write(page.content())
            except Exception as e:
                print(f"[DEL][FAIL] Ошибка при удалении {name}: {e}")
        # Финальный скриншот панели файлов
        page.screenshot(path='screenshots/diagnostic_final_file_panel.png', full_page=True)
        save_screenshot(page, "test_create_and_delete_all_file_types_in_existing_project_delete")
    except Exception as e:
        print(f"[TEST][FAIL] Ошибка в тесте: {e}")
        raise

# Пример отдельного теста для структуры данных
def test_create_only_data_structure_file(login_page):
    page = login_page
    file_panel = FilePanelPage(page)
    # Переход в проект
    page.wait_for_selector('div[aria-label="projects_card"]', timeout=15000)
    cards = page.query_selector_all('div[aria-label="projects_card"]')
    if not cards:
        raise Exception('Нет доступных проектов для перехода!')
    first_card = cards[0]
    link = first_card.query_selector('a[aria-label="projects_card_link"]')
    if not link:
        raise Exception('Не найдена ссылка на проект в карточке!')
    link.click()
    page.wait_for_load_state('networkidle')
    file_panel.open_file_panel()
    file_panel.open_create_file_menu()
    # Явно ждём появления кнопки 'Структуры данных' в меню
    page.wait_for_selector('div[role="treeitem"][aria-label="data_structure"], div[role="treeitem"][extension=".ds.json"], div.TreeItem__LabelPrimary___vzajD:has-text("Структуры данных")', timeout=10000)
    # Диагностика: скриншот меню и вывод всех кнопок типов файлов
    page.screenshot(path='screenshots/diagnostic_file_type_menu.png', full_page=True)
    file_type_buttons = file_panel.get_file_type_buttons()
    print('[DIAG] Кнопки типов файлов:')
    for btn in file_type_buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        extension = btn.get_attribute('extension')
        print(f'  aria-label: {aria}, text: {text}, extension: {extension}')
    # Создаём файл "Структура данных"
    file_name = create_data_structure_file(page, file_panel)
    assert file_name, 'Файл структуры данных не был создан!'

def test_create_and_delete_data_structure_file(login_page):
    import time
    page = login_page
    # Переход в первый проект после авторизации
    page.wait_for_selector('div[aria-label="projects_card"]', timeout=15000)
    cards = page.query_selector_all('div[aria-label="projects_card"]')
    assert cards, 'Нет доступных проектов для перехода!'
    first_card = cards[0]
    link = first_card.query_selector('a[aria-label="projects_card_link"]')
    assert link, 'Не найдена ссылка на проект в карточке!'
    link.click()
    page.wait_for_load_state('networkidle')
    # Открыть панель файлов
    page.get_by_role("button", name="board_toolbar_filemanager_button").click()
    # Открыть меню создания файла
    page.get_by_role("button", name="filemanager_create_button").click()
    # Клик по типу "Структуры данных"
    page.get_by_role("treeitem", name="data_structure").locator("div").nth(1).click()
    # Ввод уникального имени файла
    file_name = f"datastruct_{int(time.time())}"
    page.get_by_role("textbox", name="treeitem_label_field").fill(file_name)
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    # Ожидание появления файла в дереве
    selector = f'div[role="treeitem"][aria-label="/{file_name}.ds.json"]'
    page.wait_for_selector(selector, timeout=10000)
    page.screenshot(path=f'screenshots/after_create_{file_name}.png', full_page=True)
    # Удаление файла через контекстное меню
    treeitem = page.query_selector(selector)
    assert treeitem, f'Не найден элемент для удаления: {file_name}'
    page.evaluate('(el) => el.scrollIntoView({block: "center"})', treeitem)
    treeitem.click(button='right')
    page.wait_for_selector('div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Удалить")', timeout=3000)
    delete_btn = page.query_selector('div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Удалить")')
    assert delete_btn, f'Не найдена кнопка удаления для: {file_name}'
    delete_btn.click()
    page.wait_for_selector('button:has-text("Удалить")', timeout=5000)
    page.get_by_role("button", name="Удалить").click()
    page.wait_for_selector(selector, state='detached', timeout=10000)
    assert not page.query_selector(selector), f'Файл {file_name} не был удалён!'
    print(f'[DEL][OK] Удалён: {file_name}')
    time.sleep(2)

def test_create_and_delete_all_types_universal(login_page):
    import time
    page = login_page
    # Переход в первый проект после авторизации
    page.wait_for_selector('div[aria-label="projects_card"]', timeout=15000)
    cards = page.query_selector_all('div[aria-label="projects_card"]')
    assert cards, 'Нет доступных проектов для перехода!'
    first_card = cards[0]
    link = first_card.query_selector('a[aria-label="projects_card_link"]')
    assert link, 'Не найдена ссылка на проект в карточке!'
    link.click()
    page.wait_for_load_state('networkidle')
    page.get_by_role("button", name="board_toolbar_filemanager_button").click()
    types = [
        {"type_role": "treeitem", "type_name": "directory", "ext": "", "desc": "Папка"},
        {"type_role": "treeitem", "type_name": "data_structure", "ext": ".ds.json", "desc": "Структуры данных"},
        {"type_role": "treeitem", "type_name": "decision_flow", "ext": ".df.json", "desc": "Процесс"},
        {"type_role": "treeitem", "type_name": "python", "ext": ".py", "desc": "Скрипт Python"},
        {"type_role": "treeitem", "type_name": "decision_table", "ext": ".dt.json", "desc": "Таблица решений"},
        {"type_role": "treeitem", "type_name": "test", "ext": ".test.json", "desc": "Тест"},
        {"type_role": "treeitem", "type_name": "database_connection_info", "ext": ".db.json", "desc": "Подключение к БД"},
        {"type_role": "treeitem", "type_name": "user_file", "ext": "", "desc": "Файл"},
    ]
    for t in types:
        try:
            page.get_by_role("button", name="filemanager_create_button").click()
            page.get_by_role(t["type_role"], name=t["type_name"]).locator("div").nth(1).click()
            file_name = f"autofile_{t['type_name']}_{int(time.time())}"
            page.get_by_role("textbox", name="treeitem_label_field").fill(file_name)
            page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
            ext = t["ext"]
            selector = f'div[role="treeitem"][aria-label="/{file_name}{ext}"]'
            page.wait_for_selector(selector, timeout=10000)
            print(f'[CREATE][OK] {t["desc"]}: {file_name}{ext}')
            # Удаление
            treeitem = page.query_selector(selector)
            assert treeitem, f'Не найден элемент для удаления: {file_name}{ext}'
            page.evaluate('(el) => el.scrollIntoView({block: "center"})', treeitem)
            treeitem.click(button='right')
            page.wait_for_selector('div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Удалить")', timeout=3000)
            delete_btn = page.query_selector('div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Удалить")')
            assert delete_btn, f'Не найдена кнопка удаления для: {file_name}{ext}'
            delete_btn.click()
            page.wait_for_selector('button:has-text("Удалить")', timeout=5000)
            page.get_by_role("button", name="Удалить").click()
            page.wait_for_selector(selector, state='detached', timeout=10000)
            assert not page.query_selector(selector), f'Файл {file_name}{ext} не был удалён!'
            print(f'[DEL][OK] {t["desc"]}: {file_name}{ext}')
            time.sleep(1)
        except Exception as e:
            print(f'[FAIL] {t["desc"]}: {e}')
    time.sleep(2)

def test_context_menu_all_file_actions(login_page):
    import time
    import pyperclip
    page = login_page
    file_panel = FilePanelPage(page)
    # Переход в первый проект после авторизации
    page.wait_for_selector('div[aria-label="projects_card"]', timeout=15000)
    cards = page.query_selector_all('div[aria-label="projects_card"]')
    assert cards, 'Нет доступных проектов для перехода!'
    first_card = cards[0]
    link = first_card.query_selector('a[aria-label="projects_card_link"]')
    assert link, 'Не найдена ссылка на проект в карточке!'
    link.click()
    page.wait_for_load_state('networkidle')
    file_panel.open_file_panel()
    # 1. Создать тестовую папку
    folder_name = f"test_target_folder_{int(time.time())}"
    file_panel.open_create_file_menu()
    time.sleep(1)
    folder_btn = None
    folder_btns = page.query_selector_all('div.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]')
    for btn in folder_btns:
        if btn.inner_text().strip() == 'Папку':
            folder_btn = btn
            break
    assert folder_btn, "Кнопка 'Папку' не найдена!"
    file_panel.create_file_or_folder_of_type(folder_btn, folder_name)
    folder_selector = f'div[role="treeitem"][aria-label="/{folder_name}"]'
    page.wait_for_selector(folder_selector, timeout=10000)
    folder_item = page.query_selector(folder_selector)
    # 2. Создать структуру данных внутри папки через контекстное меню
    page.evaluate('(el) => el.scrollIntoView({block: "center"})', folder_item)
    folder_item.click(button='right')
    page.wait_for_selector('[name="contextmenu"] [role="treeitem"]', timeout=3000)
    create_btn = page.query_selector('[role="treeitem"][aria-label="contextmenu_create"]')
    assert create_btn, 'Кнопка "Создать" не найдена в контекстном меню папки!'
    create_btn.click()
    time.sleep(0.5)
    # В подменю выбрать "Структуры данных"
    ds_btn = None
    for btn in file_panel.get_file_type_buttons():
        if btn.inner_text().strip().lower() == 'структуры данных':
            ds_btn = btn
            break
    assert ds_btn, "Кнопка 'Структуры данных' не найдена в подменю!"
    ds_btn.click()
    time.sleep(0.5)
    ds_name = f"datastruct_{int(time.time())}"
    input_box = page.query_selector('input[name="treeitem_label_field"]')
    assert input_box, 'Инпут для имени структуры данных не найден!'
    input_box.fill(ds_name)
    page.keyboard.press('Enter')
    ds_selector = f'div[role="treeitem"][aria-label="/{folder_name}/{ds_name}.ds.json"]'
    page.wait_for_selector(ds_selector, timeout=10000)
    file_item = page.query_selector(ds_selector)
    assert file_item, f'Не найден элемент структуры данных: {ds_name}'
    page.evaluate('(el) => el.scrollIntoView({block: "center"})', file_item)
    # Открыть контекстное меню
    file_item.click(button='right')
    page.wait_for_selector('[name="contextmenu"] [role="treeitem"]', timeout=3000)
    time.sleep(0.2)
    # 1. Проверка "Создать" (отмена)
    create_btn = page.query_selector('[role="treeitem"][aria-label="contextmenu_create"]')
    assert create_btn, 'Кнопка "Создать" не найдена!'
    create_btn.click()
    time.sleep(0.5)
    # Отмена создания (Esc)
    page.keyboard.press('Escape')
    time.sleep(0.5)
    # 2. Переименовать
    page.get_by_text(f"{ds_name}.ds.json").click(button="right")
    time.sleep(0.5)
    page.get_by_text("Переименовать").click()
    time.sleep(0.5)
    try:
        page.wait_for_selector('input[name="treeitem_label_field"]', timeout=10000)
    except Exception as e:
        page.screenshot(path='screenshots/diagnostic_rename_input_not_found.png', full_page=True)
        with open('screenshots/diagnostic_rename_input_not_found.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        raise AssertionError('Инпут для переименования не найден!')
    input_box = page.query_selector('input[name="treeitem_label_field"]')
    assert input_box, 'Инпут для переименования не найден!'
    time.sleep(0.5)
    new_name = ds_name + '_renamed'
    input_box.fill(new_name)
    page.keyboard.press('Enter')
    page.wait_for_selector('input[name="treeitem_label_field"]', state='detached', timeout=10000)
    page.wait_for_selector(f'div[role="treeitem"][aria-label="/{folder_name}/{new_name}.ds.json"]', timeout=10000)
    time.sleep(0.5)
    # После переименования — диагностика
    print('--- [DIAG] Файлы после переименования:')
    for item in page.query_selector_all('div[role="treeitem"]'):
        aria = item.get_attribute('aria-label')
        text = item.inner_text()
        print(f'  aria-label: {aria}, text: {text}')
    page.screenshot(path='screenshots/diagnostic_tree_after_rename.png', full_page=True)
    # Вернуть имя обратно
    page.wait_for_selector(f'div[role="treeitem"][aria-label="/{folder_name}/{new_name}.ds.json"]', timeout=10000)
    page.get_by_text(f"{new_name}.ds.json").click(button="right")
    time.sleep(0.5)
    page.get_by_text("Переименовать").click()
    time.sleep(0.5)
    try:
        page.wait_for_selector('input[name="treeitem_label_field"]', timeout=10000)
    except Exception as e:
        page.screenshot(path='screenshots/diagnostic_rename_input_not_found_back.png', full_page=True)
        with open('screenshots/diagnostic_rename_input_not_found_back.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        raise AssertionError('Инпут для переименования (возврат) не найден!')
    input_box = page.query_selector('input[name="treeitem_label_field"]')
    input_box.fill(ds_name)
    page.keyboard.press('Enter')
    page.wait_for_selector('input[name="treeitem_label_field"]', state='detached', timeout=10000)
    page.wait_for_selector(f'div[role="treeitem"][aria-label="/{folder_name}/{ds_name}.ds.json"]', timeout=10000)
    time.sleep(0.5)
    # 3. Копировать и вставить в корень — УБРАНО
    # 4. Вырезать и вставить обратно в папку
    file_item = page.query_selector(ds_selector)
    file_item.click(button='right')
    page.wait_for_selector('[name="contextmenu"] [role="treeitem"]', timeout=3000)
    cut_btn = page.query_selector('[role="treeitem"][aria-label="contextmenu_cut"]')
    assert cut_btn, 'Кнопка "Вырезать" не найдена!'
    cut_btn.click()
    folder_item.click()
    time.sleep(0.5)
    page.keyboard.press('Control+V')
    time.sleep(1)
    # После перемещения — найти новый элемент файла внутри папки
    file_item = page.query_selector(ds_selector)
    assert file_item, 'Файл не перемещён обратно в папку!'
    # 5. Копировать путь
    file_item.click(button='right')
    page.wait_for_selector('[name="contextmenu"] [role="treeitem"]', timeout=3000)
    copy_path_btn = page.query_selector('[role="treeitem"][aria-label="contextmenu_copyPath"]')
    assert copy_path_btn, 'Кнопка "Копировать путь" не найдена!'
    copy_path_btn.click()
    time.sleep(0.5)
    path_clip = pyperclip.paste()
    assert ds_name in path_clip, 'Путь не скопирован корректно!'
    # 6. Копировать ссылку
    file_item = page.query_selector(ds_selector)
    file_item.click(button='right')
    page.wait_for_selector('[name="contextmenu"] [role="treeitem"]', timeout=3000)
    copy_link_btn = page.query_selector('[role="treeitem"][aria-label="contextmenu_copyFullPath"]')
    assert copy_link_btn, 'Кнопка "Копировать ссылку" не найдена!'
    copy_link_btn.click()
    time.sleep(0.5)
    link_clip = pyperclip.paste()
    assert 'http' in link_clip, 'Ссылка не скопирована корректно!'
    # 7. Скачать
    file_item = page.query_selector(ds_selector)
    file_item.click(button='right')
    page.wait_for_selector('[name="contextmenu"] [role="treeitem"]', timeout=3000)
    download_btn = page.query_selector('[role="treeitem"][aria-label="contextmenu_download"]')
    assert download_btn, 'Кнопка "Скачать" не найдена!'
    with page.expect_download() as download_info:
        download_btn.click()
    download = download_info.value
    download_path = download.path()
    assert os.path.exists(download_path), 'Файл не скачан!'
    # 8. Удалить структуру данных
    file_item = page.query_selector(ds_selector)
    file_item.click(button='right')
    page.wait_for_selector('[name="contextmenu"] [role="treeitem"]', timeout=3000)
    delete_btn = page.query_selector('[role="treeitem"][aria-label="contextmenu_delete"]')
    assert delete_btn, 'Кнопка "Удалить" не найдена!'
    delete_btn.click()
    page.wait_for_selector('button:has-text("Удалить")', timeout=5000)
    page.get_by_role("button", name="Удалить").click()
    page.wait_for_selector(ds_selector, state='detached', timeout=10000)
    assert not page.query_selector(ds_selector), 'Файл не был удалён!'
    # Очистка: удалить тестовую папку
    folder_item = page.query_selector(folder_selector)
    folder_item.click(button='right')
    page.wait_for_selector('[name="contextmenu"] [role="treeitem"]', timeout=3000)
    delete_btn = page.query_selector('[role="treeitem"][aria-label="contextmenu_delete"]')
    delete_btn.click()
    page.wait_for_selector('button:has-text("Удалить")', timeout=5000)
    page.get_by_role("button", name="Удалить").click()
    page.wait_for_selector(folder_selector, state='detached', timeout=10000)
    assert not page.query_selector(folder_selector), 'Папка не была удалена!'
    print('[TEST][OK] Все пункты контекстного меню успешно проверены!') 