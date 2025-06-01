from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, CommandHandler
from mistralai import Mistral

from .dynamodb_repository import dynamodb_repo
from .config import env_vars
from .utils import Utils

api_key = env_vars.MISTRAL_API_KEY
# Récupérer les jetons depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = env_vars.TELEGRAM_BOT_TOKEN
MISTRAL_API_KEY = env_vars.MISTRAL_API_KEY
API_WEBHOOK_URL = f"{env_vars.TELEGRAM_API_URL}{TELEGRAM_BOT_TOKEN}/setWebhook?url={env_vars.WEBHOOK_URL}" 
# API_WEBHOOK_URL = env_vars.WEBHOOK_URL
MISTRAL_MODEL = "mistral-large-latest"

if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN n'est pas défini.")
if not MISTRAL_API_KEY:
    raise ValueError("MISTRAL_API_KEY n'est pas défini.")

# Initialisation du client MistralAI
mistral_client = Mistral(api_key=MISTRAL_API_KEY)

# Initialisation de l'application Python-Telegram-Bot
ptb_app = Application.builder().token(TELEGRAM_BOT_TOKEN).updater(None).build()

async def start_command(update: Update, context):
    # Gère la commande /start.
    user = update.message.from_user
    user_message = update.message.text
    chat_id = update.message.chat_id
    message_id = update.message.message_id
    user_name = user.full_name or user.username or "N/A"
    await dynamodb_repo.save_message(chat_id, message_id, user.id, user_name, "user", user_message)
    response_text = f"Bonjour {user_name} ! Je suis Koz votre bot intelligent de causerie. Posez-moi une question !"
    await update.message.reply_text()
    bot_message = await ptb_app.bot.send_message(chat_id=chat_id, text=response_text)
    await dynamodb_repo.save_message(chat_id, bot_message.message_id, ptb_app.bot.id, ptb_app.bot.username, response_text, "bot")
    

async def handle_message(update: Update, context):
    # Traite tous les messages texte et utilise MistralAI pour répondre.
    try:
        if update.message and update.message.text:
            user = update.message.from_user
            user_message = update.message.text
            chat_id = update.message.chat_id
            message_id = update.message.message_id
            user_name = user.full_name or user.username or "N/A"
            
            # Enregistrer le message utilisateur via le repository
            await dynamodb_repo.save_message(chat_id, message_id, user.id, user_name, user_message, "user")

            try:
                chat_response = mistral_client.chat.complete(
                    model=MISTRAL_MODEL,
                    messages=[
                        {
                            "role": "user",
                            "content": user_message,
                        },
                    ]
                )
                
                response_text = chat_response.choices[0].message.content
                bot_message  = await ptb_app.bot.send_message(chat_id=chat_id, text=response_text)
                # Enregistrer la reponse du bot
                await dynamodb_repo.save_message(
                    chat_id, 
                    bot_message.message_id, 
                    ptb_app.bot.id, 
                    ptb_app.bot.username, 
                    response_text,
                    "bot", 
                    MISTRAL_MODEL
                )
            except Exception as e:
                Utils.log_info(f"Erreur lors de l'interaction avec MistralAI ou Telegram: {e}")
                error_response = "Désolé, une erreur est survenue lors du traitement de votre demande."
                # Enregistrer le message d'erreur du bot via le dépôt
                bot_message = await ptb_app.bot.send_message(chat_id=chat_id, text=error_response)
                await dynamodb_repo.save_message(chat_id, bot_message.message_id, ptb_app.bot.id, ptb_app.bot.username, error_response, "bot")
    except Exception as e:
        Utils.log_error("Traitement du message échoué.")

async def setup_ptb_handlers():
    try:
        # Configure les handlers de l'application Python-Telegram-Bot
        ptb_app.add_handler(CommandHandler("start", start_command))
        ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        await ptb_app.initialize()
        Utils.log_info("Handlers Telegram initialisés.")
    except Exception as e:
        Utils.log_error(f"Erreur lors de la configuration des handlers Telegram : {e}")

async def configure_telegram_webhook():
    # Configure le webhook Telegram avec l'URL définie.
    if not API_WEBHOOK_URL:
        Utils.log_error("WEBHOOK_URL non défini. Le webhook ne sera pas configuré automatiquement.")
        return

    bot = Bot(TELEGRAM_BOT_TOKEN)
    try:
        await bot.set_webhook(url=API_WEBHOOK_URL)
        Utils.log_info(f"Webhook Telegram configuré sur : {env_vars.WEBHOOK_URL}")
        Utils.log_info(f"Webhook Telegram API : {API_WEBHOOK_URL}")
    except Exception as e:
        Utils.log_error(f"Erreur lors de la configuration du webhook Telegram : {e}")

async def process_telegram_update(update_json: dict):
    update = Update.de_json(update_json, ptb_app.bot)
    await ptb_app.process_update(update)

async def shutdown_ptb():
    # Arrête l'application Python-Telegram-Bot.
    await ptb_app.shutdown()
    Utils.log_warning("Application Telegram arrêtée.")