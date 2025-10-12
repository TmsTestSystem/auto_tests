"""
Локаторы для панели инструментов (Toolbar)
"""


class ToolbarLocators:
    """Локаторы для работы с панелью инструментов"""
    
    # Основная панель инструментов
    BOARD_TOOLBAR_PANEL = '[aria-label="board_toolbar_panel"]'
    
    # Кнопки панели инструментов
    TOOLBAR_BUTTONS = 'button[title], button[aria-label], .toolbar button'
    
    # Кнопки создания
    DIAGRAM_CREATE_BUTTON = 'button[aria-label="diagram_create_button"]'
    FILE_MANAGER_BUTTON = 'button[aria-label="board_toolbar_filemanager_button"]'
    
    # Навигационные элементы
    BREADCRUMBS = '.breadcrumb, [aria-label*="breadcrumb"]'
    BREADCRUMBS_ALT = '.breadcrumb, [aria-label*="навигация"], nav'
    
    # Кнопки действий
    RUN_DIAGRAM_BUTTON = 'button[aria-label*="run"], button[title*="запуск"], button[title*="выполнить"]'
    DIAGRAM_PLAY_BUTTON = 'button[aria-label="diagram_play_button"]'
    TOOLBAR_RUN_BUTTON = 'button[aria-label="toolbar_run_button"]'
    
    # Панели интерфейса
    LEFT_PANEL = '.left-panel, .sidebar-left, [data-panel="left"]'
    RIGHT_PANEL = '.right-panel, .sidebar-right, [data-panel="right"]'
    BOTTOM_PANEL = '.bottom-panel, .status-bar, .footer'
    
    # Вкладки
    TABS = '[role="tab"], .tab, .file-tab'
    
    # Редактор
    EDITOR = '.editor, .monaco-editor, [role="textbox"]'
    
    # Меню
    MENU_BUTTONS = '[role="menubar"] button, .menu button, [aria-label*="меню"]'
    CONTEXT_MENU = '[role="menu"], .context-menu, .dropdown-menu'
    
    @staticmethod
    def get_toolbar_button_by_title(title: str) -> str:
        """Получить локатор для кнопки панели инструментов по title"""
        return f'button[title="{title}"]'
    
    @staticmethod
    def get_toolbar_button_by_aria_label(label: str) -> str:
        """Получить локатор для кнопки панели инструментов по aria-label"""
        return f'button[aria-label="{label}"]'
