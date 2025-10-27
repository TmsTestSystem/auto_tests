"""
Тесты для всех методов создания файлов из FilePanelAPI
"""

import pytest
import sys
import os
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "api"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "utils"))

from custom_logger import setup_test_logger


class TestFilePanelCreation:
    """Тесты всех методов создания файлов из FilePanelAPI"""
    
    @classmethod
    def setup_class(cls):
        """Настройка логгера для всего класса тестов"""
        cls.logger = setup_test_logger("file_panel_test")
    
    @classmethod
    def teardown_class(cls):
        """Закрытие логгера после всех тестов класса"""
        cls.logger.close()
    
    def test_create_folder(self, file_panel_api):
        """Тест создания папки"""
        folder_name = "test_folder_api"
        
        self.__class__.logger.info(f"[TEST] Создание папки: {folder_name}")
        try:
            result = file_panel_api.create_folder(folder_name)
            self.__class__.logger.info(f"[SUCCESS] Папка создана: {result}")
            
            self.__class__.logger.info(f"[INFO] Папка {folder_name} оставлена для просмотра")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при создании папки: {e}")
            raise
    
    def test_create_regular_file(self, file_panel_api):
        """Тест создания обычного файла"""
        file_name = "test_file.txt"
        
        self.__class__.logger.info(f"[TEST] Создание обычного файла: {file_name}")
        try:
            result = file_panel_api.create_file(file_name)
            self.__class__.logger.info(f"[SUCCESS] Обычный файл создан: {result}")
            
            self.__class__.logger.info(f"[INFO] Файл {file_name} оставлен для просмотра")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при создании обычного файла: {e}")
            raise
    
    def test_create_process_file(self, file_panel_api):
        """Тест создания файла процесса"""
        process_name = "test_process"
        
        self.__class__.logger.info(f"[TEST] Создание файла процесса: {process_name}")
        try:
            result = file_panel_api.create_process_file(process_name)
            self.__class__.logger.info(f"[SUCCESS] Файл процесса создан: {result}")
            
            self.__class__.logger.info(f"[INFO] Файл оставлен для просмотра")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при создании файла процесса: {e}")
            raise
    
    def test_create_data_structure_file(self, file_panel_api):
        """Тест создания файла структуры данных"""
        structure_name = "test_structure"
        
        self.__class__.logger.info(f"[TEST] Создание файла структуры данных: {structure_name}")
        try:
            result = file_panel_api.create_data_structure_file(structure_name)
            self.__class__.logger.info(f"[SUCCESS] Файл структуры данных создан: {result}")
            
            self.__class__.logger.info(f"[INFO] Файл оставлен для просмотра")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при создании файла структуры данных: {e}")
            raise
    
    def test_create_db_connection_file(self, file_panel_api):
        """Тест создания файла подключения к БД"""
        db_name = "test_db_connection"
        
        self.__class__.logger.info(f"[TEST] Создание файла подключения к БД: {db_name}")
        try:
            result = file_panel_api.create_db_connection_file(db_name)
            self.__class__.logger.info(f"[SUCCESS] Файл подключения к БД создан: {result}")
            
            self.__class__.logger.info(f"[INFO] Файл оставлен для просмотра")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при создании файла подключения к БД: {e}")
            raise
    
    def test_create_decision_table_file(self, file_panel_api):
        """Тест создания файла таблицы принятия решений"""
        table_name = "test_decision_table"
        
        self.__class__.logger.info(f"[TEST] Создание файла таблицы принятия решений: {table_name}")
        try:
            result = file_panel_api.create_decision_table_file(table_name)
            self.__class__.logger.info(f"[SUCCESS] Файл таблицы принятия решений создан: {result}")
            
            self.__class__.logger.info(f"[INFO] Файл оставлен для просмотра")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при создании файла таблицы принятия решений: {e}")
            raise
    
    def test_create_python_script_file(self, file_panel_api):
        """Тест создания Python скрипта"""
        script_name = "test_python_script"
        
        self.__class__.logger.info(f"[TEST] Создание Python скрипта: {script_name}")
        try:
            result = file_panel_api.create_python_script_file(script_name)
            self.__class__.logger.info(f"[SUCCESS] Python скрипт создан: {result}")
            
            try:
                file_panel_api.delete_file(f"/{script_name}.py")
                self.__class__.logger.info(f"[CLEANUP] Python скрипт {script_name}.py удален")
            except Exception as cleanup_error:
                self.__class__.logger.warning(f"[WARN] Ошибка при удалении Python скрипта: {cleanup_error}")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при создании Python скрипта: {e}")
            raise
    
    def test_create_test_file(self, file_panel_api):
        """Тест создания файла тестов"""
        test_name = "test_test_file"
        
        self.__class__.logger.info(f"[TEST] Создание файла тестов: {test_name}")
        try:
            result = file_panel_api.create_test_file(test_name)
            self.__class__.logger.info(f"[SUCCESS] Файл тестов создан: {result}")
            
            self.__class__.logger.info(f"[INFO] Файл оставлен для просмотра")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при создании файла тестов: {e}")
            raise
    
    def test_rename_file(self, file_panel_api):
        """Тест переименования файла"""
        original_name = "test_rename_original.txt"
        new_name = "test_rename_new.txt"
        
        self.__class__.logger.info(f"[TEST] Переименование файла: {original_name} -> {new_name}")
        try:
            file_panel_api.create_file(original_name)
            self.__class__.logger.info(f"[SETUP] Исходный файл создан: {original_name}")
            
            result = file_panel_api.rename_file(f"/{original_name}", f"/{new_name}")
            self.__class__.logger.info(f"[SUCCESS] Файл переименован: {result}")
            
            self.__class__.logger.info(f"[INFO] Переименованный файл оставлен для просмотра")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при переименовании файла: {e}")
            raise
    
    def test_delete_file(self, file_panel_api):
        """Тест удаления файла"""
        file_name = "test_delete_file.txt"
        
        self.__class__.logger.info(f"[TEST] Удаление файла: {file_name}")
        try:
            file_panel_api.create_file(file_name)
            self.__class__.logger.info(f"[SETUP] Файл для удаления создан: {file_name}")
            
            result = file_panel_api.delete_file(f"/{file_name}")
            self.__class__.logger.info(f"[SUCCESS] Файл удален: {result}")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при удалении файла: {e}")
            raise
    
    def test_get_file_tree(self, file_panel_api):
        """Тест получения дерева файлов"""
        self.__class__.logger.info(f"[TEST] Получение дерева файлов")
        try:
            result = file_panel_api.get_file_tree()
            self.__class__.logger.info(f"[SUCCESS] Дерево файлов получено")
            self.__class__.logger.info(f"[INFO] Количество элементов в корне: {len(result) if isinstance(result, list) else len(result.get('items', []))}")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при получении дерева файлов: {e}")
            raise
    
    def test_get_file_content(self, file_panel_api):
        """Тест получения содержимого файла"""
        file_name = "test_content_file.txt"
        
        self.__class__.logger.info(f"[TEST] Получение содержимого файла: {file_name}")
        try:
            # Сначала создаем файл
            file_panel_api.create_file(file_name)
            self.__class__.logger.info(f"[SETUP] Файл для чтения создан: {file_name}")
            
            # Получаем содержимое
            result = file_panel_api.get_file_content(f"/{file_name}")
            self.__class__.logger.info(f"[SUCCESS] Содержимое файла получено: {result}")
            
            # Очистка
            file_panel_api.delete_file(f"/{file_name}")
            self.__class__.logger.info(f"[CLEANUP] Файл {file_name} удален")
                
        except Exception as e:
            self.__class__.logger.error(f"[ERROR] Ошибка при получении содержимого файла: {e}")
            raise