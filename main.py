import os, threading, io, json, base64
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {} # uid -> list de messages
SIGNATURE = "COURAGEUX THE KING 🔥🔥🔥🔥\nwa.me/243973622250"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot COURAGEUX KING"

def try_b64_decode(s):
    s = s.strip().replace("darktunnel://","").replace("\n","").replace("\r","").replace(" ","")
    # Essaie 3 méthodes
    for _ in range(2):
        try:
            padded = s + "=" * (-len(s) % 4)
            decoded = base64.urlsafe_b64decode(padded)
            return decoded.decode('utf-8', errors='ignore')
        except: pass
        try:
            padded = s + "=" * (-len(s) % 4)
            decoded = base64.b64decode(padded)
            return decoded.decode('utf-8', errors='ignore')
        except: pass
    return None

async def start(update: Update, context):
    uid = update.effective_user.id
    conversations[uid] = [] # initialise mémoire
    await update.message.reply_text(f"Salut je suis {SIGNATURE}\nEnvoie ton.dark, je te donne HOST, UUID, PATH comme DarkTunnel!")

async def handle_dark(update: Update, context):
    doc = update.message.document
    fname = doc.file_name
    user = update.effective_user.first_name or "King"
    uid = update.effective_user.id
    if uid not in conversations: conversations[uid] = []

    file_obj = await doc.get_file()
    raw_bytes = await file_obj.download_as_bytearray()

    # Essaie de lire comme texte
    try:
        raw_text = raw_bytes.decode('utf-8', errors='ignore').strip()
    except:
        raw_text = ""

    # Si c'est binaire, essaie quand même
    if not raw_text:
        raw_text = str(raw_bytes)

    decoded = try_b64_decode(raw_text)

    # Si ça échoue, essaie directement le bytes comme base64
    if not decoded:
        try:
            decoded = raw_bytes.decode('utf-8', errors='ignore')
            decoded = try_b64_decode(decoded) or decoded
        except:
            pass

    if not decoded:
        await update.message.reply_text(f"❌ Encore impossible de décoder {fname}. Envoie le fichier sur @COURAGEUX pour que je vois.\n\n{SIGNATURE}")
        return

    try:
        j = json.loads(decoded)
        # Stocke dans mémoire pour qu'il s'en souvienne
        conversations[uid].append({"role":"user","content":f"decode {fname}"})
        conversations[uid].append({"role":"assistant","content":f"J'ai décodé {fname}: {decoded[:500]}"})

        # --- FORMAT DARKTUNNEL APP ---
        try:
            enc = j.get("encryptedLockedConfig", {}).get("EncryptedLockedConfig", {})
            v2 = enc.get("V2RayConfig", {}).get("EncryptedConfig", {})
            outbound = v2.get("outbounds", [{}])[0]
            vnext = outbound.get("settings", {}).get("vnext", [{}])[0]
            address = vnext.get("address", "?")
            port = vnext.get("port", "")
            uuid = vnext.get("users", [{}])[0].get("id", "?")
            stream = outbound.get("streamSettings", {})
            sni = stream.get("tlsSettings", {}).get("serverName", address)
            path = stream.get("wsSettings", {}).get("path", "/")
            host_h = stream.get("wsSettings", {}).get("headers", {}).get("Host", sni)
            inject = enc.get("InjectConfig", {})
            proxy_host = inject.get("EncryptedProxyHost", "")
            proxy_port = inject.get("EncryptedProxyPort", "")

            msg = f"""DarkTunnel - Décodé par {SIGNATURE}

VLess · Websocket SSL/TLS
target server
{address}:{port}

uuid
{uuid}

path
{path}

server name indication
{sni}

header host
{host_h}

proxy: {proxy_host}:{proxy_port}
"""
            await update.message.reply_text(msg)
        except Exception as e:
            await update.message.reply_text(f"✅ Décodé mais format spécial:\n{json.dumps(j, indent=2)[:3500]}\n\nErreur détail: {e}\n\n{SIGNATURE}")

        # Fichier txt
        txt = f"Decoded by {SIGNATURE}\nFile: {fname}\n\n{json.dumps(j, indent=4, ensure_ascii=False)}"
        await update.message.reply_document(
            document=io.BytesIO(txt.encode('utf-8')),
            filename=f"{fname}_DECODED.txt",
            caption=f"✅ Decrypted Successfully\n👤 {user}\n👑 {SIGNATURE}"
        )

    except Exception as e:
        await update.message.reply_text(f"Contenu décodé (pas JSON):\n{decoded[:3500]}\n\nErreur: {e}\n\n{SIGNATURE}")

async def chat_gpt(update: Update, context):
    uid = update.effective_user.id
    text = update.message.text
    if uid not in conversations:
        conversations[uid] = []
    conversations[uid].append({"role": "user", "content": text})
    conversations[uid] = conversations[uid][-20:] # garde 20 messages de mémoire

    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    try:
        comp = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role":"system","content":f"Tu es {SIGNATURE}, tu te souviens de tout ce qu'on a parlé. Réponds en français."}] + conversations[uid]
        )
        rep = comp.choices[0].message.content
        conversations[uid].append({"role":"assistant","content":rep})
        await update.message.reply_text(f"{rep}\n\n— {SIGNATURE}")
    except Exception as e:
        await update.message.reply_text(f"Erreur IA: {e}\n\n{SIGNATURE}")

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()
app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_dark))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
