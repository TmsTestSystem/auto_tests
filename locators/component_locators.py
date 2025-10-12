"""
Локаторы для компонентов диаграммы
"""


class ComponentLocators:
    """Локаторы для работы с компонентами диаграммы"""
    
    # Основные компоненты
    INPUT = 'text="Input"'
    OUTPUT = 'text="Output"'
    FUNCTION = 'text="Function"'
    LOOP = 'text="Loop"'
    HTTP = 'text="HTTP"'
    FLOW_PROC = 'text="Flow_proc"'
    
    # Конфигурационные поля
    CONFIG_FUNCTION = 'textbox[name="config.function"]'
    CONFIG_URL = 'textbox[name="config.url"]'
    CONFIG_METHOD = 'textbox[name="config.method"]'
    CONFIG_LOOP_END = 'textbox[name="config.loop_end.0"]'
    
    # Поля ввода данных
    INPUTS_DATA_VALUE = 'textbox[name="inputs_config.data.value"]'
    INPUTS_N_VALUE = 'textbox[name="inputs_config.n.value"]'
    INPUTS_HEADERS_VALUE_NAME = 'textbox[name="inputs_config.headers.value.0.name"]'
    INPUTS_ITERATOR = 'textbox[name="inputs_config."]'
    
    # Кнопки действий
    SELECT_FILE_BUTTON = 'button[aria-label="textfield_select_file_button"]'
    ADD_BUTTON = 'button[aria-label="extendable_list_add_button"]'
    
    # Переменные в Input компоненте
    VARIABLES_CREATE_BUTTON = 'button[aria-label="variables_create_button"]'
    VARIABLES_ITEM_SETTINGS_BUTTON = 'button[aria-label="variables_item_settings_button"]'
    
    # Assignment компонент
    ASSIGNMENT_TARGET_FIELD = 'textbox[name="config.assignments.{i}.target"]'
    ASSIGNMENT_VALUE_FIELD = 'textbox[name="config.assignments.{i}.value"]'
    
    # Output компонент
    OUTPUT_DATA_FIELD = 'textbox[name="config.data"]'
    
    # Панель деталей
    DETAILS_PANEL = '[aria-label="diagram_details_panel"]'
    DETAILS_PANEL_SWITCHER = 'button[aria-label="diagram_details_panel_switcher"]'
    ELEMENT_NAME_HEADING = 'heading[name="diagram_element_name"]'
    
    # Вкладки
    COMPONENT_TAB = 'text="Компонент", exact=True'
    PROCESS_TAB = 'text="Процесс", exact=True'
    ANALYSIS_TAB = 'text="Анализ"'
    
    # Кнопки просмотра
    FULL_VIEW_BUTTON = 'button[aria-label="formitem_full_view_button"]'
    
    # Fallback локаторы
    DATA_VALUE_FALLBACK = 'textarea[name*="data"], input[name*="data"], textarea[aria-label*="data"]'
    URL_FIELD_FALLBACK = 'textarea[name="config.url"], input[name="config.url"]'
    METHOD_FIELD_FALLBACK = 'textarea[name="config.method"], select[name="config.method"]'
    HTTP_BODY_FIELD = 'textarea[name="body"], input[name="body"]'
    HTTP_EXPRESSION_BUTTON = 'button[aria-label*="expression"], button[title*="expression"]'
    HTTP_HEADERS_NAME_FIELD = 'textbox[name="inputs_config.headers.value.0.name"]'
    HTTP_HEADERS_VALUE_FIELD = 'textbox[name="inputs_config.headers.value.0.value"]'
    
    # Loop специфичные
    LOOP_START_FIELD = '.TextField__TextField___-71sY.TextField__TextField_invalid___KA8-t > .TextField__InputWrapper___anui0'
    
    # Функции и опции
    FUNCTION_OPTION_DIV = 'treeitem > div:has-text("Function")'
    FUNCTION_LABEL_PRIMARY = '.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Function")'
    
    @staticmethod
    def get_component_by_name(name: str) -> str:
        """Получить локатор для компонента по имени"""
        return f'text="{name}"'
    
    @staticmethod
    def get_function_option_by_name(function_name: str) -> str:
        """Получить локатор для опции функции по имени"""
        return f'treeitem[name="{function_name}"] > label[aria-label="treeitem_label"]'
    
    @staticmethod
    def get_http_method_option(method: str) -> str:
        """Получить локатор для HTTP метода"""
        return f'treeitem[name="{method}"] > div:nth-child(2)'
