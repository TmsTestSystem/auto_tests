"""
Локаторы для UI тестов
"""

from .file_panel_locators import FilePanelLocators
from .diagram_locators import DiagramLocators
from .canvas_locators import CanvasLocators
from .component_locators import ComponentLocators
from .modal_locators import ModalLocators
from .toolbar_locators import ToolbarLocators

__all__ = [
    'FilePanelLocators',
    'DiagramLocators', 
    'CanvasLocators',
    'ComponentLocators',
    'ModalLocators',
    'ToolbarLocators'
]
