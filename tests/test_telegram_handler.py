pytest_plugins = ("pytest_asyncio",)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_start_command_sends_menu():
    mock_update = MagicMock()
    mock_context = MagicMock()
    mock_update.message.from_user.full_name = "Test User"
    mock_update.message.from_user.username = "testuser"
    mock_update.message.chat_id = 123
    mock_update.message.text = "/start"

    with patch("src.telegram_handler.telegram_handler.ptb_app.bot.send_message", new_callable=AsyncMock) as send_message_mock:
        from src.telegram_handler import telegram_handler
        await telegram_handler.start_command(mock_update, mock_context)
        send_message_mock.assert_awaited_once()
        args, kwargs = send_message_mock.await_args
        assert kwargs["chat_id"] == 123
        assert "Bienvenue sur le bot KOZ" in kwargs["text"]

@pytest.mark.asyncio
async def test_help_command():
    mock_update = MagicMock()
    mock_context = MagicMock()
    mock_update.message.chat_id = 456

    with patch("src.telegram_handler.telegram_handler.ptb_app.bot.send_message", new_callable=AsyncMock) as send_message_mock:
        from src.telegram_handler import telegram_handler
        await telegram_handler.help_command(mock_update, mock_context)
        send_message_mock.assert_awaited_once()
        args, kwargs = send_message_mock.await_args
        assert kwargs["chat_id"] == 456
        assert "Voici les commandes disponibles" in kwargs["text"]

@pytest.mark.asyncio
async def test_clear_command():
    mock_update = MagicMock()
    mock_context = MagicMock()
    mock_update.message.chat_id = 789

    with patch("src.telegram_handler.telegram_handler.ptb_app.bot.send_message", new_callable=AsyncMock) as send_message_mock:
        from src.telegram_handler import telegram_handler
        await telegram_handler.clear_command(mock_update, mock_context)
        send_message_mock.assert_awaited_once()
        args, kwargs = send_message_mock.await_args
        assert kwargs["chat_id"] == 789
        assert "La conversation a été effacée" in kwargs["text"]

@pytest.mark.asyncio
async def test_handle_message_called_on_webhook():
    update_json = {
        "update_id": 987654321,
        "message": {
            "message_id": 2,
            "from": {"id": 456, "is_bot": False, "first_name": "Tester"},
            "chat": {"id": 456, "type": "private"},
            "date": 1680000001,
            "text": "Test handle"
        }
    }
    with patch("src.telegram_handler.telegram_handler.process_telegram_update", new_callable=AsyncMock) as mock_process_update:
        from src.main import app
        from fastapi.testclient import TestClient
        with TestClient(app) as test_client:
            response = test_client.post("/webhook", json=update_json)
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}
            mock_process_update.assert_awaited_once_with(update_json)
