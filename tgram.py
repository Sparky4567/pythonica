import requests
from telegram import Update
from modules.settings.settings import MY_MODEL
from modules.settings.settings import TELEGRAM_TOKEN
from modules.settings.settings import TELEGRAM_ENABLED
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = TELEGRAM_TOKEN

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = MY_MODEL


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    
    prompt = update.message.text

    print(f"Received: {prompt}")

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }

    try:

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=120
        )

        response.raise_for_status()

        data = response.json()

        answer = data["message"]["content"]

        print(f"Reply: {answer}")

        await update.message.reply_text(answer)

    except Exception as e:

        print("ERROR:", e)

        await update.message.reply_text(
            f"Error contacting Ollama:\n{e}"
        )


def tele_run():

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            chat
        )
    )

    print("Bot started...")

    app.run_polling()

if TELEGRAM_ENABLED is False:
    try:
        tele_run()
    except Exception as e:
        print(f"Exception {e}")
else:
    print("Change TELEGRAM_ENABLED in settings.py to true")