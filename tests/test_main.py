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

@pytest.fixture(scope="module", autouse=True)
def mock_telegram_handler_module():
    """
    Mocke complètement le module 'src.telegram_handler' pour éviter
    son exécution réelle lors de l'importation de 'main.py'.
    """
    # Crée un mock pour le module telegram_handler.
    # Nous pourrions ajouter des attributs ou méthodes mockés si main.py
    # appelait des choses spécifiques du handler directement (ex: handler.process_update)
    mock_handler = MagicMock()

    # Mocker les fonctions/objets que main.py importe depuis telegram_handler.py
    # Ces noms doivent correspondre exactement à ce qui est importé dans main.py
    mock_handler.setup_ptb_handlers = MagicMock(return_value=None) # async function, so it will be awaited
    mock_handler.configure_telegram_webhook = MagicMock(return_value=None) # async function
    mock_handler.process_telegram_update = MagicMock(return_value=None) # async function
    mock_handler.shutdown_ptb = MagicMock(return_value=None) # async function

    with patch.dict('sys.modules', {'src.telegram_handler': mock_handler}):
        yield # L'application va maintenant importer notre mock_handler


@pytest.fixture(scope="module")
def client():
    # C'est ici que src.main est importé, et donc src.telegram_handler
    # sera importé comme notre mock_handler.
    from src.main import app
    with TestClient(app) as c:
        yield c

# client = TestClient(app)


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
