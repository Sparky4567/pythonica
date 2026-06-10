import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

BOT_TOKEN = ""

OPENWEBUI_URL = "http://localhost:3000/api/chat/completions"
#OPENWEBUI_API_KEY = "YOUR_API_KEY"

MODEL = "gemma3:270m"

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = update.message.text
    print(prompt)
#    payload = {
#        "model": MODEL,
#        "messages": [
#            {"role": "user", "content": prompt}
#        ]
#    }

#    headers = {
#        "Authorization": f"Bearer {OPENWEBUI_API_KEY}",
#        "Content-Type": "application/json"
#    }

#    response = requests.post(
#        OPENWEBUI_URL,
#        json=payload
#       headers=headers
#    )

#    answer = response.json()["choices"][0]["message"]["content"]

#    await update.message.reply_text(answer)

app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, chat))

app.run_polling()
