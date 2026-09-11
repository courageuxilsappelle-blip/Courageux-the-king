import os, threading, io, json, base64, re, zipfile
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
SIGNATURE = "COURAGEUX THE KING 🔥🔥🔥🔥\nwa.me/243973622250"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot KING"

def parse_json_recursive(data, prefix=""):
    """Parcourt et formate le dictionnaire JSON à la manière du bot de décryptage"""
    output = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, (dict, list)):
                output.append(f"{prefix}[~] [{k}] :")
                output.extend(parse_json_recursive(v, prefix + "    "))
            else:
                output.append(f"{prefix}[-] [{k}] : {v}")
    elif isinstance(data, list):
        for item in data:
            output.extend(parse_json_recursive(item, prefix))
    return output

def extract_hosts_from_binary(data_bytes):
    try:
        text = data_bytes.decode('utf-8', errors='ignore')
    except:
        text = str(data_bytes)
    domains = re.findall(r'[a-z0-9\-]{2,}\.[a-z0-9\-\.]+\.[a-z]{2,}', text)
    ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text)
    paths = re.findall(r'\/[A-Za-z0-9\/_\-\@]{3,}', text)
    return list(set(domains))[:20], list(set(ips))[:10], list(set(paths))[:10]

async def start(update: Update, context):
    uid = update.effective_user.id
    conversations[uid] = []
    await update.message.reply_text(f"Je suis {SIGNATURE}\nEnvoie .dark .nm .tnl, je te sors la config complète!")

async def handle_file(update: Update, context):
    doc = update.message.document
    fname = doc.file_name.lower()
    user = update.effective_user.first_name
    uid = update.effective_user.id
    if uid not in conversations: conversations[uid]=[]

    f = await doc.get_file()
    raw = await f.download_as_bytearray()
    raw_bytes = bytes(raw)

    # 1. Tentative d'analyse en tant que JSON brut ou ZIP contenant du JSON (.nm / .ss)
    try:
        text_content = raw_bytes.decode('utf-8', errors='ignore').strip()
        data_json = None
        
        if text_content.startswith("{") or text_content.startswith("["):
            data_json = json.loads(text_content)
        elif zipfile.is_zipfile(io.BytesIO(raw_bytes)):
            with zipfile.ZipFile(io.BytesIO(raw_bytes)) as z:
                content = z.read(z.namelist()[0]).decode('utf-8', errors='ignore')
                data_json = json.loads(content)
        
        if data_json:
            formatted_lines = parse_json_recursive(data_json)
            full_text = "\n".join(formatted_lines)
            
            # Découpage par morceaux si le texte est trop long pour Telegram (limite ~4000 caractères)
            chunks = [full_text[i:i+3500] for i in range(0, len(full_text), 3500)]
            for idx, chunk in enumerate(chunks):
                header = "Full Config 🔓\n\n" if idx == 0 else ""
                footer = f"\n\n👑 {SIGNATURE}" if idx == len(chunks) - 1 else ""
                await update.message.reply_text(f"{header}{chunk}{footer}")
            return
    except Exception as e:
        pass

    # 2. Essaie DARKTUNNEL base64
    decoded_text = None
    try:
        txt = raw_bytes.decode('utf-8', errors='ignore').strip().replace("darktunnel://","")
        txt_padded = txt + "=" * (-len(txt) % 4)
        try:
            decoded_text = base64.urlsafe_b64decode(txt_padded).decode('utf-8', errors='ignore')
        except:
            decoded_text = base64.b64decode(txt_padded).decode('utf-8', errors='ignore')
        j = json.loads(decoded_text)
        
        enc = j.get("encryptedLockedConfig",{}).get("EncryptedLockedConfig",{})
        v2 = enc.get("V2RayConfig",{}).get("EncryptedConfig",{})
        outbound = v2.get("outbounds",[{}])[0] if v2.get("outbounds") else {}
        vnext = outbound.get("settings",{}).get("vnext",[{}])[0] if outbound.get("settings") else {}
        address = vnext.get("address","?")
        port = vnext.get("port","")
        uuid = vnext.get("users",[{}])[0].get("id","?") if vnext.get("users") else "?"
        sni = outbound.get("streamSettings",{}).get("tlsSettings",{}).get("serverName","?")
        path = outbound.get("streamSettings",{}).get("wsSettings",{}).get("path","?")
        host_h = outbound.get("streamSettings",{}).get("wsSettings",{}).get("headers",{}).get("Host","?")

        await update.message.reply_text(f"""DarkTunnel Décodé ✅

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

👑 {SIGNATURE}""")
        return
    except:
        pass

    # 3. Si tout échoue -> extraction brute
    domains, ips, paths = extract_hosts_from_binary(raw_bytes)

    msg = f"""⚠️ Fichier {fname} chiffré (.nm / .ss)

Il n'est pas en Base64 simple, il faut la clé de l'app. Mais j'ai extrait ce que j'ai trouvé dedans:

🌐 DOMAINES / HOSTS trouvés:
{chr(10).join(domains[:10]) if domains else 'Aucun domaine clair - 100% chiffré'}

📡 IP trouvées:
{chr(10).join(ips[:10]) if ips else 'Aucune'}

📁 PATHS trouvés:
{chr(10).join(paths[:10]) if paths else 'Aucun'}

👑 {SIGNATURE}
"""
    await update.message.reply_text(msg)

async def chat_gpt(update: Update, context):
    uid = update.effective_user.id
    if uid not in conversations: conversations[uid]=[]
    conversations[uid].append({"role":"user","content":update.message.text})
    conversations[uid]=conversations[uid][-20:]
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"system","content":f"Tu es {SIGNATURE}, tu te souviens de tout."}]+conversations[uid])
    rep = comp.choices[0].message.content
    conversations[uid].append({"role":"assistant","content":rep})
    await update.message.reply_text(f"{rep}\n\n— {SIGNATURE}")

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()
app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
    
