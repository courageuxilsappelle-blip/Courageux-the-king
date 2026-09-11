from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import requests
import os

TOKEN = os.environ.get("TOKEN","8611301789:AAGPaVmAwNFENIRln2Ts7pEojmMdrntYVjU")
GROQ_KEY = os.environ.get("GROQ_KEY","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")

def ia(q):
    try:
        r = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {GROQ_KEY}"}, json={"model":"openai/gpt-oss-20b","messages":[{"role":"user","content":q}]}, timeout=30)
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Erreur: {e}"

async def start(u,c):
    await u.message.reply_text("Bot 24h en ligne! ✅")

async def chat(u,c):
    await u.message.reply_text(ia(u.message.text))

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
app.run_polling()
