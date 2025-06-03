from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
from mistralai import Mistral
import asyncio

from .dynamodb_repository import dynamodb_repo
from .config import env_vars
from .utils import Utils

api_key = env_vars.MISTRAL_API_KEY
# Récupérer les jetons depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = env_vars.TELEGRAM_BOT_TOKEN
MISTRAL_API_KEY = env_vars.MISTRAL_API_KEY
# API_WEBHOOK_URL = f"{env_vars.TELEGRAM_API_URL}{TELEGRAM_BOT_TOKEN}/setWebhook?url={env_vars.WEBHOOK_URL}" 
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
    try:
        # Gère la commande /start.
        user = update.message.from_user
        user_message = update.message.text
        chat_id = update.message.chat_id
        message_id = update.message.message_id
        user_name = user.full_name or user.username or "N/A"
        Utils.log_warning(f"===== Start command Initializing ====== {TELEGRAM_BOT_TOKEN}")
        
        # try:
        #     await dynamodb_repo.save_message(chat_id, message_id, user.id, user_name, "user", user_message)
        # except Exception as db_error:
        #     Utils.log_error(f"DB_ERROR.start_command 1 ====== {e}")
        response_text = (
            f"Hello {user_name}! How can I assist you today? Let's have a friendly conversation. Here are a few suggestions for how we can proceed:\n\n"
            "• You can ask me a question about a topic you're interested in.\n"
            "• We can play a word game, like word association or 20 questions.\n"
            "• You can share something about yourself, and I'll do my best to relate.\n"
            "• We can discuss a recent event or trending topic.\n\n"
            "How would you like to begin?"
        )
        # await update.message.reply_text()
        bot_message = await ptb_app.bot.send_message(chat_id=chat_id, text=response_text)
        # try:
        #     await dynamodb_repo.save_message(chat_id, bot_message.message_id, ptb_app.bot.id, ptb_app.bot.username, response_text, "bot")
        # except Exception as db_error:
        #     Utils.log_error(f"DB_ERROR.start_command 2 ====== {e}")
    except Exception as e:
        Utils.log_error(f"Start command error ==== {e}")
    

async def handle_message(update: Update, context):
    try:
        if update.message and update.message.text:
            user = update.message.from_user
            user_message = update.message.text
            chat_id = update.message.chat_id
            message_id = update.message.message_id
            user_name = user.full_name or user.username or "N/A"
            
            # try:
            Utils.log_warning(f"KOZ_MSG ======= {user_name} - {user_message}")
            await dynamodb_repo.save_message(chat_id, message_id, user.id, user_name, user_message, "user")
            # except Exception as db_error:
            #     Utils.log_error(f"DB_ERROR.handle_message ====== {db_error}")
            Utils.log_warning(f"CONTINUE PROCESS ======= {user_name}")
            
            try:
                Utils.log_warning(f"GET MISTRAL RESPONSE ======")
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
                Utils.log_warning(f"MESSAGE ANSWER ======= {response_text}")
                
                bot_message  = await ptb_app.bot.send_message(chat_id=chat_id, text=response_text)
                Utils.log_warning(f"ANSWER SENT ======= {bot_message.message_id}")
                
                try:
                    if bot_message :
                        Utils.log_warning(f"SAVING ANSWER ======= {bot_message.message_id}")
                        # Enregistrement dans DynamoDB
                        await dynamodb_repo.save_message(
                            chat_id, 
                            bot_message.message_id, 
                            ptb_app.bot.id, 
                            ptb_app.bot.username, 
                            response_text,
                            "bot", 
                            MISTRAL_MODEL
                        )
                        Utils.log_warning(f"ANSWER SAVED =======")
                except Exception as db_error:
                    Utils.log_info(f"Erreur lors de l'enregistrement dans DynamoDB: {db_error}")
            except Exception as e:
                error_response = "Sorry, an error occurred while processing your message."
                bot_message = await ptb_app.bot.send_message(chat_id=chat_id, text=error_response)
                # try:
                #     await dynamodb_repo.save_message(chat_id, bot_message.message_id, ptb_app.bot.id, ptb_app.bot.username, error_response, "bot")
                # except Exception as db_error:
                    # Utils.log_error(f"Erreur lors de l'enregistrement dans DynamoDB: {db_error}")
    except Exception as e:
        Utils.log_error("Traitement du message échoué.")

async def _error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    Utils.log_error(f"== Unhandled Telegram exception: {context.error}")

        
async def setup_ptb_handlers():
    try:
        # Configure les handlers de l'application Python-Telegram-Bot
        ptb_app.add_handler(CommandHandler("start", start_command))
        Utils.log_warning("Handle first message ====")
        ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        ptb_app.add_error_handler(_error_handler)
        await ptb_app.initialize()
        Utils.log_warning("Handlers Telegram initialisés.")
    except Exception as e:
        Utils.log_error(f"Erreur lors de la configuration des handlers Telegram : {e}")

async def configure_telegram_webhook(webhook_url: str):
    api_webhook_url = f"{env_vars.TELEGRAM_API_URL}{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}" 
    if not api_webhook_url:
        Utils.log_error("WEBHOOK_URL non défini. Le webhook ne sera pas configuré automatiquement.")
        return

    bot = Bot(TELEGRAM_BOT_TOKEN)
    try:
        current_webhook = await bot.get_webhook_info()
        Utils.log_warning(f"=== TELEGRAM to connect : \n NEW : {webhook_url} \n OLD: {current_webhook.url}")
        if current_webhook.url != api_webhook_url:
            try:
                await bot.set_webhook(url=api_webhook_url)
                Utils.log_warning(f"Webhook Telegram configuré sur : {webhook_url}")
            except Exception as bot_error:
                Utils.log_error(f"Erreur configuration du webhook url : {e}")
        else:
            Utils.log_warning("Webhook déjà configuré, aucune modification nécessaire.")
    except Exception as e:
        Utils.log_error(f"Erreur lors de la configuration du webhook Telegram : {webhook_url} {e}")

async def process_telegram_update(update_json: dict):
    update = Update.de_json(update_json, ptb_app.bot)
    await ptb_app.process_update(update)

async def shutdown_ptb():
    # Arrête l'application Python-Telegram-Bot.
    await ptb_app.shutdown()
    Utils.log_warning("Application Telegram arrêtée.")