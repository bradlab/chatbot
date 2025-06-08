import os
from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.config import Settings

@pytest.fixture(scope="module", autouse=True)
def mock_env_vars():
    """
    Mocke les variables d'environnement requises par l'application.
    """
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.TELEGRAM_BOT_TOKEN = "mock_telegram_token_for_tests"
    mock_settings_instance.MISTRAL_API_KEY = "mock_mistral_api_key_for_tests"
    mock_settings_instance.WEBHOOK_URL = "http://mock.webhook.url/webhook_for_tests"
    mock_settings_instance.TELEGRAM_API_URL = "https://api.telegram.org"

    with patch('src.config.get_settings', return_value=mock_settings_instance):
        yield

@pytest.fixture(scope="module", autouse=True)
def mock_telegram_handler_singleton():
    """
    Mocke le singleton telegram_handler pour éviter l'exécution réelle.
    """
    mock_handler = MagicMock()
    # Mock les méthodes async attendues sur le singleton
    mock_handler.setup_ptb_handlers = AsyncMock(return_value=None)
    mock_handler.configure_telegram_webhook = AsyncMock(return_value=None)
    mock_handler.process_telegram_update = AsyncMock(return_value=None)
    mock_handler.shutdown_ptb = AsyncMock(return_value=None)

    # Patch le singleton dans le module src.telegram_handler
    with patch('src.telegram_handler.telegram_handler', mock_handler):
        yield

@pytest.fixture(scope="module")
def client():
    from src.main import app
    with TestClient(app) as c:
        yield c

def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World. Welcome to KOZ API"}

def test_read_prompt(client):
    response = client.get("/prompt")
    assert response.status_code == 404
    assert response.json() != {"msg": "Hello", "response": ""}

def test_noread_prompt(client):
    response = client.get("/prompt")
    assert response.status_code == 404
    assert response.json() != {"msg": "Hola", "response": ""}

def test_webhook_post(client):
    # Simule un update Telegram minimal
    update_json = {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {"id": 123, "is_bot": False, "first_name": "Test"},
            "chat": {"id": 123, "type": "private"},
            "date": 1680000000,
            "text": "Bonjour"
        }
    }
    response = client.post("/webhook", json=update_json)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
