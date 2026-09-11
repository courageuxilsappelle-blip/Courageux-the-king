import os, threading, io, json, base64
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
SIGNATURE = "COURAGEUX THE KING 🔥🔥🔥🔥\nwa.me/243973622250"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot COURAGEUX"

def b64_try_decode(s):
    try:
        s = s.strip()
        s += "=" * (-len(s) % 4)
        return base64.urlsafe_b64decode(s).decode('utf-8', errors='ignore')
    except:
        try:
            s += "=" * (-len(s) % 4)
            return base64.b64decode(s).decode('utf-8', errors='ignore')
        except:
            return None

async def start(update: Update, context):
    await update.message.reply_text(f"Je suis {SIGNATURE}\nEnvoie ton YOUTUBE.dark, je te sors le HOST / SERVER direct.")

async def handle_dark(update: Update, context):
    doc = update.message.document
    fname = doc.file_name
    user = update.effective_user.first_name
    f = await doc.get_file()
    raw = (await f.download_as_bytearray()).decode('utf-8', errors='ignore').strip()

    # 1ere couche darktunnel://
    payload = raw.replace("darktunnel://", "").strip()
    first = b64_try_decode(payload)
    if not first:
        await update.message.reply_text("❌ 1ere couche non décodable")
        return

    try:
        j = json.loads(first)
    except:
        await update.message.reply_text(f"1ere couche décodée mais pas JSON:\n{first[:3000]}")
        return

    # 2eme couche encryptedLockedConfig
    enc_locked = j.get("encryptedLockedConfig", "")
    second_decoded = b64_try_decode(enc_locked) if isinstance(enc_locked, str) else None

    # Essaye de parser la 2eme couche
    host_info = "Non trouvé"
    server_info = "Non trouvé"
    payload_info = "Non trouvé"

    if second_decoded:
        try:
            j2 = json.loads(second_decoded)
            pretty2 = json.dumps(j2, indent=2, ensure_ascii=False)
            # Cherche le HOST partout
            text_all = json.dumps(j2)
            # Extraction intelligente
            if "ProxyHost" in text_all or "Host" in text_all:
                host_info = pretty2[:3000]
        except:
            # Si c'est pas JSON, c'est peut-être encore encodé
            host_info = second_decoded[:3000]

    # Extraction directe du JSON principal si déjà présent
    full_pretty = json.dumps(j, indent=4, ensure_ascii=False)

    # Message final avec HOST
    msg = f"""✅ **Decrypted Successfully**
👤 Requested by: {user}

📁 File: {fname}
🔓 Type: {j.get('type','TROJAN')} - {j.get('name','YOUTUBE')}

🌐 **SERVEUR / HOST trouvé:**
