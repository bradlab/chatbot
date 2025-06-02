from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from mangum import Mangum
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import datetime
from mistralai import Mistral
import asyncio

from .dynamodb_repository import dynamodb_repo


# Importe les fonctions de traitement Telegram
from .telegram_handler import (
    setup_ptb_handlers,
    configure_telegram_webhook,
    process_telegram_update,
    shutdown_ptb
)

from .config import env_vars


from .utils import Utils

api_key = env_vars.MISTRAL_API_KEY
model = "mistral-small-latest"
client = Mistral(api_key=api_key)


@asynccontextmanager
async def app_lifespan(application: FastAPI):
    Utils.log_info("Application KOZ API  démarrée.")
    await setup_ptb_handlers()
    asyncio.create_task(configure_telegram_webhook())

    yield # L'application est maintenant prête à recevoir des requêtes

    Utils.log_info("Application KOZ API arrêtée.")
    await shutdown_ptb()


app = FastAPI(
    title="ChatBot KOZ API",
    description="Chatbot API description",
    version="1.0.0",
    lifespan=app_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialise le rate limiter (par IP)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.middleware("http")
@limiter.limit("100/minute")
async def global_rate_limit(request: Request, call_next):
    return await call_next(request)


@app.get("/")
async def root():
    return {"msg": "Hello World. Welcome to KOZ API"}

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/chat")
async def chat(question: str):
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": question,
            },
        ]
    )
    Utils.log_info(chat_response)
    response = {
        "chat_id": {
            "S": f"{chat_response.id}",
        },
        "question": {
            "S": f"{question}",
        },
        "answer": {
            "S": f"{chat_response.choices[0].message.content}",
        }
    }
    Utils.insert_data(response)
    return response

@app.post("/webhook", description="Endpoint pour recevoir les mises à jour ou changement dans le bot Telegram")
async def telegram_webhook(request: Request):
    try:
        update_json = await request.json()
        await process_telegram_update(update_json)
        return {"status": "ok"}
    except Exception as e:
        Utils.log_error(f"Erreur de traitement du webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat-history/{chat_id}", description="Endpoint pour récupérer l'historique d'une discussion.")
async def get_chat_history_endpoint(chat_id: int, limit: int = 100):
    history = await dynamodb_repo.get_chat_history(chat_id, limit)
    if not history:
        raise HTTPException(status_code=404, detail="Historique de chat non trouvé ou erreur.")
    return {"chat_id": chat_id, "history": history}

@app.get("/user-messages/{user_id}", description="Récupère tous les messages d'un utilisateur spécifique dans une plage de dates.")
async def get_user_messages_endpoint(
    user_id: int,
    start_date: str = Query(..., description="Date de début (YYYY-MM-DD)"),
    end_date: str = Query(..., description="Date de fin (YYYY-MM-DD)"),
    limit: int = 100
):
    try:
        # Convertir les dates en timestamps ISO 8601 pour la requête DynamoDB
        start_timestamp = datetime.datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc).isoformat()
        end_timestamp = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=datetime.timezone.utc).isoformat()
    except ValueError:
        raise HTTPException(status_code=400, detail="Format de date invalide. Utilisez YYYY-MM-DD.")

    messages = await dynamodb_repo.get_user_messages_by_date_range(user_id, start_timestamp, end_timestamp, limit)
    if not messages:
        err_msg = f"Aucun message trouvé pour l'utilisateur {user_id} entre {start_date} et {end_date}."
        Utils.log_error(err_msg)
        raise HTTPException(status_code=404, detail=err_msg)
    return {"user_id": user_id, "messages": messages}

async def chats():
    # Get al chats here
    return {}

handler = Mangum(app)
