"""
Базовый класс для локаторов
"""

from typing import Dict, List


class BaseLocators:
    """Базовый класс для всех локаторов"""
    
    @staticmethod
    def get_locator_with_text(text: str) -> str:
        """Получить локатор с текстом"""
        return f'text="{text}"'
    
    @staticmethod
    def get_locator_with_aria_label(label: str) -> str:
        """Получить локатор с aria-label"""
        return f'[aria-label="{label}"]'
    
    @staticmethod
    def get_locator_with_name(name: str) -> str:
        """Получить локатор с name"""
        return f'[name="{name}"]'
    
    @staticmethod
    def get_locator_with_role(role: str, name: str = None) -> str:
        """Получить локатор с role"""
        if name:
            return f'[role="{role}"][name="{name}"]'
        return f'[role="{role}"]'
    
    @staticmethod
    def get_locator_with_testid(testid: str) -> str:
        """Получить локатор с data-testid"""
        return f'[data-testid="{testid}"]'
    
    @staticmethod
    def combine_locators(*locators: str) -> str:
        """Объединить несколько локаторов через запятую"""
        return ', '.join(locators)
    
    @staticmethod
    def get_fallback_locators(primary: str, *fallbacks: str) -> List[str]:
        """Получить список локаторов с основным и запасными"""
        return [primary] + list(fallbacks)
