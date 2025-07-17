import time
import pytest

def test_create_data_struct_and_add_attribute(login_page):
    page = login_page
    # 0. Переход в первый доступный проект
    page.wait_for_selector('div[aria-label="projects_card"]', timeout=15000)
    cards = page.query_selector_all('div[aria-label="projects_card"]')
    assert cards, 'Нет доступных проектов!'
    first_card = cards[0]
    link = first_card.query_selector('a[aria-label="projects_card_link"]')
    assert link, 'Не найдена ссылка на проект!'
    link.click()
    page.wait_for_load_state('networkidle')
    # 1. Открыть файловую панель и создать структуру данных
    page.get_by_role("button", name="board_toolbar_filemanager_button").click()
    page.get_by_role("button", name="filemanager_create_button").click()
    page.get_by_role("treeitem", name="data_structure").locator("div").nth(2).click()
    file_name = f"datastruct_{int(time.time())}"
    page.get_by_role("textbox", name="treeitem_label_field").fill(file_name)
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    # 2. Создать схему
    page.get_by_role("button", name="datastructureeditor_create_schema_button").click()
    schema_name = f"schema_{int(time.time())}"
    page.get_by_role("textbox", name="treeitem_label_field").click()
    page.get_by_role("textbox", name="treeitem_label_field").fill(schema_name)
    page.get_by_role("textbox", name="treeitem_label_field").press("Enter")
    # 2.1. Заполнить описание схемы
    page.get_by_role("textbox", name="description").fill("Описание схемы автотестом")
    # 3. Добавить атрибут
    page.get_by_role("button", name="datastructureeditor_create_attribute_button").click()
    page.get_by_role("textbox", name="attributes.0.name").fill("test")
    page.get_by_role("textbox", name="attributes.0.name").press("Enter")
    # 3.1. Выбрать тип через выпадающий список
    page.get_by_role("button", name="textfield_arrow_button").click()
    page.get_by_text("string").click()
    # 3.2. Заполнить описание атрибута
    page.get_by_role("textbox", name="attributes.0.schema.description").click()
    page.get_by_role("textbox", name="attributes.0.schema.description").fill("Описание атрибута автотестом")
    # 3.3. Сделать атрибут обязательным
    page.get_by_role("button", name="datastructureeditor_required_attribute_button").click()
    time.sleep(5) 