"""
Локаторы для работы с канвасом
"""


class CanvasLocators:
    """Локаторы для работы с канвасом диаграммы"""
    
    # Основной канвас
    CANVAS = 'canvas'
    
    # Компоненты на канвасе
    INPUT_COMPONENT = 'text="Input"'
    OUTPUT_COMPONENT = 'text="Output"'
    FUNCTION_COMPONENT = 'text="Function"'
    LOOP_COMPONENT = 'text="Loop"'
    HTTP_COMPONENT = 'text="HTTP"'
    FLOW_PROC_COMPONENT = 'text="Flow_proc"'
    
    # Поиск компонентов
    ALL_COMPONENTS = 'text="Input", text="Output", text="Function", text="Loop", text="HTTP", text="Flow_proc"'
    
    # Координаты для кликов (примерные позиции)
    CANVAS_CENTER = {"x": 0.5, "y": 0.5}
    CANVAS_TOP_LEFT = {"x": 0.3, "y": 0.3}
    CANVAS_TOP_RIGHT = {"x": 0.7, "y": 0.3}
    CANVAS_TOP_CENTER = {"x": 0.5, "y": 0.2}
    
    @staticmethod
    def get_component_by_text(component_text: str) -> str:
        """Получить локатор для компонента по тексту"""
        return f'text="{component_text}"'
    
    @staticmethod
    def get_canvas_position(x_percent: float, y_percent: float) -> dict:
        """Получить позицию на канвасе в процентах"""
        return {"x": x_percent, "y": y_percent}
