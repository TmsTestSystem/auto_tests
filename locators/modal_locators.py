"""
Локаторы для модальных окон
"""


class ModalLocators:
    """Локаторы для работы с модальными окнами"""
    
    # Основные модальные окна
    MODAL_CONTAINER = '[data-testid="Modal__Container"]'
    JSON_VIEW_MODAL = 'text="Просмотр JSON"'
    
    # Структура данных
    SCHEMA_TYPE_FIELD = 'textbox[name="schema.type"]'
    DATASTRUCTURE_SELECT_BUTTON = 'button[aria-label="datastructureview_select_button"]'
    DATASTRUCTURE_SETTINGS_SUBMIT_BUTTON = 'button[aria-label="datastructureeditor_settings_submit_button"]'
    DATASTRUCTURE_POPUP_SELECT_BUTTON = 'button[aria-label="datastructureeditor_popup_select_button"]'
    POPUP_TYPE_FIELD = 'textbox[name="popup.type"]'
    
    # Элементы в модальных окнах
    JSON_CONTENT = 'pre, code, .json-content'
    RESPONSE_SECTION = 'text="Ответ"'
    EXPRESSION_MODAL = '[role="dialog"], .modal, .expression-modal'
    JSON_MODAL = '[role="dialog"]:has-text("Просмотр JSON")'
    JSON_MODAL_VIEW_LINES = '[role="dialog"] .view-lines'
    MONACO_EDITOR = '.monaco-editor textarea, .view-lines, [data-testid="editor"]'
    MODAL_CLOSE_BUTTON = '[role="dialog"] button[aria-label="close"], [role="dialog"] .close-button'
    
    # Селекторы файлов в модальных окнах
    FILE_BY_NAME = '[data-testid="Modal__Container"] > text="{filename}"'
    
    # Toast уведомления
    TOAST = '[data-testid="toast"], .toast, [role="alert"]'
    MONACO_ALERT = '.monaco-alert'
    TOAST_SPECIFIC = '.Toast__Toast___ZqZzU[aria-label="toast"]'
    ALERT_WITH_CLASS = '[class*="alert"]'
    TOAST_WITH_CLASS = '[class*="toast"]'
    
    # Все возможные селекторы для toast
    TOAST_SELECTORS = [
        '[data-testid="toast"]',
        '.toast',
        '[role="alert"]',
        '.monaco-alert',
        '[class*="alert"]',
        '[class*="toast"]'
    ]
    
    @staticmethod
    def get_file_by_name(filename: str) -> str:
        """Получить локатор для файла в модальном окне по имени"""
        return f'[data-testid="Modal__Container"] > text="{filename}"'
    
    @staticmethod
    def get_json_content_selector() -> str:
        """Получить селектор для JSON контента"""
        return 'pre, code, .json-content'
