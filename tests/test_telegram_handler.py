import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import os
import datetime

# Importez les fonctions que vous voulez tester
from src.telegram_handler import (
    ptb_app,
)

# Importez l'instance de dépôt DynamoDB
from src.dynamodb_repository import dynamodb_repo # IMPORTANT

# Importez la classe Settings et get_settings de votre module config
from src.config import Settings, get_settings


# --- Fixtures Pytest pour le Mocking ---

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

@pytest.fixture
def mock_update():
    update = AsyncMock()
    update.message.reply_text = AsyncMock()
    update.message.text = "Hello world"
    update.message.chat_id = 12345
    update.message.message_id = 54321
    update.message.from_user.id = 98765
    update.message.from_user.full_name = "Test User"
    update.message.from_user.username = "testuser"
    return update

@pytest.fixture
def mock_context():
    context = MagicMock()
    return context

@pytest.fixture(autouse=True)
def mock_telegram_bot_methods():
    with patch.object(ptb_app, 'bot', new_callable=AsyncMock) as mock_bot:
        mock_bot.send_message = AsyncMock()
        mock_bot.set_webhook = AsyncMock()
        mock_bot.id = 1234567
        mock_bot.full_name = "MyBotName"
        yield mock_bot

@pytest.fixture(autouse=True)
def mock_mistral_client():
    with patch('src.telegram_handler.Mistral', new_callable=MagicMock) as MockMistral:
        mock_instance = MockMistral.return_value
        mock_instance.chat = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a mocked AI response."
        mock_instance.chat.return_value = mock_response
        yield mock_instance

@pytest.fixture(autouse=True)
def mock_dynamodb_repository_save_message():
    """
    Mocke la méthode save_message du dépôt DynamoDB.
    """
    with patch.object(dynamodb_repo, 'save_message', new_callable=AsyncMock) as mock_save_message:
        yield mock_save_message
