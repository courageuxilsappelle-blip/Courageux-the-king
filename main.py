import os, threading, io, json, base64, hashlib
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
SIGNATURE = "COURAGEUX THE KING 🔥🔥🔥🔥\nwa.me/243973622250"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return f"Bot {SIGNATURE}"

async def start(update: Update, context):
    conversations[update.effective_user.id] = []
    await update.message.reply_text(f"Salut je suis {SIGNATURE} 👑\nEnvoie ton fichier.dark DARKTUNNEL, je te donne les infos dedans!")

async def handle_dark(update: Update, context):
    doc = update.message.document
    file_name = doc.file_name
    user = update.effective_user.first_name or "King"
    f = await doc.get_file()
    raw_bytes = await f.download_as_bytearray()
    content = raw_bytes.decode('utf-8', errors='ignore').strip()

    # Enlève le prefix darktunnel://
    if content.startswith("darktunnel://"):
        b64_payload = content.replace("darktunnel://", "").strip()
    else:
        b64_payload = content

    # Décode Base64
    try:
        # ajoute le padding manquant
        missing = len(b64_payload) % 4
        if missing: b64_payload += "=" * (4 - missing)
        decoded_bytes = base64.urlsafe_b64decode(b64_payload)
        decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
        # Essaie de formatter en JSON joli
        try:
            j = json.loads(decoded_str)
            pretty_json = json.dumps(j, indent=4, ensure_ascii=False)
        except:
            pretty_json = decoded_str
    except Exception as e:
        await update.message.reply_text(f"❌ Impossible de décoder: {e}\n\n{SIGNATURE}")
        return

    # 1. Envoie en TEXT comme sur ton screen (JSON)
    text_to_send = f"JSON\n\n{content}\n\n--- DECODED ---\n{pretty_json[:3500]}"
    if len(text_to_send) > 4000:
        await update.message.reply_text(f"JSON\n\n{content[:2000]}...\n\n✅ Decoded part:\n{pretty_json[:2000]}", parse_mode="Markdown")
    else:
        await update.message.reply_text(text_to_send)

    # 2. Envoie le.txt avec les infos
    txt_content = f"""Document de {SIGNATURE}
━━━━━━━━━━━━━━━━
File: {file_name}
Size: 8,8 KB
Status: Decrypted Successfully
Requested by: {user}
Type: DARK (17)
━━━━━━━━━━━━━━━━
RAW:
{content}

DECODED JSON:
{pretty_json}

━━━━━━━━━━━━━━━━
{SIGNATURE}
"""
    keyboard = [
        [InlineKeyboardButton("📤 EXPORT AS UNLOCKED", callback_data="export")],
        [InlineKeyboardButton("Channel", url="https://t.me/ton_channel"),
         InlineKeyboardButton("Contacter le King 🔥", url="https://wa.me/243973622250")],
    ]

    await update.message.reply_document(
        document=io.BytesIO(txt_content.encode('utf-8')),
        filename=f"{file_name}.txt",
        caption=f"✅ Decrypted Successfully\n👤 Requested by: {user}\n👑 {SIGNATURE}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def chat_gpt(update: Update, context):
    user_id = update.effective_user.id
    if user_id not in conversations: conversations[user_id] = []
    conversations[user_id].append({"role":"user","content":update.message.text})
    conversations[user_id] = conversations[user_id][-20:]
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    comp = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role":"system","content":f"Tu es {SIGNATURE}"}] + conversations[user_id]
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
