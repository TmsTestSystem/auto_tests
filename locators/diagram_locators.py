"""
Локаторы для работы с диаграммами
"""


class DiagramLocators:
    """Локаторы для работы с диаграммами"""
    
    # Основные элементы диаграммы
    CREATE_BUTTON = 'button[aria-label="diagram_create_button"]'
    DETAILS_PANEL = '[aria-label="diagram_details_panel"]'
    DETAILS_PANEL_SWITCHER = 'button[aria-label="diagram_details_panel_switcher"]'
    ADD_BUTTON = '[aria-label="diagram_element_details"] div:has-text("Добавить")'
    
    # Элементы диаграммы
    START_PROCESS = 'text="Старт процесса"'
    END_PROCESS = 'text="Конец процесса"'
    INPUT_COMPONENT = 'text="Input"'
    OUTPUT_COMPONENT = 'text="Output"'
    FUNCTION_COMPONENT = 'text="Function"'
    LOOP_COMPONENT = 'text="Loop"'
    HTTP_COMPONENT = 'text="HTTP"'
    FLOW_PROC_COMPONENT = 'text="Flow_proc"'
    
    # Вкладки в панели деталей
    COMPONENT_TAB = 'text="Компонент", exact=True'
    PROCESS_TAB = 'text="Процесс", exact=True'
    ANALYSIS_TAB = 'text="Анализ"'
    ACTIVE_TAB = '.active, [aria-selected="true"]'
    
    # Поля конфигурации компонентов
    FUNCTION_SELECT_FILE_BUTTON = 'button[aria-label="textfield_select_file_button"]'
    FUNCTION_CONFIG_FIELD = 'textbox[name="config.function"]'
    FUNCTION_OPTION_BY_NAME = 'treeitem[name="{name}"] > label[aria-label="treeitem_label"]'
    DROPDOWN_TREE = 'div[role="tree"].TextField__Menu___pmHMx'
    
    # Поля ввода данных
    DATA_VALUE_FIELD = 'textbox[name="inputs_config.data.value"]'
    DATA_VALUE_FALLBACK = 'textarea[name*="data"], input[name*="data"], textarea[aria-label*="data"]'
    N_VALUE_FIELD = 'textbox[name="inputs_config.n.value"]'
    URL_FIELD = 'textbox[name="config.url"]'
    URL_FIELD_FALLBACK = 'textarea[name="config.url"], input[name="config.url"]'
    METHOD_FIELD = 'textbox[name="config.method"]'
    METHOD_FIELD_FALLBACK = 'textarea[name="config.method"], select[name="config.method"]'
    
    # HTTP методы
    HTTP_GET_OPTION = 'treeitem[name="GET"] > div:nth-child(2)'
    HTTP_POST_OPTION = 'treeitem[name="POST"] > div:nth-child(2)'
    
    # Заголовки HTTP
    HEADERS_VALUE_NAME = 'textbox[name="inputs_config.headers.value.0.name"]'
    
    # Loop компонент
    LOOP_START_FIELD = '.TextField__TextField___-71sY.TextField__TextField_invalid___KA8-t > .TextField__InputWrapper___anui0'
    LOOP_END_FIELD = 'textbox[name="config.loop_end.0"]'
    LOOP_ITERATOR_FIELD = 'textbox[name="inputs_config."]'
    
    # Функции и опции
    FUNCTION_OPTION_DIV = 'treeitem > div:has-text("Function")'
    FUNCTION_LABEL_PRIMARY = '.TreeItem__LabelPrimary___vzajD[aria-label="treeitem_label"]:has-text("Function")'
    
    # Кнопки действий
    EXTENDABLE_LIST_ADD_BUTTON = 'button[aria-label="extendable_list_add_button"]'
    FULL_VIEW_BUTTON = 'button[aria-label="formitem_full_view_button"]'
    
    # Элемент заголовка
    DIAGRAM_ELEMENT_NAME = 'heading[name="diagram_element_name"]'
    
    @staticmethod
    def get_function_option_by_name(function_name: str) -> str:
        """Получить локатор для опции функции по имени"""
        return f'treeitem[name="{function_name}"] > label[aria-label="treeitem_label"]'
    
    @staticmethod
    def get_component_by_name(component_name: str) -> str:
        """Получить локатор для компонента по имени"""
        return f'text="{component_name}"'
