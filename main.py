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
def home(): return "Bot COURAGEUX KING"

def b64_decode(s):
    try:
        s = s.strip().replace("darktunnel://","").replace("\n","").replace("\r","")
        s += "=" * (-len(s) % 4)
        return base64.urlsafe_b64decode(s).decode('utf-8', errors='ignore')
    except:
        try:
            return base64.b64decode(s).decode('utf-8', errors='ignore')
        except: return None

async def start(update: Update, context):
    await update.message.reply_text(f"Je suis {SIGNATURE}\nEnvoie ton.dark YOUTUBE, je te sors target server + uuid + path comme DarkTunnel!")

async def handle_dark(update: Update, context):
    doc = update.message.document
    fname = doc.file_name
    user = update.effective_user.first_name
    f = await doc.get_file()
    raw = (await f.download_as_bytearray()).decode('utf-8', errors='ignore').strip()

    decoded = b64_decode(raw)
    if not decoded:
        await update.message.reply_text("❌ Impossible de décoder le.dark")
        return

    try:
        j = json.loads(decoded)
    except:
        await update.message.reply_text(f"Décodé mais erreur JSON:\n{decoded[:2000]}")
        return

    # --- EXTRACTION STYLE DARKTUNNEL APP ---
    try:
        # Le chemin est dans encryptedLockedConfig -> EncryptedLockedConfig -> V2RayConfig
        v2 = j.get("encryptedLockedConfig", {}).get("EncryptedLockedConfig", {}).get("V2RayConfig", {}).get("EncryptedConfig", {})
        if not v2:
            # Essaie autre chemin si c'est déjà décodé
            v2 = j.get("encryptedLockedConfig", {}).get("EncryptedLockedConfig", {}).get("V2RayConfig", {}).get("EncryptedConfig", j)

        outbound = v2.get("outbounds", [{}])[0]
        vnext = outbound.get("settings", {}).get("vnext", [{}])[0]
        address = vnext.get("address", "Non trouvé")
        port = vnext.get("port", "")
        uuid = vnext.get("users", [{}])[0].get("id", "Non trouvé")

        stream = outbound.get("streamSettings", {})
        network = stream.get("network", "ws")
        security = stream.get("security", "tls")
        sni = stream.get("tlsSettings", {}).get("serverName", address)
        path = stream.get("wsSettings", {}).get("path", "/")
        host_header = stream.get("wsSettings", {}).get("headers", {}).get("Host", sni)

        # Proxy HTTP aussi
        inject = j.get("encryptedLockedConfig", {}).get("EncryptedLockedConfig", {}).get("InjectConfig", {})
        proxy_host = inject.get("EncryptedProxyHost", "Non trouvé")
        proxy_port = inject.get("EncryptedProxyPort", "")
        payload = inject.get("EncryptedPayload", "")

        # Message comme dans ta capture DarkTunnel
        darktunnel_msg = f"""DarkTunnel

VLess • Websocket SSL/TLS
target server
{address}:{port}

uuid
{uuid}

path
{path}

server name indication
{sni}

header host
{host_header}

--- PROXY ---
proxy host: {proxy_host}:{proxy_port}
payload: {payload}

👑 {SIGNATURE}
"""
        await update.message.reply_text(darktunnel_msg)

        # Fichier txt
        full_json = json.dumps(j, indent=4, ensure_ascii=False)
        txt = f"""Document de {SIGNATURE}
File: {fname}
Requested by: {user}

=== DARKTUNNEL DECODED ===

Target Server: {address}:{port}
UUID: {uuid}
Path: {path}
SNI: {sni}
Header Host: {host_header}
Network: {network} | Security: {security}

Proxy: {proxy_host}:{proxy_port}
Payload: {payload}

=== FULL JSON ===
{full_json}

{SIGNATURE}
"""
        keyboard = [[InlineKeyboardButton("📤 EXPORT AS UNLOCKED", callback_data="export")],
                    [InlineKeyboardButton("Contacter le King 🔥", url="https://wa.me/243973622250")]]

        await update.message.reply_document(
            document=io.BytesIO(txt.encode('utf-8')),
            filename=f"{fname}_DARKTUNNEL.txt",
            caption=f"✅ Decrypted comme DarkTunnel\n👤 {user}\n👑 {SIGNATURE}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        await update.message.reply_text(f"Erreur extraction: {e}\n\nJSON brut:\n{json.dumps(j, indent=2)[:3000]}\n\n{SIGNATURE}")

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
