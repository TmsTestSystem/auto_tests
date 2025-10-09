"""
Локаторы для панели файлов (File Panel)
"""


class FilePanelLocators:
    """Локаторы для работы с панелью файлов"""
    
    # Основные элементы панели файлов
    CREATE_BUTTON = '[aria-label*="создать"], [title*="создать"], button:has-text("+")'
    FILEMANAGER_CREATE_BUTTON = 'button[aria-label="filemanager_create_button"]'
    FILEMANAGER_SELECT_BUTTON = 'button[aria-label="filemanager_select_button"]'
    
    # Дерево файлов
    TREE_ITEMS = '.tree-item, [role="treeitem"]'
    TREEITEM_LABEL = '[aria-label="treeitem_label"]'
    TREEITEM_LABEL_FIELD = 'textbox[aria-label="treeitem_label_field"]'
    TREEITEM_BY_NAME = '[aria-label="treeitem_label"]:has-text("{name}")'
    TREEITEM_BY_PATH = '[aria-label="/{path}"]'
    
    # Контекстное меню
    CREATE_MENU = 'text="Создать", exact=True'
    FOLDER_MENU = 'text="Папка", exact=True'
    PYTHON_MENU = 'treeitem[name="python"] > label[aria-label="treeitem_label"]'
    
    # Редактор файлов
    EDITOR_VIEW = 'textbox[aria-label="editor_view"]'
    VIEW_LINES = '.view-lines'
    TEXTAREA_EDITOR = 'textarea[aria-label="editor_view"]'
    
    # База данных
    DATABASE_CONNECTION_INFO = '[aria-label="database_connection_info"]'
    
    # Специфичные для типов файлов
    PROCESS_MENU_ITEM = 'div[role="treeitem"], div.TreeItem__LabelPrimary___vzajD'
    DATA_STRUCTURE_CREATE_ATTRIBUTE_BUTTON = 'button[aria-label="datastructureeditor_create_attribute_button"]'
    
    # Дополнительные элементы интерфейса
    TREE_ITEMS = '.tree-item, [role="treeitem"]'
    CREATE_FILE_BUTTON = '[aria-label*="создать"], [title*="создать"], button:has-text("+")'
    
    @staticmethod
    def get_treeitem_by_name(name: str) -> str:
        """Получить локатор для элемента дерева по имени"""
        return f'[aria-label="treeitem_label"]:has-text("{name}")'
    
    @staticmethod
    def get_treeitem_by_path(path: str) -> str:
        """Получить локатор для элемента дерева по пути"""
        return f'[aria-label="/{path}"]'
