from datetime import datetime
from pathlib import Path


class CustomLogger:
    def __init__(self, log_file_path):
        self.log_file = open(log_file_path, 'w', encoding='utf-8')
        
    def info(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"{timestamp} - {message}\n"
        self.log_file.write(log_line)
        self.log_file.flush()
        print(message)  # Также выводим в консоль
        
    def warning(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"{timestamp} - [WARNING] {message}\n"
        self.log_file.write(log_line)
        self.log_file.flush()
        print(f"[WARNING] {message}")
        
    def error(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"{timestamp} - [ERROR] {message}\n"
        self.log_file.write(log_line)
        self.log_file.flush()
        print(f"[ERROR] {message}")
        
    def close(self):
        self.log_file.close()


def setup_test_logger(test_name: str = "test"):
    """Создает логгер для теста с автоматическим именем файла"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(__file__).parent.parent / "logs" / f"{test_name}_{timestamp}.log"
    log_file.parent.mkdir(exist_ok=True)
    
    return CustomLogger(log_file)
