import os, threading, io, json, base64, hashlib
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from cryptography.fernet import Fernet

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
SIGNATURE = "COURAGEUX THE KING 🔥🔥🔥🔥\nwa.me/243973622250"

def get_fernet(password="COURAGEUX2025"):
    key = base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
    return Fernet(key)

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot COURAGEUX THE KING"

async def start(update: Update, context):
    conversations[update.effective_user.id] = []
    await update.message.reply_text(f"Je suis {SIGNATURE}\n👑 Envoie ton.dark, je déchiffre + txt + texte")

async def handle_dark(update: Update, context):
    doc = update.message.document
    file_name = doc.file_name
    user = update.effective_user.first_name
    file = await doc.get_file()
    data = await file.download_as_bytearray()
    raw = bytes(data)

    decrypted_text = None
    try:
        fernet = get_fernet()
        decrypted_text = fernet.decrypt(raw).decode('utf-8', errors='ignore')
    except:
        try: decrypted_text = base64.b64decode(raw).decode('utf-8', errors='ignore')
        except:
            try: decrypted_text = raw.decode('utf-8', errors='ignore')
            except: decrypted_text = None

    if not decrypted_text:
        await update.message.reply_text("❌ Fichier.dark invalide")
        return

    pretty = decrypted_text
    try:
        j = json.loads(decrypted_text)
        pretty = json.dumps(j, indent=4, ensure_ascii=False)
    except: pass

    # 1. Envoi en TEXT
    if len(pretty) > 3500:
        await update.message.reply_text(f"```json\n{pretty[:3500]}\n```", parse_mode="Markdown")
        await update.message.reply_text(f"Suite du config dans le.txt 👇\n\n{SIGNATURE}")
    else:
        await update.message.reply_text(f"```json\n{pretty}\n```\n\n{SIGNATURE}", parse_mode="Markdown")

    # 2. Fichier.txt
    info_txt = f"""Document de {SIGNATURE}
━━━━━━━━━━━━━━━━━━
File: {file_name}
Status: Decrypted Successfully
Requested by: {user}
Bot: {SIGNATURE}
━━━━━━━━━━━━━━━━━━

{pretty}
"""
    keyboard = [
        [InlineKeyboardButton("📤 EXPORT AS UNLOCKED", callback_data="export")],
        [InlineKeyboardButton("Channel", url="https://t.me/ton_channel"),
         InlineKeyboardButton("Contacter le King 🔥", url="https://wa.me/243973622250")],
    ]

    await update.message.reply_document(
        document=io.BytesIO(info_txt.encode('utf-8')),
        filename=f"{file_name}.txt",
        caption=f"✅ Decrypted Successfully\n👤 Requested by: {user}\n👑 {SIGNATURE}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def chat_gpt(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text
    if user_id not in conversations: conversations[user_id] = []
    conversations[user_id].append({"role":"user","content":text})
    conversations[user_id] = conversations[user_id][-20:]
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    comp = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role":"system","content":f"Tu t'appelles {SIGNATURE}, assistant IA français drôle et puissant."}] + conversations[user_id]
    )
    rep = comp.choices[0].message.content
    conversations[user_id].append({"role":"assistant","content":rep})
    await update.message.reply_text(f"{rep}\n\n— {SIGNATURE}")

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()
app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_dark))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
