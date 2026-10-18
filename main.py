import os, re, requests, threading, datetime, random, base64, socket, time, asyncio, textwrap, json, tempfile, unicodedata, subprocess
from pathlib import Path
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont
import urllib3
import msgpack
from fpdf import FPDF
urllib3.disable_warnings()

TOKEN = os.getenv("TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
print("=== V27 FINAL VISION FIX ===")

try:
    groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
except:
    groq_client = None

conversations = {}
SIGNATURE = "COURAGEUX THE KING"

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"Bot {SIGNATURE} V27 VISION FINAL LIVE"

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), use_reloader=False), daemon=True).start()
time.sleep(1)

MATRIX_MODULES = {}
for mod_name in ["DARKTUNNEL","HTTPCUSTOM","HTTPINJECTOR","NPVTUNNEL","NETMOD","OPENTUNNEL_TNL","SOCKSHTTP","SSCCUSTOM","SocksIP","Ha_Tunnel","ZIVPN","V2BOX","netmod_decoder","HL_Tunnel","HttpCustom","OpenTunnel"]:
    try:
        MATRIX_MODULES[mod_name] = __import__(mod_name)
    except:
        pass

async def owner_cmd(update,context):
    save_user(update.effective_user.id)
    try:
        r=requests.get("https://api.github.com/repos/matrixzat/vpn-decryptor",timeout=10,headers={"User-Agent":"Mozilla/5.0"}).json()
        txt=f"PREUVE OWNER\nRepo: matrixzat/vpn-decryptor\nOwner: {r.get('owner',{}).get('login')}\n{SIGNATURE}"
        await update.message.reply_text(txt)
    except Exception as e:
        await update.message.reply_text(f"err {e}")

USERS_FILE = "users.txt"
def save_user(uid):
    try:
        if not os.path.exists(USERS_FILE):
            open(USERS_FILE,"w").close()
        with open(USERS_FILE,"r") as f:
            d = f.read()
        if str(uid) not in d:
            with open(USERS_FILE,"a") as f:
                f.write(f"{uid}\n")
    except:
        pass

def get_total_users():
    try:
        with open(USERS_FILE,"r") as f:
            return len([l for l in f if l.strip()])
    except:
        return 0

def to_3d(t):
    return t

def create_pdf_book(title, content):
    try:
        content = re.sub(r'\*\*', '', content)
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 26)
        pdf.ln(50)
        pdf.multi_cell(0, 14, title[:80], align='C')
        pdf_path = f"/tmp/{title[:15].replace(' ','_')}.pdf"
        pdf.output(pdf_path)
        return pdf_path
    except:
        return None

def clean_url(u):
    return u.strip().split('?is=')[0].split('&is=')[0].split('?si=')[0]
def get_yt_id(u):
    m = re.search(r'(?:v=|be/|shorts/|embed/)([A-Za-z0-9_-]{11})', u)
    return m.group(1) if m else None
def is_link(t):
    return any(x in t.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com","fb.watch","facebook.com"])
def load_vmess():
    try:
        env = os.getenv("VMESS_DATA")
        if env:
            return [l.strip() for l in env.splitlines() if l.strip().startswith("vmess://")]
        if os.path.exists("vmess.txt"):
            with open("vmess.txt","r") as f:
                return [l.strip() for l in f if l.strip().startswith("vmess://")]
        return []
    except:
        return []
def get_random_vmess(n=5):
    a = load_vmess()
    return random.sample(a, min(n,len(a))) if a else None
def get_host_info(host):
    try:
        ip = socket.gethostbyname(host)
        return {"ip": ip}
    except Exception as e:
        return {"error": str(e)}
def check_blacklist_dns(ip):
    blacklists = ["zen.spamhaus.org","bl.spamcop.net","b.barracudacentral.org"]
    try:
        reversed_ip = ".".join(reversed(ip.split(".")))
        listed = []
        clean = 0
        for bl in blacklists:
            try:
                socket.gethostbyname(f"{reversed_ip}.{bl}")
                listed.append(bl)
            except socket.gaierror:
                clean += 1
            except:
                pass
        return listed, clean, len(blacklists)
    except:
        return [], 0, 3
def check_port_200(host, ip, port):
    result = {"port":port,"open":False,"status":"FERME","is_200":False,"code":0}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        if s.connect_ex((ip, int(port)))!= 0:
            s.close()
            return result
        s.close()
        result["open"] = True
        result["status"] = "OUVERT TCP"
        result["is_200"] = True
    except:
        pass
    return result

def get_todays_fixtures():
    return ["Man United vs Man City","Levante vs Barcelona","Napoli vs Bologna"]

def predict_exact_score(match):
    if not groq_client:
        return f"{match} => 2-1 (62%)"
    try:
        comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":f"Score exact EA FC 26 en francais pour: {match}"}],temperature=0.4)
        return comp.choices[0].message.content
    except:
        return f"{match} => 2-1 (62%)"

async def start(update,context):
    save_user(update.effective_user.id)
    await update.message.reply_text(f"Je suis {SIGNATURE}")

async def stats_cmd(update,context):
    save_user(update.effective_user.id)
    await update.message.reply_text(f"Total: {get_total_users()} {SIGNATURE}")

async def vmess_cmd(update,context):
    save_user(update.effective_user.id)
    s = get_random_vmess(5)
    if not s:
        await update.message.reply_text("Aucun serveur")
        return
    await update.message.reply_text("VMESS\n\n"+"\n\n".join(s)+f"\n\n{SIGNATURE}")

async def pdf_cmd(update,context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("📚 /pdf + sujet")
        return
    sujet = " ".join(context.args)
    await update.message.reply_text(f"📚 Generation: {sujet}")
    try:
        prompt = f"Redige un livre en francais sur : {sujet}. 1500 mots."
        contenu = None
        for model_id in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "llama-3.3-70b-versatile"]:
            try:
                comp = groq_client.chat.completions.create(model=model_id, messages=[{"role":"user","content":prompt}], temperature=0.7, max_tokens=4000)
                contenu = comp.choices[0].message.content
                if contenu and len(contenu) > 300:
                    break
            except:
                continue
        await update.message.reply_text(contenu[:4000])
    except Exception as e:
        await update.message.reply_text(f"Erreur PDF: {e}")

async def scan_cmd(update,context):
    save_user(update.effective_user.id)
    host = context.args[0] if context.args else "1.1.1.1"
    await update.message.reply_text(f"Scan {host} {SIGNATURE}")

async def scan200_cmd(update,context):
    await scan_cmd(update,context)
async def bl_cmd(update,context):
    await update.message.reply_text("🛡️ /bl ip")
async def mtr_cmd(update,context):
    await update.message.reply_text("📡 /mtr ip")
async def exact_cmd(update,context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("🎯 /exact Team vs Team")
        return
    pred = predict_exact_score(" ".join(context.args))
    await update.message.reply_text(f"{pred} {SIGNATURE}")
async def today_cmd(update,context):
    await exact_cmd(update,context)
async def owner_cmd(update,context):
    await update.message.reply_text(f"{SIGNATURE}")

async def handle_dark_tunnel(update, context):
    await update.message.reply_text(f"Fichier recu {SIGNATURE}")

async def handle_download(update,context,audio_only=False):
    await update.message.reply_text("Lien recu")

async def handle_photo(update,context):
    save_user(update.effective_user.id)
    cap = update.message.caption or "C est quel modele? Donne le modele exact du telephone sur la photo. Reponds en francais."
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    try:
        pf = await update.message.photo[-1].get_file()
        fp = "/tmp/analyse.jpg"
        await pf.download_to_drive(fp)
        with open(fp,"rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        if groq_client:
            try:
                comp = groq_client.chat.completions.create(
                    model="llama-3.2-11b-vision-preview",
                    messages=[{"role":"user","content":[{"type":"text","text":cap},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],
                    temperature=0.3,
                    max_tokens=600)
                rep = comp.choices[0].message.content
                await update.message.reply_text(f"ANALYSE:\n\n{rep}\n\n{SIGNATURE}")
                return
            except Exception as e:
                print(f"11b fail {e}, trying 90b")
                comp = groq_client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=[{"role":"user","content":[{"type":"text","text":cap},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],
                    temperature=0.3,
                    max_tokens=600)
                rep = comp.choices[0].message.content
                await update.message.reply_text(f"ANALYSE:\n\n{rep}\n\n{SIGNATURE}")
                return
    except Exception as e:
        await update.message.reply_text(f"Erreur vision: {str(e)[:800]}\n{SIGNATURE}")

async def mp3_cmd(update,context):
    await handle_download(update,context,True)

async def chat_gpt(update,context):
    save_user(update.effective_user.id)
    txt = update.message.text or ""
    if is_link(txt):
        await handle_download(update,context,False)
        return
    try:
        comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":f"Tu es {SIGNATURE}."},{"role":"user","content":txt}],temperature=0.7)
        rep = comp.choices[0].message.content
    except:
        rep = f"Bien recu: {txt}"
    await update.message.reply_text(f"{rep} {SIGNATURE}")

def main():
    print("Building V27 FINAL...")
    app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("vmess", vmess_cmd))
    app.add_handler(CommandHandler("v2ray", vmess_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("trace", scan_cmd))
    app.add_handler(CommandHandler("scan200", scan200_cmd))
    app.add_handler(CommandHandler("bl", bl_cmd))
    app.add_handler(CommandHandler("blacklist", bl_cmd))
    app.add_handler(CommandHandler("mtr", mtr_cmd))
    app.add_handler(CommandHandler("pdf", pdf_cmd))
    app.add_handler(CommandHandler("mp3", mp3_cmd))
    app.add_handler(CommandHandler("exact", exact_cmd))
    app.add_handler(CommandHandler("today", today_cmd))
    app.add_handler(CommandHandler("tous", today_cmd))
    app.add_handler(CommandHandler("owner", owner_cmd))
    app.add_handler(CommandHandler("audit", owner_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_dark_tunnel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
    print("V27 GO...")
    app.run_polling()

if __name__ == "__main__":
    main()
