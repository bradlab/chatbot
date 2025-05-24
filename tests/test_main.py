import os
from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch, MagicMock

from src.main import app

from src.config import get_settings, Settings

@pytest.fixture(scope="module", autouse=True)
def mock_env_vars():
    """
    Mocke les variables d'environnement requises par l'application.
    Utilise scope="module" et autouse=True pour que le mocking s'applique
    à tous les tests de ce module et soit setup/teardown une seule fois.
    """
    # Crée une instance mockée de Settings
    mock_settings_instance = MagicMock(spec=Settings)
    mock_settings_instance.TELEGRAM_BOT_TOKEN = "mock_telegram_token_for_tests"
    mock_settings_instance.MISTRAL_API_KEY = "mock_mistral_api_key_for_tests"
    mock_settings_instance.WEBHOOK_URL = "http://mock.webhook.url/webhook_for_tests"
    mock_settings_instance.TELEGRAM_API_URL = "https://api.telegram.org" # Ajoutez toutes les vars nécessaires

    with patch('src.config.get_settings', return_value=mock_settings_instance):
        # Ici, en mockant get_settings, on contourne complètement la lecture du .env.
        yield

client = TestClient(app)


def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World. Welcome to KOZ API"}
    
def test_read_prompt():
    response = client.get("/prompt")
    assert response.status_code == 404
    assert response.json() != {"msg": "Hello", "response": ""}

def test_noread_prompt():
    response = client.get("/prompt")
    assert response.status_code == 404
    assert response.json() != {"msg": "Hola", "response": ""}


# calculator.py
class Calculator:
    def add(self, a, b):
        return a + b

    def divide(self, a, b):
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b



@pytest.fixture
def calculator():
    return Calculator()


def test_add_positive_numbers(calculator):
    result = calculator.add(2, 3)
    assert result == 5


def test_add_negative_numbers(calculator):
    result = calculator.add(-1, -4)
    assert result == -5


def test_add_zero(calculator):
    result = calculator.add(10, 0)
    assert result == 10


def test_divide_valid_numbers(calculator):
    result = calculator.divide(10, 2)
    assert result == 5.0


def test_divide_by_zero(calculator):
    with pytest.raises(ValueError, match="Division by zero is not allowed"):
        calculator.divide(10, 0)


def test_divide_negative_numbers(calculator):
    result = calculator.divide(-10, 2)
    assert result == -5.0
