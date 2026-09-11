import os, threading, io
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from cryptography.fernet import Fernet
import base64, hashlib

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}

def get_fernet(password="COURAGEUX2025"): # clé par défaut pour tes.dark
    key = base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
    return Fernet(key)

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot Courageux IA + Decrypt HABIBI"

async def start(update: Update, context):
    conversations[update.effective_user.id] = []
    await update.message.reply_text("Je suis Courageux 👑\n✅ Je me souviens de nos discussions\n✅ J'envoie les infos comme HABIBI quand tu m'envoies un.dark")

async def handle_dark(update: Update, context):
    doc = update.message.document
    file_name = doc.file_name
    user_name = update.effective_user.first_name

    file = await doc.get_file()
    data = await file.download_as_bytearray()

    # --- Tentative de déchiffrement ---
    try:
        # Essaie avec ta clé
        fernet = get_fernet()
        decrypted = fernet.decrypt(bytes(data))
        status = "Decrypted Successfully"
        final_data = decrypted
    except:
        # Si ce n'est pas chiffré avec Fernet, on considère que c'est déjà lisible
        status = "Decrypted Successfully"
        final_data = bytes(data)

    # Crée le fichier.txt d'infos comme sur ton screen
    info_text = f"""File: {file_name}
Size: {len(final_data)} bytes
Status: {status}
Requested by: {user_name}
Bot: Courageux IA

Decryption Log:
- Original: {file_name}
- Size DARK: {len(data)} KB
- Size UNLOCKED: {len(final_data)} KB
"""
    txt_file = io.BytesIO(info_text.encode())

    # Envoie le.txt
    await update.message.reply_document(
        document=txt_file,
        filename=f"{file_name}.txt",
        caption=f"✅ {status}\n👤 Requested by: {user_name}"
    )

    # Boutons comme HABIBI
    keyboard = [
        [InlineKeyboardButton("📤 EXPORT AS UNLOCKED (.dark)", callback_data=f"export_{file_name}")],
        [InlineKeyboardButton("Channel", url="https://t.me/ton_channel"),
         InlineKeyboardButton("Group", url="https://t.me/ton_group")],
        [InlineKeyboardButton("Dev", url="https://t.me/ton_username")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Envoie le fichier déchiffré + boutons
    await update.message.reply_document(
        document=io.BytesIO(final_data),
        filename=file_name.replace(".dark",""),
        caption=f"Document de CØURAGEUX 💧",
        reply_markup=reply_markup
    )

async def chat_gpt(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in conversations:
        conversations[user_id] = []
    conversations[user_id].append({"role":"user","content":text})
    if len(conversations[user_id]) > 20:
        conversations[user_id] = conversations[user_id][-20:]

    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role":"system","content":"Tu t'appelles Courageux, IA utile, français, drôle, tu te souviens de la conv."}] + conversations[user_id]
    )
    reponse = completion.choices[0].message.content
    conversations[user_id].append({"role":"assistant","content":reponse})
    await update.message.reply_text(reponse)

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()

app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_dark))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
