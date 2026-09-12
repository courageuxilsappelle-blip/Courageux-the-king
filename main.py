import os, re, requests, threading, datetime, random, base64, socket, time, asyncio
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PIL import Image
import urllib3
urllib3.disable_warnings()

print("=== COURAGEUX THE KING STARTING ===")
TOKEN = os.getenv("TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
print(f"TOKEN exists: {bool(TOKEN)} | GROQ exists: {bool(GROQ_KEY)}")

if not TOKEN:
    print("❌ ERREUR FATALE: TOKEN manquant!")
    time.sleep(1000)

groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
conversations = {}
SIGNATURE = "COURAGEUX THE KING"

# --- FLASK POUR RENDER ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"Bot {SIGNATURE} LIVE - {datetime.datetime.now()}"

def run_flask():
    port = int(os.getenv("PORT", 10000))
    print(f"Starting Flask on port {port}")
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()
time.sleep(2) # Laisse Flask démarrer pour Render
print("Flask thread lancé")

# --- FONCTIONS ---
USERS_FILE = "users.txt"
def save_user(uid):
    try:
        if not os.path.exists(USERS_FILE): open(USERS_FILE,"w").close()
        with open(USERS_FILE,"r") as f: data=f.read()
        if str(uid) not in data:
            with open(USERS_FILE,"a") as f: f.write(f"{uid}\n")
    except: pass

def get_total_users():
    try:
        if not os.path.exists(USERS_FILE): return 0
        with open(USERS_FILE,"r") as f: return len([l for l in f if l.strip()])
    except: return 0

def to_3d(t):
    try:
        normal="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        bold3d="𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
        return "".join([bold3d[normal.index(c)] if c in normal else c for c in t])
    except: return t

def clean_url(u): return u.strip().split('?is=')[0].split('&is=')[0].split('?si=')[0]
def get_yt_id(u):
    m=re.search(r'(?:v=|be/|shorts/|embed/)([A-Za-z0-9_-]{11})',u)
    return m.group(1) if m else None
def is_link(t): return any(x in t.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com","fb.watch","facebook.com"])

def get_host_info(host):
    info={}
    try:
        ip=socket.gethostbyname(host)
        info["ip"]=ip
        try: info["reverse"]=socket.gethostbyaddr(ip)[0]
        except: info["reverse"]="Pas de PTR"
        try:
            r=requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,as", timeout=5).json()
            if r.get("status")=="success":
                info.update({"country":f"{r.get('country')} - {r.get('city')}", "isp":r.get("isp"), "org":r.get("org")})
        except: pass
    except Exception as e: info["error"]=str(e)
    return info

def check_port_200(host, ip, port):
    result={"port":port,"open":False,"status":"FERMÉ","is_200":False,"code":0}
    try:
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        if s.connect_ex((ip, int(port)))!=0:
            s.close(); return result
        s.close(); result["open"]=True
    except: return result
    try:
        urls=[f"http://{host}:{port}", f"https://{host}:{port}"] if port!=443 else [f"https://{host}:{port}", f"http://{host}:{port}"]
        for u in urls:
            try:
                r=requests.get(u, timeout=4, verify=False, headers={"User-Agent":"Mozilla/5.0"})
                result["code"]=r.status_code
                if r.status_code==200:
                    result["status"]="✅ 200 OK - VIVANT"; result["is_200"]=True
                elif r.status_code in [301,302,403,401]:
                    result["status"]=f"🔀 {r.status_code} - VIVANT"; result["is_200"]=True
                else:
                    result["status"]=f"📄 {r.status_code}"; result["is_200"]=r.status_code<500
                break
            except: continue
        if result["code"]==0 and result["open"]: result["status"]="🟢 OUVERT TCP"
    except: result["status"]="🟢 OUVERT"
    return result

async def scan_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("🔍 /scan host"); return
    host=context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    await update.message.reply_text(f"🔍 Scan {host}...")
    loop=asyncio.get_event_loop()
    host_info=await loop.run_in_executor(None, get_host_info, host)
    ip=host_info.get("ip",host)
    txt=f"🌍 TRACE: {host}\nIP: {ip}\n"
    for p in [80,443,8080,1080,3128,8000,8888]:
        r=await loop.run_in_executor(None, check_port_200, host, ip, p)
        if r["is_200"]: txt+=f"✅ {r['port']}: {r['status']} code {r['code']}\n"
        elif r["open"]: txt+=f"🟡 {r['port']}: {r['status']}\n"
        else: txt+=f"❌ {r['port']}: FERMÉ\n"
    txt+=f"\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def scan200_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args: await update.message.reply_text("Usage: /scan200 host"); return
    host=context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    loop=asyncio.get_event_loop()
    host_info=await loop.run_in_executor(None, get_host_info, host)
    ip=host_info.get("ip",host)
    await update.message.reply_text(f"🎯 Scan 200 OK {host}...")
    found=[]
    for p in [80,443,8080,1080,3128]:
        r=await loop.run_in_executor(None, check_port_200, host, ip, p)
        if r["is_200"]: found.append(r)
    if found:
        txt=f"🎯 200 OK: {host} ({ip})\n"
        for r in found: txt+=f"✅ {r['port']}: code {r['code']} VIVANT\n"
        txt+=f"\n{SIGNATURE}"
    else:
        txt=f"❌ Aucun 200 OK sur {host}\n\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def mtr_cmd(update, context):
    save_user(update.effective_user.id)
    print(f"MTR called with: {context.args}")
    if not context.args:
        await update.message.reply_text("📡 SCAN MTR\n/mtr 8.8.8.8 1.1.1.1\n\nColle les IP de ton MTR\n\nCOURAGEUX THE KING")
        return
    raw=" ".join(context.args)
    ips=re.findall(r'\b\d+\.\d+\.\d+\.\d+\b', raw)
    ips=list(dict.fromkeys(ips))
    if not ips: await update.message.reply_text("❌ Aucune IP"); return
    loop=asyncio.get_event_loop()
    await update.message.reply_text(f"🔍 Scan {len(ips)} HOSTS MTR...")
    txt=f"🌍 SCAN MTR {len(ips)} HOSTS\n"
    found=[]
    for ip in ips[:15]:
        r80=await loop.run_in_executor(None, check_port_200, ip, ip, 80)
        r443=await loop.run_in_executor(None, check_port_200, ip, ip, 443)
        if r80["is_200"] or r443["is_200"]:
            found.append(ip)
            txt+=f"✅ {ip}: 200 OK VIVANT!\n"
        elif r80["open"] or r443["open"]:
            txt+=f"🟡 {ip}: Ouvert\n"
        else:
            txt+=f"❌ {ip}: Fermé\n"
    if found:
        txt+=f"\n🎯 {len(found)} AVEC 200 OK:\n"
        for ip in found: txt+=f"👉 {ip}:80\n"
    txt+=f"\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def start(update, context):
    save_user(update.effective_user.id)
    msg = (
        f"Je suis {SIGNATURE} 👑\n"
        "📸 Photo + question\n"
        "📥 Lien YouTube\n"
        "🎯 /exact Team vs Team\n"
        "🔥 /today\n"
        "🔐 /vmess\n"
        "🔍 /scan host\n"
        "🎯 /scan200 host\n"
        "📡 /mtr ip1 ip2\n"
        "📊 /stats"
    )
    await update.message.reply_text(to_3d(msg))

async def stats_cmd(update, context):
    save_user(update.effective_user.id)
    await update.message.reply_text(f"📊 Total: {get_total_users()}\n\n{SIGNATURE}")

async def vmess_cmd(update, context):
    await update.message.reply_text("🔐 VMESS - En cours\n\nCOURAGEUX THE KING")

async def exact_cmd(update, context):
    await update.message.reply_text("🎯 /exact - En cours")

async def today_cmd(update, context):
    await update.message.reply_text("🔥 /today - En cours")

async def handle_photo(update, context):
    save_user(update.effective_user.id)
    await update.message.reply_text("📸 Photo reçue - Vision en cours...")
    try:
        photo_file=await update.message.photo[-1].get_file()
        file_path="/tmp/analyse.jpg"
        await photo_file.download_to_drive(file_path)
        with open(file_path, "rb") as f:
            b64=base64.b64encode(f.read()).decode('utf-8')
        if groq_client:
            completion=groq_client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=[{"role":"user","content":[{"type":"text","text":"C'est quel modèle? Réponds français 4 lignes: marque modèle batterie processeur /no_think"},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],
                temperature=0.0, max_tokens=300)
            rep=completion.choices[0].message.content
            rep=re.sub(r'<think>.*?</think>','',rep,flags=re.DOTALL)
            await update.message.reply_text(f"🔍 {rep}\n\n{SIGNATURE}")
        else:
            await update.message.reply_text("❌ GROQ_API_KEY manquant")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {e}")

async def chat_gpt(update, context):
    txt=update.message.text or ""
    if is_link(txt):
        await update.message.reply_text("📥 Lien reçu - Download en cours...")
        return
    await update.message.reply_text(to_3d(f"Yo Boss! Tape /start\n\n{SIGNATURE}"))

# --- LANCEMENT BOT ---
def main():
    print("Building Telegram App...")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("trace", scan_cmd))
    app.add_handler(CommandHandler("scan200", scan200_cmd))
    app.add_handler(CommandHandler("mtr", mtr_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("vmess", vmess_cmd))
    app.add_handler(CommandHandler("exact", exact_cmd))
    app.add_handler(CommandHandler("today", today_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
    print("✅ Bot handlers ajoutés - Polling...")
    app.run_polling(drop_pending_updates=True, allowed_updates=["message"])

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ BOT CRASH: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(5)
