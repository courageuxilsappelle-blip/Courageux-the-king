import os, threading
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot IA Courageux en ligne!"

async def start(update: Update, context):
    await update.message.reply_text("Je suis Courageux, ton ChatGPT sur Telegram 👑 Dis-moi tout!")

async def chat_gpt(update: Update, context):
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Tu t'appelles Courageux, tu es un assistant IA très utile, tu parles en français, tu es drôle et intelligent comme ChatGPT."},
                {"role": "user", "content": update.message.text}
            ]
        )
        await update.message.reply_text(completion.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"Erreur IA: {e}")

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()

app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
