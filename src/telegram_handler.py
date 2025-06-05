from telegram import Update, Bot, ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ContextTypes
from mistralai import Mistral

from .dynamodb_repository import dynamodb_repo
from .config import env_vars
from .utils import Utils

class TelegramHandler:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TelegramHandler, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.api_key = env_vars.MISTRAL_API_KEY
        self.TELEGRAM_BOT_TOKEN = env_vars.TELEGRAM_BOT_TOKEN
        self.MISTRAL_API_KEY = env_vars.MISTRAL_API_KEY
        self.MISTRAL_MODEL = "mistral-large-latest"

        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN n'est pas défini.")
        if not self.MISTRAL_API_KEY:
            raise ValueError("MISTRAL_API_KEY n'est pas défini.")

        self.mistral_client = Mistral(api_key=self.MISTRAL_API_KEY)
        self.ptb_app = Application.builder().token(self.TELEGRAM_BOT_TOKEN).updater(None).build()
        self._initialized = True
        self.setup_ptb_handlers()
        

    async def start_command(self, update: Update, context):
        try:
            user = update.message.from_user
            chat_id = update.message.chat_id
            user_name = user.full_name or user.username or "N/A"
            Utils.log_warning(f"===== Start command Initializing ====== {self.TELEGRAM_BOT_TOKEN}")

            reply_markup = ReplyKeyboardMarkup(
                [["/start", "/help", "/clear"]],
                resize_keyboard=True
            )

            response_text = (
                f"Bonjour {user_name} !\n"
                "Bienvenue sur le bot KOZ.\n"
                "Utilisez le menu ci-dessous pour commencer :"
            )
            await self.ptb_app.bot.send_message(chat_id=chat_id, text=response_text, reply_markup=reply_markup)
        except Exception as e:
            Utils.log_error(f"Start command error ==== {e}")

    async def handle_message(self, update: Update, context):
        try:
            if update.message and update.message.text:
                user = update.message.from_user
                user_message = update.message.text
                chat_id = update.message.chat_id
                message_id = update.message.message_id
                user_name = user.full_name or user.username or "N/A"

                Utils.log_warning(f"KOZ_MSG ======= {user_name} - {user_message}")
                await dynamodb_repo.save_message(chat_id, message_id, user.id, user_name, user_message, "user")
                Utils.log_warning(f"CONTINUE PROCESS ======= {user_name}")

                try:
                    Utils.log_warning(f"GET MISTRAL RESPONSE ======")
                    chat_response = self.mistral_client.chat.complete(
                        model=self.MISTRAL_MODEL,
                        messages=[
                            {
                                "role": "user",
                                "content": user_message,
                            },
                        ]
                    )
                    Utils.log_warning(f"AFTER MISTRAL ====== {chat_response}")

                    if chat_response:
                        response_text = chat_response.choices[0].message.content

                        bot_message = await self.ptb_app.bot.send_message(chat_id=chat_id, text=response_text)

                        await dynamodb_repo.save_message(
                            chat_id,
                            bot_message.message_id,
                            self.ptb_app.bot.id,
                            self.ptb_app.bot.username,
                            response_text,
                            "bot",
                            self.MISTRAL_MODEL
                        )
                        Utils.log_warning(f"ANSWER SAVED =======")
                except Exception as e:
                    error_response = "Désolé, une erreur est survenue lors du traitement de votre demande."
                    Utils.log_error(f"{error_response}: {e}")
                    await self.ptb_app.bot.send_message(chat_id=chat_id, text=error_response)
        except Exception as e:
            Utils.log_error("Traitement du message échoué.")

    async def help_command(self, update: Update, context):
        try:
            chat_id = update.message.chat_id
            response_text = (
                "Voici les commandes disponibles :\n"
                "/start - Afficher le menu principal\n"
                "/help - Afficher l'aide\n"
                "/clear - Effacer la conversation"
            )
            await self.ptb_app.bot.send_message(chat_id=chat_id, text=response_text)
        except Exception as e:
            Utils.log_error(f"Help command error ==== {e}")

    async def clear_command(self, update: Update, context):
        try:
            chat_id = update.message.chat_id
            response_text = "La conversation a été effacée"
            await self.ptb_app.bot.send_message(chat_id=chat_id, text=response_text)
        except Exception as e:
            Utils.log_error(f"Clear command error ==== {e}")

    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        Utils.log_error(f"== Unhandled Telegram exception: {context.error}")

    async def setup_ptb_handlers(self):
        try:
            self.ptb_app.add_handler(CommandHandler("start", self.start_command))
            self.ptb_app.add_handler(CommandHandler("help", self.help_command))
            self.ptb_app.add_handler(CommandHandler("clear", self.clear_command))
            Utils.log_warning("Handle first message ====")
            self.ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
            self.ptb_app.add_error_handler(self._error_handler)
            await self.ptb_app.initialize()
            Utils.log_warning("Handlers Telegram initialisés.")
        except Exception as e:
            Utils.log_error(f"Erreur lors de la configuration des handlers Telegram : {e}")

    async def configure_telegram_webhook(self, webhook_url: str):
        api_webhook_url = f"{env_vars.TELEGRAM_API_URL}{self.TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
        if not api_webhook_url:
            Utils.log_error("WEBHOOK_URL non défini. Le webhook ne sera pas configuré automatiquement.")
            return

        bot = Bot(self.TELEGRAM_BOT_TOKEN)
        try:
            current_webhook = await bot.get_webhook_info()
            Utils.log_warning(f"=== TELEGRAM to connect : \n NEW : {webhook_url} \n OLD: {current_webhook.url}")
            if current_webhook.url != api_webhook_url:
                try:
                    await bot.set_webhook(url=api_webhook_url)
                    Utils.log_warning(f"Webhook Telegram configuré sur : {webhook_url}")
                except Exception as bot_error:
                    Utils.log_error(f"Erreur configuration du webhook url : {bot_error}")
            else:
                Utils.log_warning("Webhook déjà configuré, aucune modification nécessaire.")
        except Exception as e:
            Utils.log_error(f"Erreur lors de la configuration du webhook Telegram : {webhook_url} {e}")

    async def process_telegram_update(self, update_json: dict):
        update = Update.de_json(update_json, self.ptb_app.bot)
        await self.ptb_app.process_update(update)

    async def shutdown_ptb(self):
        await self.ptb_app.shutdown()
        Utils.log_warning("Application Telegram arrêtée.")

# Singleton instance
telegram_handler = TelegramHandler()
