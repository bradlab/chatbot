from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from mangum import Mangum
import json, boto3
from mistralai import Mistral
import asyncio

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
    asyncio.create_task(configure_telegram_webhook()) # <-- C'est la source probable du problème

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
        "id": {
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

@app.post("/webhook")
async def telegram_webhook(request: Request):
    #Endpoint pour recevoir les mises à jour de Telegram
    try:
        update_json = await request.json()
        await process_telegram_update(update_json)
        return {"status": "ok"}
    except Exception as e:
        Utils.log_error(f"Erreur de traitement du webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def chats():
    # Get al chats here
    return {}

handler = Mangum(app)
