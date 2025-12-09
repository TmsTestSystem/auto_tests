import os
import re
import time
import uuid
import requests
import urllib3
from pathlib import Path
from urllib.parse import urlparse, urlunparse
from dotenv import load_dotenv
import pytest

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from conftest import get_auth_cookies, get_api_base_url


class MailHogClient:
    
    def __init__(self, mailhog_url: str = None):
        self.base_url = mailhog_url or os.getenv("MAILHOG_URL", "http://localhost:8025")
        self.api_url = f"{self.base_url}/api/v2"
    
    def get_messages(self, limit: int = 50) -> list:
        try:
            resp = requests.get(f"{self.api_url}/messages", params={"limit": limit}, timeout=10, verify=False)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError as e:
            pytest.fail(f"MailHog недоступен по адресу {self.base_url}. Проверьте, что MailHog запущен. Ошибка: {e}")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Ошибка при обращении к MailHog {self.base_url}: {e}")
    
    def get_message_by_id(self, message_id: str) -> dict:
        resp = requests.get(f"{self.api_url}/messages/{message_id}", timeout=10, verify=False)
        resp.raise_for_status()
        return resp.json()
    
    def search_messages(self, query: str, kind: str = "to") -> list:
        messages = self.get_messages()
        results = []
        for msg in messages.get("items", []):
            content = msg.get("Content", {})
            headers = content.get("Headers", {})
            
            if kind == "to":
                recipients = headers.get("To", [])
            else:
                recipients = headers.get("From", [])
            
            for recipient in recipients:
                if query.lower() in recipient.lower():
                    results.append(msg)
                    break
        
        return results
    
    def wait_for_message(self, recipient: str, timeout: int = 10, check_interval: float = 0.5) -> dict:
        start_time = time.time()
        while time.time() - start_time < timeout:
            messages = self.search_messages(recipient, kind="to")
            if messages:
                return messages[0]
            time.sleep(check_interval)
        
        raise TimeoutError(f"Письмо для {recipient} не появилось за {timeout} секунд")
    
    def clear_messages(self):
        try:
            resp = requests.delete(f"{self.api_url}/messages", timeout=10, verify=False)
            resp.raise_for_status()
        except requests.exceptions.RequestException:
            pass


@pytest.fixture(scope="function")
def mailhog(request):
    test_host = request.config.getoption("--test-host", default=None)
    if test_host and test_host.startswith("st"):
        pytest.skip(f"Тесты с MailHog доступны только на локальных стендах (local-192, local-a, local-b, local-c), текущий хост: {test_host}")
    
    if "MAILHOG_URL" in os.environ:
        del os.environ["MAILHOG_URL"]
    load_dotenv(dotenv_path=env_path, override=True)
    
    mailhog_url = None
    print(f"[DEBUG] Читаем .env файл: {env_path}")
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            print(f"[DEBUG] Всего строк в .env: {len(lines)}")
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if 'MAILHOG_URL' in line:
                    parts = line.split('=', 1)
                    if len(parts) == 2 and parts[0].strip() == 'MAILHOG_URL':
                        mailhog_url = parts[1].strip()
                        print(f"[DEBUG] Прочитано из .env файла (строка {line_num}): {mailhog_url}")
                        break
    except Exception as e:
        print(f"[WARN] Не удалось прочитать MAILHOG_URL из .env: {e}")
    
    if not mailhog_url:
        mailhog_url = os.getenv("MAILHOG_URL")
        if mailhog_url:
            print(f"[DEBUG] Прочитано из переменной окружения os.getenv: {mailhog_url}")
        else:
            print(f"[DEBUG] os.getenv('MAILHOG_URL') вернул None")
    
    mailhog_url = mailhog_url or "http://localhost:8025"
    print(f"[INFO] Используется MailHog URL: {mailhog_url}")
    
    client = MailHogClient(mailhog_url)
    
    try:
        test_resp = requests.get(f"{client.api_url}/messages", params={"limit": 1}, timeout=5, verify=False)
        test_resp.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        pytest.skip(f"MailHog недоступен по адресу {mailhog_url}. Установите MAILHOG_URL=http://192.168.0.7:8025 в .env или запустите MailHog. Ошибка: {e}")
    except requests.exceptions.RequestException as e:
        pytest.skip(f"Ошибка при обращении к MailHog {mailhog_url}: {e}")
    
    client.clear_messages()
    yield client


@pytest.fixture(scope="function")
def api_client():
    base_url = get_api_base_url()
    cookies = get_auth_cookies()
    return {
        "base_url": base_url,
        "cookies": cookies
    }


def test_mailhog_accessible(mailhog):
    messages = mailhog.get_messages()
    assert isinstance(messages, dict), "MailHog вернул неверный формат ответа"
    assert "items" in messages, "В ответе MailHog нет поля 'items'"


def test_user_creation_sends_email(api_client, mailhog):
    import uuid
    
    base_url = api_client["base_url"]
    cookies = api_client["cookies"]
    
    unique_id = str(uuid.uuid4())[:8]
    timestamp = int(time.time())
    test_email = f"test_{timestamp}_{unique_id}@mail.com"
    
    messages_before = mailhog.get_messages()
    count_before = len(messages_before.get("items", []))
    
    phone_suffix = f"{timestamp % 1000000000:09d}"[:9]
    user_data = {
        "last_name": f"test_{timestamp}_{unique_id}",
        "first_name": f"test_{timestamp}_{unique_id}",
        "middle_name": f"test_{timestamp}_{unique_id}",
        "email": test_email,
        "phone": f"9{phone_suffix}",
        "position": f"QA_test_{timestamp}_{unique_id}"
    }
    
    resp = requests.post(
        f"{base_url}/api/role_system/users",
        json=user_data,
        cookies=cookies,
        verify=False,
        timeout=30
    )
    
    assert resp.status_code in [200, 201], \
        f"Ошибка создания пользователя: {resp.status_code}, {resp.text}"
    
    user_response = resp.json()
    user_id = user_response.get("id")
    assert user_id is not None, f"В ответе создания пользователя нет поля 'id'. Ответ: {user_response}"
    
    print(f"[INFO] Пользователь создан с ID: {user_id}")
    
    time.sleep(1)
    
    invite_data = {
        "user_id": user_id
    }
    
    invite_resp = requests.post(
        f"{base_url}/api/invitations",
        json=invite_data,
        cookies=cookies,
        verify=False,
        timeout=30
    )
    
    assert invite_resp.status_code in [200, 201], \
        f"Ошибка отправки инвайта: {invite_resp.status_code}, {invite_resp.text}"
    
    print(f"[INFO] Инвайт отправлен для пользователя {user_id} ({test_email})")
    
    time.sleep(2)
    
    try:
        message = mailhog.wait_for_message(test_email, timeout=15)
        assert message is not None, "Письмо не найдено в MailHog"
        
        print(f"[SUCCESS] Письмо для {test_email} найдено в MailHog")
        
        content = message.get("Content", {})
        headers = content.get("Headers", {})
        
        recipients = headers.get("To", [])
        assert any(test_email.lower() in r.lower() for r in recipients), \
            f"Получатель {test_email} не найден в письме. Получатели: {recipients}"
        
        sender = headers.get("From", [""])[0]
        assert sender, f"Отправитель не найден в письме"
        print(f"[INFO] Отправитель: {sender}")
        
        subject = headers.get("Subject", [""])[0]
        assert subject, f"Тема письма пуста"
        print(f"[INFO] Тема письма: {subject}")
        
        body = content.get("Body", "")
        assert body, f"Тело письма пусто"
        print(f"[INFO] Тело письма (первые 200 символов): {body[:200]}")
        
        assert test_email.lower() in body.lower() or user_data["first_name"] in body or user_data["last_name"] in body, \
            f"В теле письма не найдена информация о пользователе. Тело: {body[:200]}"
        
        url_pattern = r'https?://[^\s<>"\'\)]+'
        urls = re.findall(url_pattern, body)
        
        assert len(urls) > 0, f"В письме не найдено ссылок. Тело: {body[:500]}"
        
        original_link = urls[0].rstrip('.,;:!?)')
        print(f"[INFO] Найдена ссылка инвайта в письме: {original_link}")
        print(f"[INFO] Все найденные ссылки в письме: {urls}")
        
        parsed_original = urlparse(original_link)
        invite_token_pattern = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
        invite_token_match = re.search(invite_token_pattern, parsed_original.path, re.IGNORECASE)
        assert invite_token_match is not None, f"Токен инвайта не найден в ссылке: {parsed_original.path}"
        invite_token = invite_token_match.group(0)
        print(f"[INFO] Извлечен токен инвайта: {invite_token}")
        
        frontend_base_url = get_api_base_url()
        print(f"[INFO] BASE_URL динамически установлен: {frontend_base_url} (зависит от --test-host)")
        parsed_new = parsed_original._replace(scheme=urlparse(frontend_base_url).scheme,
                                             netloc=urlparse(frontend_base_url).netloc)
        invite_link = urlunparse(parsed_new)
        
        print(f"[INFO] Ссылка после замены хоста: {invite_link}")
        
        try:
            link_resp = requests.get(invite_link, verify=False, timeout=10, allow_redirects=True)
            print(f"[INFO] Ответ от ссылки {invite_link}: статус {link_resp.status_code}, размер ответа: {len(link_resp.content)} байт")
            assert link_resp.status_code in [200, 201, 302, 301], \
                f"Ссылка {invite_link} недоступна. Статус: {link_resp.status_code}, ответ: {link_resp.text[:200]}"
            print(f"[SUCCESS] Ссылка {invite_link} доступна (статус: {link_resp.status_code})")
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Ошибка при проверке доступности ссылки {invite_link}: {e}")
        
        test_password = "пароль"
        accept_data = {
            "new_password": test_password,
            "password_confirmation": test_password,
            "last_name": user_data["last_name"],
            "first_name": user_data["first_name"],
            "middle_name": user_data["middle_name"],
            "email": user_data["email"],
            "phone": user_data["phone"],
            "position": user_data["position"]
        }
        
        accept_url = f"{base_url}/api/invitations/{invite_token}/accept"
        print(f"[INFO] Принимаем инвайт: POST {accept_url}")
        accept_resp = requests.post(
            accept_url,
            json=accept_data,
            verify=False,
            timeout=30
        )
        
        assert accept_resp.status_code in [200, 201], \
            f"Ошибка принятия инвайта: {accept_resp.status_code}, ответ: {accept_resp.text}"
        print(f"[SUCCESS] Инвайт принят успешно (статус: {accept_resp.status_code})")
        
        time.sleep(1)
        
        sign_in_data = {
            "email": test_email,
            "password": test_password
        }
        
        sign_in_url = f"{base_url}/api/auth/sign_in"
        print(f"[INFO] Проверяем авторизацию: POST {sign_in_url}")
        print(f"[INFO] Данные авторизации: email={test_email}, password={test_password}")
        sign_in_resp = requests.post(
            sign_in_url,
            json=sign_in_data,
            verify=False,
            timeout=30
        )
        
        assert sign_in_resp.status_code in [200, 201], \
            f"Ошибка авторизации: {sign_in_resp.status_code}, ответ: {sign_in_resp.text}"
        print(f"[SUCCESS] Авторизация прошла успешно (статус: {sign_in_resp.status_code})")
        
        sign_in_response = sign_in_resp.json()
        assert sign_in_response is not None, "Ответ авторизации пуст"
        assert isinstance(sign_in_response, dict), f"Ответ авторизации должен быть словарем, получен: {type(sign_in_response)}"
        
        assert len(sign_in_resp.cookies) > 0, "В ответе авторизации отсутствуют cookies"
        
        if "data" in sign_in_response:
            user_data_response = sign_in_response["data"]
            assert "email" in user_data_response, f"В ответе авторизации отсутствует email. Ответ: {sign_in_response}"
            assert user_data_response["email"] == test_email, \
                f"Email в ответе не совпадает. Ожидали: {test_email}, получили: {user_data_response.get('email')}"
        elif "email" in sign_in_response:
            assert sign_in_response["email"] == test_email, \
                f"Email в ответе не совпадает. Ожидали: {test_email}, получили: {sign_in_response.get('email')}"
        
        print(f"[INFO] Данные авторизации: {sign_in_response}")
        print(f"[SUCCESS] Авторизация успешна: пользователь {test_email} может войти в систему")
        
        messages_after = mailhog.get_messages()
        count_after = len(messages_after.get("items", []))
        assert count_after > count_before, \
            f"Количество писем не увеличилось. Было: {count_before}, стало: {count_after}"
        
    except TimeoutError:
        pytest.fail(f"Письмо для {test_email} не появилось в MailHog за отведенное время")
