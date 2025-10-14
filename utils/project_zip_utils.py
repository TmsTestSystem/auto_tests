import os
import zipfile
import tempfile
from pathlib import Path
import shutil


def create_project_zip(project_folder_path: str, output_zip_path: str = None) -> str:
    """
    Создает ZIP архив из папки project_for_tests.
    
    Args:
        project_folder_path: Путь к папке project_for_tests
        output_zip_path: Путь для сохранения ZIP архива (опционально)
    
    Returns:
        Путь к созданному ZIP архиву
    """
    if not os.path.exists(project_folder_path):
        raise FileNotFoundError(f"Папка {project_folder_path} не найдена")
    
    # Если путь не указан, создаем временный файл
    if output_zip_path is None:
        temp_dir = tempfile.gettempdir()
        output_zip_path = os.path.join(temp_dir, "project_for_tests.zip")
    
    # Удаляем существующий архив, если он есть
    if os.path.exists(output_zip_path):
        os.remove(output_zip_path)
    
    print(f"[ZIP] Создаю архив из {project_folder_path} в {output_zip_path}")
    
    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Проходим по всем файлам и папкам в project_for_tests
        for root, dirs, files in os.walk(project_folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                # Относительный путь от project_for_tests
                arcname = os.path.relpath(file_path, project_folder_path)
                zipf.write(file_path, arcname)
                print(f"[ZIP] Добавлен файл: {arcname}")
    
    print(f"[ZIP] Архив успешно создан: {output_zip_path}")
    return output_zip_path


def cleanup_temp_zip(zip_path: str):
    """
    Удаляет временный ZIP архив.
    
    Args:
        zip_path: Путь к ZIP архиву для удаления
    """
    try:
        if os.path.exists(zip_path):
            os.remove(zip_path)
            print(f"[ZIP] Временный архив удален: {zip_path}")
    except Exception as e:
        print(f"[WARNING] Не удалось удалить временный архив {zip_path}: {e}")


def get_project_folder_path() -> str:
    """
    Получает путь к папке project_for_tests относительно корня проекта.
    
    Returns:
        Абсолютный путь к папке project_for_tests
    """
    # Получаем путь к корню проекта (где находится conftest.py)
    project_root = Path(__file__).parent.parent
    project_folder = project_root / "project_for_tests"
    
    if not project_folder.exists():
        raise FileNotFoundError(f"Папка project_for_tests не найдена в {project_root}")
    
    return str(project_folder)

