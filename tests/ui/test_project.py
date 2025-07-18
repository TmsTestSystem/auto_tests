import os
import time
import pytest
from pages.project_page import ProjectPage
from conftest import save_screenshot


def test_create_project_and_check_toolbar(login_page):
    page = login_page
    project_code = f"autotest{int(time.time())}"
    project_title = f"Автотест {int(time.time())}"
    project_page = ProjectPage(page)
    project_page.open_create_project_modal()
    project_page.create_project(
        title=project_title,
        code=project_code,
        git="git@github.com:IlyaKurilin/spr.git",
        default_branch="main"
    )
    project_page.wait_modal_close()
    prj = None
    for _ in range(30):
        prj = project_page.find_project_in_list(project_title)
        if prj:
            break
        time.sleep(0.5)
    assert prj is not None, f"Проект с названием {project_title} не найден в списке после создания!"
    prj.click()
    page.wait_for_load_state('networkidle')
    toolbar_labels = [
        'board_toolbar_filemanager_button',
        'board_toolbar_commit_button',
        'board_toolbar_tests_button',
        'board_toolbar_structures_button',
        'board_toolbar_search_button',
    ]
    found_labels = project_page.wait_for_toolbar_buttons(toolbar_labels)
    for label in toolbar_labels:
        assert label in found_labels, f'Кнопка с aria-label="{label}" не найдена на тулбаре проекта!'
    save_screenshot(page, "test_create_project_and_check_toolbar")


def test_parse_file_panel_buttons(login_page):
    page = login_page
    project_code = f"autotest{int(time.time())}"
    project_title = f"Автотест {int(time.time())}"
    project_page = ProjectPage(page)
    project_page.open_create_project_modal()
    project_page.create_project(
        title=project_title,
        code=project_code,
        git="git@github.com:IlyaKurilin/spr.git",
        default_branch="main"
    )
    project_page.wait_modal_close()
    prj = None
    for _ in range(30):
        prj = project_page.find_project_in_list(project_title)
        if prj:
            break
        time.sleep(0.5)
    assert prj is not None, f"Проект с названием {project_title} не найден в списке после создания!"
    prj.click()
    page.wait_for_load_state('networkidle')
    project_page.open_file_panel()
    print("\n[FILE_SIDEBAR] Кнопки в левом сайдбаре файлового менеджера:")
    buttons = project_page.get_file_sidebar_buttons()
    for btn in buttons:
        aria = btn.get_attribute('aria-label')
        text = btn.inner_text()
        attrs = page.evaluate('(el) => { const attrs = {}; for (const attr of el.attributes) { attrs[attr.name] = attr.value }; return attrs; }', btn)
        print(f"---\naria-label: {aria}\ntext: {text}\nattrs: {attrs}")
    save_screenshot(page, "test_parse_file_panel_buttons")
