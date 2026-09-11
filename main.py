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

def b64_decode(s):
    try:
        s = s.strip().replace("darktunnel://","")
        s += "=" * (-len(s) % 4)
        return base64.urlsafe_b64decode(s).decode('utf-8', errors='ignore')
    except:
        try:
            s += "=" * (-len(s) % 4)
            return base64.b64decode(s).decode('utf-8', errors='ignore')
        except: return None

def format_like_univers(data, indent=0):
    out = ""
    prefix = " " * indent
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                icon = "[✧]" if indent==0 else "[~]"
                out += f"{prefix}{icon} [{k}] :\n"
                out += format_like_univers(v, indent+1)
            elif isinstance(v, list):
                icon = "[✧]" if indent==0 else "[~]"
                out += f"{prefix}{icon} [{k}] :\n"
                for item in v:
                    out += format_like_univers(item, indent+1)
            else:
                out += f"{prefix} [-] [{k}] : {v}\n"
    return out

async def start(update: Update, context):
    await update.message.reply_text(f"Je suis {SIGNATURE}\nEnvoie ton.dark YOUTUBE, je te le déchiffre style Univers!")

async def handle_dark(update: Update, context):
    doc = update.message.document
    fname = doc.file_name
    user = update.effective_user.first_name
    file = await doc.get_file()
    raw = (await file.download_as_bytearray()).decode('utf-8', errors='ignore').strip()

    # Décodage darktunnel
    decoded = b64_decode(raw)
    if not decoded:
        await update.message.reply_text("❌ Fichier non décodable")
        return

    try:
        j = json.loads(decoded)
    except:
        await update.message.reply_text(f"Décodé mais pas JSON:\n{decoded[:3000]}")
        return

    # Format style Univers
    pretty_univers = format_like_univers(j)

    # Message principal comme sur ta capture
    caption = f"""📂 File : {fname}
✅ Decrypted by {SIGNATURE}

{pretty_univers[:3500]}
"""

    await update.message.reply_text(caption)

    # Deuxième message avec HOST extrait clairement
    try:
        host = j['encryptedLockedConfig']['EncryptedLockedConfig']['InjectConfig']['EncryptedProxyHost']
        port = j['encryptedLockedConfig']['EncryptedLockedConfig']['InjectConfig']['EncryptedProxyPort']
        payload = j['encryptedLockedConfig']['EncryptedLockedConfig']['InjectConfig']['EncryptedPayload']
        await update.message.reply_text(f"""🌐 **HOST EXTRAIT:**

**ProxyHost:** {host}
**ProxyPort:** {port}
**Payload:** {payload}

👑 {SIGNATURE}""")
    except:
        pass

    # Fichier.txt
    txt_content = f"""Document de {SIGNATURE}
File: {fname}
Requested by: {user}

{pretty_univers}

--- RAW JSON ---
{json.dumps(j, indent=4, ensure_ascii=False)}

{SIGNATURE}
"""
    keyboard = [[InlineKeyboardButton("📤 EXPORT AS UNLOCKED", callback_data="export")],
                [InlineKeyboardButton("Contacter le King 🔥", url="https://wa.me/243973622250")]]

    await update.message.reply_document(
        document=io.BytesIO(txt_content.encode('utf-8')),
        filename=f"{fname}.txt",
        caption=f"✅ Decrypted Successfully\n👤 Requested by: {user}\n👑 {SIGNATURE}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def chat_gpt(update: Update, context):
    uid = update.effective_user.id
    if uid not in conversations: conversations[uid]=[]
    conversations[uid].append({"role":"user","content":update.message.text})
    conversations[uid]=conversations[uid][-20:]
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"system","content":f"Tu es {SIGNATURE}"}]+conversations[uid])
    rep = comp.choices[0].message.content
    conversations[uid].append({"role":"assistant","content":rep})
    await update.message.reply_text(f"{rep}\n\n— {SIGNATURE}")

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()
app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_dark))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
