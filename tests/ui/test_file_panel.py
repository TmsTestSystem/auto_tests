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

# Удалены вспомогательные функции создания файлов и папок, теперь только тесты


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
    folder_name = file_panel.create_folder(f"autofolder_{int(time.time())}")
    if folder_name:
            created += 1
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
        file_name = file_panel.create_file_of_type(f"autofile_{idx}_{int(time.time())}", aria, text)
        if file_name:
            created += 1
    print(f"[CREATE_FILES] Всего успешно создано: {created}")
    save_screenshot(page, "test_create_all_file_types")


# Удалён тест test_create_and_delete_all_types_universal 