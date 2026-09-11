import os, threading
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}

# UN SEUL NOM - SIGNATURE UNIQUE
SIGNATURE = "COURAGEUX THE KING"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot IA Courageux en ligne!"

async def start(update: Update, context):
    conversations[update.effective_user.id] = []
    await update.message.reply_text(f"Je suis {SIGNATURE} 👑 ton ChatGPT sur Telegram!\nJe me souviens de tout!")

async def chat_gpt(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text

    await context.bot.send_chat_action(update.effective_chat.id, "typing")

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({"role": "user", "content": text})

    if len(conversations[user_id]) > 20:
        conversations[user_id] = conversations[user_id][-20:]

    try:
        messages_to_groq = [
            {"role": "system", "content": f"Tu t'appelles {SIGNATURE}, assistant IA utile, tu parles français, drôle et intelligent. Tu termines TOUJOURS chaque réponse par '{SIGNATURE}'."}
        ] + conversations[user_id]

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_to_groq
        )
        reponse = completion.choices[0].message.content

    except:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages_to_groq
        )
        reponse = completion.choices[0].message.content

    conversations[user_id].append({"role": "assistant", "content": reponse})
    await update.message.reply_text(f"{reponse}\n\n{SIGNATURE}")

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()

app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
