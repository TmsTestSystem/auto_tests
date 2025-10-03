"""
Fake HTTP Server для тестирования HTTP компонентов
Поддерживает методы: GET, POST, PUT, PATCH, DELETE
Валидирует заголовки запросов
"""
import json
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FakeHTTPRequestHandler(BaseHTTPRequestHandler):
    """Обработчик запросов для fake HTTP сервера"""
    
    def __init__(self, *args, **kwargs):
        # Данные для хранения состояния
        self.test_data = {
            "users": [
                {"id": 1, "name": "John Doe", "email": "john@example.com", "active": True},
                {"id": 2, "name": "Jane Smith", "email": "jane@example.com", "active": False},
                {"id": 3, "name": "Bob Johnson", "email": "bob@example.com", "active": True}
            ],
            "posts": [
                {"id": 1, "title": "First Post", "body": "This is the first post", "userId": 1},
                {"id": 2, "title": "Second Post", "body": "This is the second post", "userId": 2}
            ],
            "next_id": {"users": 4, "posts": 3}
        }
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Переопределяем логирование для более читаемого вывода"""
        logger.info(f"{self.address_string()} - {format % args}")
    
    def _validate_headers(self, required_headers=None):
        """Валидация заголовков запроса"""
        if required_headers is None:
            required_headers = ["Content-Type"]
        
        missing_headers = []
        for header in required_headers:
            if header not in self.headers:
                missing_headers.append(header)
        
        if missing_headers:
            self.send_error(400, f"Missing required headers: {', '.join(missing_headers)}")
            return False
        
        # Проверяем Content-Type для методов с телом
        if self.command in ["POST", "PUT", "PATCH"]:
            content_type = self.headers.get("Content-Type", "")
            if "application/json" not in content_type:
                self.send_error(400, "Content-Type must be application/json")
                return False
        
        return True
    
    def _send_json_response(self, data, status_code=200):
        """Отправка JSON ответа"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        
        response_json = json.dumps(data, indent=2)
        self.wfile.write(response_json.encode('utf-8'))
    
    def _get_request_body(self):
        """Получение тела запроса"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            return self.rfile.read(content_length).decode('utf-8')
        return ""
    
    def _parse_json_body(self):
        """Парсинг JSON тела запроса"""
        body = self._get_request_body()
        if body:
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON in request body")
                return None
        return {}
    
    def _get_resource_id(self, path):
        """Извлечение ID ресурса из пути"""
        path_parts = path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[1].isdigit():
            return int(path_parts[1])
        return None
    
    def do_GET(self):
        """Обработка GET запросов"""
        logger.info(f"GET request to {self.path}")
        
        # Валидация заголовков (GET не требует Content-Type)
        if not self._validate_headers([]):
            return
        
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        if len(path_parts) == 0:
            # Корневой путь - возвращаем информацию о сервере
            self._send_json_response({
                "message": "Fake HTTP Server",
                "version": "1.0.0",
                "endpoints": {
                    "users": "/users",
                    "posts": "/posts",
                    "user_by_id": "/users/{id}",
                    "post_by_id": "/posts/{id}"
                }
            })
        
        elif path_parts[0] == "users":
            if len(path_parts) == 1:
                # GET /users - получить всех пользователей
                self._send_json_response(self.test_data["users"])
            elif len(path_parts) == 2 and path_parts[1].isdigit():
                # GET /users/{id} - получить пользователя по ID
                user_id = int(path_parts[1])
                user = next((u for u in self.test_data["users"] if u["id"] == user_id), None)
                if user:
                    self._send_json_response(user)
                else:
                    self.send_error(404, f"User with ID {user_id} not found")
            else:
                self.send_error(400, "Invalid path")
        
        elif path_parts[0] == "posts":
            if len(path_parts) == 1:
                # GET /posts - получить все посты
                self._send_json_response(self.test_data["posts"])
            elif len(path_parts) == 2 and path_parts[1].isdigit():
                # GET /posts/{id} - получить пост по ID
                post_id = int(path_parts[1])
                post = next((p for p in self.test_data["posts"] if p["id"] == post_id), None)
                if post:
                    self._send_json_response(post)
                else:
                    self.send_error(404, f"Post with ID {post_id} not found")
            else:
                self.send_error(400, "Invalid path")
        
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        """Обработка POST запросов"""
        logger.info(f"POST request to {self.path}")
        
        # Валидация заголовков
        if not self._validate_headers(["Content-Type"]):
            return
        
        data = self._parse_json_body()
        if data is None:
            return
        
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        if path_parts[0] == "users":
            # POST /users - создать нового пользователя
            new_user = {
                "id": self.test_data["next_id"]["users"],
                "name": data.get("name", "Unknown"),
                "email": data.get("email", "unknown@example.com"),
                "active": data.get("active", True)
            }
            self.test_data["users"].append(new_user)
            self.test_data["next_id"]["users"] += 1
            
            self._send_json_response(new_user, 201)
            logger.info(f"Created user: {new_user}")
        
        elif path_parts[0] == "posts":
            # POST /posts - создать новый пост
            new_post = {
                "id": self.test_data["next_id"]["posts"],
                "title": data.get("title", "Untitled"),
                "body": data.get("body", ""),
                "userId": data.get("userId", 1)
            }
            self.test_data["posts"].append(new_post)
            self.test_data["next_id"]["posts"] += 1
            
            self._send_json_response(new_post, 201)
            logger.info(f"Created post: {new_post}")
        
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_PUT(self):
        """Обработка PUT запросов"""
        logger.info(f"PUT request to {self.path}")
        
        # Валидация заголовков
        if not self._validate_headers(["Content-Type"]):
            return
        
        data = self._parse_json_body()
        if data is None:
            return
        
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        if len(path_parts) == 2 and path_parts[1].isdigit():
            resource_id = int(path_parts[1])
            
            if path_parts[0] == "users":
                # PUT /users/{id} - полное обновление пользователя
                user_index = next((i for i, u in enumerate(self.test_data["users"]) if u["id"] == resource_id), None)
                if user_index is not None:
                    updated_user = {
                        "id": resource_id,
                        "name": data.get("name", "Unknown"),
                        "email": data.get("email", "unknown@example.com"),
                        "active": data.get("active", True)
                    }
                    self.test_data["users"][user_index] = updated_user
                    self._send_json_response(updated_user)
                    logger.info(f"Updated user: {updated_user}")
                else:
                    self.send_error(404, f"User with ID {resource_id} not found")
            
            elif path_parts[0] == "posts":
                # PUT /posts/{id} - полное обновление поста
                post_index = next((i for i, p in enumerate(self.test_data["posts"]) if p["id"] == resource_id), None)
                if post_index is not None:
                    updated_post = {
                        "id": resource_id,
                        "title": data.get("title", "Untitled"),
                        "body": data.get("body", ""),
                        "userId": data.get("userId", 1)
                    }
                    self.test_data["posts"][post_index] = updated_post
                    self._send_json_response(updated_post)
                    logger.info(f"Updated post: {updated_post}")
                else:
                    self.send_error(404, f"Post with ID {resource_id} not found")
            
            else:
                self.send_error(404, "Endpoint not found")
        else:
            self.send_error(400, "Invalid path for PUT request")
    
    def do_PATCH(self):
        """Обработка PATCH запросов"""
        logger.info(f"PATCH request to {self.path}")
        
        # Валидация заголовков
        if not self._validate_headers(["Content-Type"]):
            return
        
        data = self._parse_json_body()
        if data is None:
            return
        
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        if len(path_parts) == 2 and path_parts[1].isdigit():
            resource_id = int(path_parts[1])
            
            if path_parts[0] == "users":
                # PATCH /users/{id} - частичное обновление пользователя
                user_index = next((i for i, u in enumerate(self.test_data["users"]) if u["id"] == resource_id), None)
                if user_index is not None:
                    # Обновляем только переданные поля
                    for key, value in data.items():
                        if key in self.test_data["users"][user_index]:
                            self.test_data["users"][user_index][key] = value
                    
                    self._send_json_response(self.test_data["users"][user_index])
                    logger.info(f"Patched user: {self.test_data['users'][user_index]}")
                else:
                    self.send_error(404, f"User with ID {resource_id} not found")
            
            elif path_parts[0] == "posts":
                # PATCH /posts/{id} - частичное обновление поста
                post_index = next((i for i, p in enumerate(self.test_data["posts"]) if p["id"] == resource_id), None)
                if post_index is not None:
                    # Обновляем только переданные поля
                    for key, value in data.items():
                        if key in self.test_data["posts"][post_index]:
                            self.test_data["posts"][post_index][key] = value
                    
                    self._send_json_response(self.test_data["posts"][post_index])
                    logger.info(f"Patched post: {self.test_data['posts'][post_index]}")
                else:
                    self.send_error(404, f"Post with ID {resource_id} not found")
            
            else:
                self.send_error(404, "Endpoint not found")
        else:
            self.send_error(400, "Invalid path for PATCH request")
    
    def do_DELETE(self):
        """Обработка DELETE запросов"""
        logger.info(f"DELETE request to {self.path}")
        
        # Валидация заголовков (DELETE не требует Content-Type)
        if not self._validate_headers([]):
            return
        
        parsed_path = urlparse(self.path)
        path_parts = parsed_path.path.strip('/').split('/')
        
        if len(path_parts) == 2 and path_parts[1].isdigit():
            resource_id = int(path_parts[1])
            
            if path_parts[0] == "users":
                # DELETE /users/{id} - удалить пользователя
                user_index = next((i for i, u in enumerate(self.test_data["users"]) if u["id"] == resource_id), None)
                if user_index is not None:
                    deleted_user = self.test_data["users"].pop(user_index)
                    # Возвращаем подробный JSON ответ для DELETE
                    response_data = {
                        "success": True,
                        "message": f"User {resource_id} successfully deleted",
                        "deleted_user": deleted_user,
                        "remaining_users_count": len(self.test_data["users"]),
                        "timestamp": time.time()
                    }
                    self._send_json_response(response_data)
                    logger.info(f"Deleted user: {deleted_user}")
                else:
                    self.send_error(404, f"User with ID {resource_id} not found")
            
            elif path_parts[0] == "posts":
                # DELETE /posts/{id} - удалить пост
                post_index = next((i for i, p in enumerate(self.test_data["posts"]) if p["id"] == resource_id), None)
                if post_index is not None:
                    deleted_post = self.test_data["posts"].pop(post_index)
                    # Возвращаем подробный JSON ответ для DELETE
                    response_data = {
                        "success": True,
                        "message": f"Post {resource_id} successfully deleted",
                        "deleted_post": deleted_post,
                        "remaining_posts_count": len(self.test_data["posts"]),
                        "timestamp": time.time()
                    }
                    self._send_json_response(response_data)
                    logger.info(f"Deleted post: {deleted_post}")
                else:
                    self.send_error(404, f"Post with ID {resource_id} not found")
            
            else:
                self.send_error(404, "Endpoint not found")
        else:
            self.send_error(400, "Invalid path for DELETE request")
    
    def do_OPTIONS(self):
        """Обработка OPTIONS запросов для CORS"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()


class FakeHTTPServer:
    """Класс для управления fake HTTP сервером"""
    
    def __init__(self, host="localhost", port=8888):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        # Для доступа из приложения всегда используем localhost
        self.base_url = f"http://localhost:{port}"
    
    def start(self):
        """Запуск сервера в отдельном потоке"""
        try:
            # Проверяем, не запущен ли уже сервер
            if self.is_running():
                logger.warning("Server is already running")
                return True
            
            self.server = HTTPServer((self.host, self.port), FakeHTTPRequestHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            
            # Ждем немного, чтобы сервер успел запуститься
            time.sleep(1)
            
            # Проверяем, что сервер действительно запустился
            if self.is_running():
                logger.info(f"Fake HTTP Server started on {self.base_url}")
                return True
            else:
                logger.error("Server thread failed to start")
                return False
                
        except OSError as e:
            if e.errno == 10048:  # Port already in use on Windows
                logger.error(f"Port {self.port} is already in use")
            elif e.errno == 98:  # Port already in use on Linux
                logger.error(f"Port {self.port} is already in use")
            else:
                logger.error(f"OS Error starting server: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop(self):
        """Остановка сервера"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=2)
            logger.info("Fake HTTP Server stopped")
    
    def is_running(self):
        """Проверка, запущен ли сервер"""
        return self.server is not None and self.server_thread is not None and self.server_thread.is_alive()


def create_fake_server(host="localhost", port=8888):
    """Фабричная функция для создания fake сервера"""
    import os
    # Если запускаем в Docker, используем 0.0.0.0 для доступности извне
    if os.getenv("DOCKER_ENV") or host == "0.0.0.0":
        host = "0.0.0.0"
    return FakeHTTPServer(host, port)


if __name__ == "__main__":
    # Тестирование сервера
    server = create_fake_server()
    
    try:
        if server.start():
            print(f"Server running on {server.base_url}")
            print("Available endpoints:")
            print("  GET    /users - Get all users")
            print("  GET    /users/{id} - Get user by ID")
            print("  POST   /users - Create new user")
            print("  PUT    /users/{id} - Update user (full)")
            print("  PATCH  /users/{id} - Update user (partial)")
            print("  DELETE /users/{id} - Delete user")
            print("  GET    /posts - Get all posts")
            print("  GET    /posts/{id} - Get post by ID")
            print("  POST   /posts - Create new post")
            print("  PUT    /posts/{id} - Update post (full)")
            print("  PATCH  /posts/{id} - Update post (partial)")
            print("  DELETE /posts/{id} - Delete post")
            print("\nPress Ctrl+C to stop the server")
            
            # Держим сервер запущенным
            while True:
                time.sleep(1)
        else:
            print("Failed to start server")
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop()
        print("Server stopped")
