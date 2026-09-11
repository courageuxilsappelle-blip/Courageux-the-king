import os
import threading
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# --- TON BOT - METS TES FONCTIONS ICI ---
async def start(update, context):
    await update.message.reply_text("Bot est en ligne! ✅")

# --------------------------------------------------------

# Serveur web pour Render gratuit
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is Live!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Lance le serveur web en arrière-plan
    threading.Thread(target=run_web, daemon=True).start()

    # Lance le bot Telegram
    TOKEN = os.environ.get("TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    # AJOUTE TES AUTRES HANDLERS ICI
    
    print("Bot démarré...")
    app.run_polling()
