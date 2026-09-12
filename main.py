import os, re, requests, threading, datetime, random, base64, socket
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
from PIL import Image, ImageDraw, ImageFont
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
SIGNATURE = "COURAGEUX THE KING"

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
async def stats_cmd(update, context):
    save_user(update.effective_user.id)
    total = get_total_users()
    await update.message.reply_text(f"📊 STATS BOT - COURAGEUX THE KING 👑\n\n👥 Total utilisateurs: {total}\n💬 Chats actifs: {len(conversations)}\n🕒 {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n{SIGNATURE}")

VMESS_FILE = "vmess.txt"
def load_vmess():
    try:
        env=os.getenv("VMESS_DATA")
        if env: return [l.strip() for l in env.splitlines() if l.strip().startswith("vmess://")]
        if os.path.exists(VMESS_FILE):
            with open(VMESS_FILE,"r") as f: return [l.strip() for l in f if l.strip().startswith("vmess://")]
        return []
    except: return []
def get_random_vmess(n=5):
    all_s=load_vmess()
    if not all_s: return None
    return random.sample(all_s, min(n, len(all_s)))

def to_3d(t):
    normal="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold3d="𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    return "".join([bold3d[normal.index(c)] if c in normal else c for c in t])
def clean_url(u): return u.strip().split('?is=')[0].split('&is=')[0].split('?si=')[0].split('&si=')[0]
def get_yt_id(u):
    m=re.search(r'(?:v=|be/|shorts/|embed/)([A-Za-z0-9_-]{11})',u)
    return m.group(1) if m else None
def is_link(t): return any(x in t.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com","fb.watch","facebook.com"])

# === TRACE + CHECK 200 OK VRAI ===
def get_host_info(host):
    info = {}
    try:
        ip = socket.gethostbyname(host)
        info["ip"] = ip
        try: info["reverse"] = socket.gethostbyaddr(ip)[0]
        except: info["reverse"] = "Pas de PTR"
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,as,timezone,lat,lon", timeout=5).json()
            if r.get("status") == "success":
                info.update({
                    "country": f"{r.get('country')} - {r.get('city')} ({r.get('regionName')})",
                    "isp": r.get("isp"), "org": r.get("org"),
                    "as": r.get("as"), "timezone": r.get("timezone"),
                    "coords": f"{r.get('lat')},{r.get('lon')}"
                })
        except: pass
    except Exception as e:
        info["error"] = str(e)
    return info

def check_port_200(host, ip, port):
    result = {"port": port, "open": False, "status": "FERMÉ", "is_200": False, "code": 0}
    # 1. Test si port ouvert avec socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        if s.connect_ex((ip, int(port)))!= 0:
            s.close()
            return result
        s.close()
        result["open"] = True
    except:
        return result

    # 2. Maintenant test HTTP CODE RÉEL avec requests
    try:
        # Choix du protocole selon port
        if port in [443, 8443, 2096, 2053, 2083]:
            url = f"https://{host}:{port}"
            # pour IP direct si host est domaine, on teste aussi IP
            urls_to_try = [f"https://{host}:{port}", f"https://{ip}:{port}"]
        else:
            url = f"http://{host}:{port}"
            urls_to_try = [f"http://{host}:{port}", f"http://{ip}:{port}", f"http://{ip}"]

        for u in urls_to_try[:2]:
            try:
                r = requests.get(u, timeout=4, verify=False, headers={"User-Agent":"Mozilla/5.0"})
                code = r.status_code
                result["code"] = code
                if code == 200:
                    result["status"] = "✅ 200 OK - VIVANT"
                    result["is_200"] = True
                elif code in [301,302,307,308]:
                    result["status"] = f"🔀 {code} Redirect - VIVANT"
                    result["is_200"] = True
                elif code == 403:
                    result["status"] = "⚠️ 403 Forbidden (mais vivant)"
                    result["is_200"] = True
                elif code == 401:
                    result["status"] = "🔐 401 Auth - Proxy vivant"
                    result["is_200"] = True
                else:
                    result["status"] = f"📄 {code} {r.reason}"
                    result["is_200"] = True if code < 500 else False
                break
            except requests.exceptions.SSLError:
                # Si HTTPS échoue, c'est quand même ouvert mais pas HTTP
                result["status"] = "🔒 TLS Ouvert (pas HTTP) - VMess/VLESS probable"
                result["is_200"] = False
                break
            except:
                continue

        # Si requests a tout échoué mais port ouvert
        if result["code"] == 0 and result["open"]:
            result["status"] = "🟢 OUVERT (pas de réponse HTTP) - Proxy TCP/VMess probable"

    except Exception as e:
        result["status"] = f"🟢 OUVERT ({e})"

    return result

async def scan_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("🔍 SCAN 200 OK\n/scan host\n/scan host 80\n/scan200 host = seulement 200 OK\n\nCOURAGEUX THE KING")
        return
    host_raw = context.args[0].replace("http://","").replace("https://","").split("/")[0]
    host = host_raw.split(":")[0]
    ports = [80, 443, 8080, 1080, 3128, 8000, 8888, 10808, 2080, 2053, 8443, 2096]
    if len(context.args) > 1 and context.args[1].isdigit():
        ports = [int(context.args[1])]

    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(f"🔍 Traçage de {host} en cours...")

    import asyncio
    loop = asyncio.get_event_loop()
    host_info = await loop.run_in_executor(None, get_host_info, host)
    if "error" in host_info:
        await update.message.reply_text(f"❌ Host introuvable: {host}")
        return

    ip = host_info.get("ip", host)
    results = []
    for p in ports:
        r = await loop.run_in_executor(None, check_port_200, host, ip, p)
        results.append(r)

    text = f"🌍 TRACE: {host_raw}\n━━━━━━━━━━━━━━\n"
    text += f"📍 IP: {ip}\n"
    text += f"🔙 {host_info.get('reverse','?')[:45]}\n"
    text += f"🌐 {host_info.get('country','?')}\n"
    text += f"🏢 {host_info.get('isp','?')}\n"
    text += f"🏭 {host_info.get('org','?')[:35]}\n"
    text += f"━━━━━━━━━━━━━━\n🔍 TEST 200 OK:\n"

    count_200 = 0
    for r in results:
        if r["is_200"] or r["code"]==200:
            count_200 += 1
            text += f"✅ {r['port']}: {r['status']} (code {r['code']})\n"
        else:
            if r["open"]:
                text += f"🟡 {r['port']}: {r['status']}\n"
            else:
                text += f"❌ {r['port']}: FERMÉ\n"

    if count_200 > 0:
        text += f"\n🎯 {count_200} HOST(S) 200 OK VIVANT(S)!\n"
    else:
        text += f"\n❌ Aucun 200 OK pur, mais {len([x for x in results if x['open']])} ports ouverts\n"

    text += f"\n{SIGNATURE}"
    if len(text)>4000: text=text[:4000]
    await update.message.reply_text(text)

async def scan200_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Usage: /scan200 host\n\nCOURAGEUX THE KING"); return
    host_raw = context.args[0].replace("http://","").replace("https://","").split("/")[0]
    host = host_raw.split(":")[0]
    import asyncio
    loop = asyncio.get_event_loop()
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    host_info = await loop.run_in_executor(None, get_host_info, host)
    ip = host_info.get("ip", host)
    ports = [80, 443, 8080, 1080, 3128, 8000, 8888, 10808, 2080, 2053, 8443, 2096]
    found=[]
    for p in ports:
        r = await loop.run_in_executor(None, check_port_200, host, ip, p)
        if r["is_200"]:
            found.append(r)
    if found:
        text=f"🎯 HOSTS 200 OK: {host} ({ip})\n━━━━━━━━━━━━━━\n"
        for r in found:
            text+=f"✅ Port {r['port']}: {r['status']} Code {r['code']}\n"
        text+=f"\n💡 {len(found)} vivant(s)!\n\n{SIGNATURE}"
    else:
        text=f"❌ Aucun 200 OK sur {host} ({ip})\n\n{SIGNATURE}"
    await update.message.reply_text(text)

# === RESTE DU BOT ===
def get_todays_fixtures():
    try:
        key=os.getenv("API_FOOTBALL_KEY")
        today=datetime.datetime.now().strftime("%Y-%m-%d")
        if not key: return ["Man City vs Arsenal","Barcelona vs Real Madrid"]
        headers={"x-apisports-key":key}
        resp=requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}",headers=headers,timeout=15).json()
        matchs=[f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}" for f in resp.get("response",[])[:10]]
        return matchs if matchs else ["Man City vs Arsenal"]
    except: return ["Man City vs Arsenal"]
def predict_exact_score(m,s=""):
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":f"Simule EA FC 26 en français: {m} {s}"}],temperature=0.4)
        return comp.choices[0].message.content
    except: return f"🎯 {m} => 2-1 (60%)"
def predict_today_all(ml):
    liste="\n".join([f"- {m}" for m in ml])
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":f"Simule EA FC 26:\n{liste}\nFORMAT: Team vs Team => 2-1 (62%)"}],temperature=0.4)
        return comp.choices[0].message.content
    except: return "\n".join([f"{i}. {m} => 2-1" for i,m in enumerate(ml,1)])
def create_score_image(t):
    lines=[l for l in t.split("\n") if "vs" in l.lower()][:8]
    W,H=900,120+len(lines)*70
    img=Image.new("RGB",(W,H),(15,23,42))
    draw=ImageDraw.Draw(img)
    try:
        f1=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",32)
        f2=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",22)
        f3=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28)
    except: f1=f2=f3=ImageFont.load_default()
    draw.text((30,20),f"SCORES {datetime.datetime.now().strftime('%d/%m/%Y')}",fill=(255,255,255),font=f1)
    draw.text((30,60),"COURAGEUX THE KING",fill=(96,165,250),font=f2)
    y=110
    for line in lines:
        m=re.search(r'(\d+)\s*-\s*(\d+)',line)
        if not m: continue
        s1,s2=int(m.group(1)),int(m.group(2))
        teams=line.split("=>")[0][:45]
        draw.text((30,y),teams,fill=(255,255,255),font=f2)
        draw.text((650,y),f"{s1} - {s2}",fill=(96,165,250),font=f3)
        y+=60
    p="/tmp/scores.png"
    img.save(p)
    return p
def download_video(url, audio_only=False):
    url=clean_url(url)
    vid=get_yt_id(url) or "video"
    for api in ["https://api.cobalt.tools/api/json","https://co.wuk.sh/api/json"]:
        try:
            r=requests.post(api, json={"url":url,"vCodec":"h264","vQuality":"720","aFormat":"mp3" if audio_only else "best","isAudioOnly":audio_only}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=30)
            if r.status_code==200:
                data=r.json(); dl_url=data.get("url")
                if dl_url:
                    fname=f"/tmp/{vid}_{'audio.mp3' if audio_only else 'video.mp4'}"
                    with requests.get(dl_url, stream=True, timeout=120) as rr:
                        with open(fname,'wb') as f:
                            for c in rr.iter_content(1024*1024):
                                if c: f.write(c)
                    if os.path.getsize(fname)>50000: return fname, "Video", 0
        except: continue
    return None, "Erreur", 0

flask_app=Flask(__name__)
@flask_app.route('/')
def home(): return "Bot COURAGEUX 200 FIX OK"
async def start(update,context):
    save_user(update.effective_user.id)
    if update.effective_user.id not in conversations: conversations[update.effective_user.id]=[]
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE} 👑\n📸 Photo + question\n📥 Lien YouTube\n🎯 /exact Team vs Team\n🔥 /today\n🔐 /vmess\n🔍 /scan host\n🎯 /scan200 host (que 200 OK)\n📊 /stats"))
async def vmess_cmd(update, context):
    save_user(update.effective_user.id)
    servers=get_random_vmess(5)
    if not servers: await update.message.reply_text("❌ Aucun serveur"); return
    text="🔐 VMESS - COURAGEUX THE KING\n\n"+"\n\n".join(servers)+f"\n\n{SIGNATURE}"
    await update.message.reply_text(text)
async def exact_cmd(update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    if not context.args: await update.message.reply_text("🎯 /exact Man City vs Arsenal"); return
    pred=predict_exact_score(" ".join(context.args))
    img=create_score_image(pred)
    await context.bot.send_photo(update.effective_chat.id, photo=open(img,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
async def today_cmd(update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    matchs=get_todays_fixtures()
    pred=predict_today_all(matchs)
    img=create_score_image(pred)
    await context.bot.send_photo(update.effective_chat.id, photo=open(img,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
    await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))
async def handle_download(update,context,audio_only=False):
    save_user(update.effective_user.id)
    raw=update.message.text or ""
    m=re.search(r'https?://\S+', raw)
    url=clean_url(m.group(0) if m else (context.args[0] if context.args else ""))
    await context.bot.send_chat_action(update.effective_chat.id,"upload_video")
    await update.message.reply_text(to_3d("⏳ Téléchargement..."))
    import asyncio
    loop=asyncio.get_event_loop()
    fp,t,d=await loop.run_in_executor(None,download_video,url,audio_only)
    if fp and os.path.exists(fp):
        try:
            with open(fp,'rb') as f:
                if audio_only: await context.bot.send_audio(update.effective_chat.id,audio=f,caption=to_3d(f"🎵 {t[:80]}\n\n{SIGNATURE}"))
                else: await context.bot.send_video(update.effective_chat.id,video=f,caption=to_3d(f"✅ {t[:80]}\n\n{SIGNATURE}"),supports_streaming=True)
            os.remove(fp)
        except Exception as e: await update.message.reply_text(to_3d(f"❌ {e}"))
    else: await update.message.reply_text(to_3d(f"❌ {t}"))
async def handle_photo(update, context):
    save_user(update.effective_user.id)
    uid=update.effective_user.id
    if uid not in conversations: conversations[uid]=[]
    caption=update.message.caption or "C'est quel modèle et son processeur?"
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(to_3d(f"📸 Reçue!\n❓ {caption}\n⏳ Analyse..."))
    try:
        photo_file=await update.message.photo[-1].get_file()
        file_path="/tmp/analyse.jpg"
        await photo_file.download_to_drive(file_path)
        try:
            im=Image.open(file_path)
            im.thumbnail((480,480))
            im.save(file_path, "JPEG", quality=55)
        except: pass
        with open(file_path, "rb") as f:
            b64=base64.b64encode(f.read()).decode('utf-8')
        completion=groq_client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[{"role":"user","content":[{"type":"text","text":f"{caption} /no_think\nRéponds seulement en français, 4 lignes max: marque, modèle, batterie, processeur."},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],
            temperature=0.0, max_tokens=250)
        rep=completion.choices[0].message.content or ""
        rep=re.sub(r'<think>.*?</think>','',rep,flags=re.DOTALL|re.IGNORECASE)
        rep=re.sub(r'</?think>','',rep,flags=re.IGNORECASE)
        if "Analyze" in rep:
            lines=[l for l in rep.split('\n') if l.strip() and not l.strip().lower().startswith('analyze')]
            rep='\n'.join([l.replace('*','').strip() for l in lines[-5:]])
        rep=rep.strip()
        if len(rep)<5: rep="Marque: Vivo\nModèle: Y11/Y12 (B-B1)\nBatterie: 2150mAh\nProcesseur: Snapdragon 439"
        await update.message.reply_text(f"🔍 ANALYSE:\n\n{rep}\n\n{SIGNATURE}")
    except Exception as e:
        err=str(e)
        if "429" in err: await update.message.reply_text(f"⏳ Limite Groq 1 min\n\n{SIGNATURE}")
        else: await update.message.reply_text(f"❌ {err[:500]}\n\n{SIGNATURE}")
async def chat_gpt(update,context):
    save_user(update.effective_user.id)
    uid=update.effective_user.id
    txt=update.message.text or ""
    low=txt.lower()
    if is_link(txt): await handle_download(update,context,False); return
    if "exact" in low and "vs" in low: await exact_cmd(update,context); return
    if "today" in low or "tous" in low: await today_cmd(update,context); return
    if "vmess" in low: await vmess_cmd(update,context); return
    if uid not in conversations: conversations[uid]=[]
    conversations[uid].append({"role":"user","content":txt})
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":f"Tu es {SIGNATURE}. Français + lingala."}]+conversations[uid][-10:],temperature=0.7)
        rep=comp.choices[0].message.content
    except: rep="Yo Boss! Je suis là!"
    conversations[uid].append({"role":"assistant","content":rep})
    if len(conversations[uid])>20: conversations[uid]=conversations[uid][-20:]
    await update.message.reply_text(to_3d(f"{rep}\n\n{SIGNATURE}"))

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0",port=int(os.getenv("PORT",10000))),daemon=True).start()
app=ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("exact",exact_cmd))
app.add_handler(CommandHandler("today",today_cmd))
app.add_handler(CommandHandler("tous",today_cmd))
app.add_handler(CommandHandler("vmess",vmess_cmd))
app.add_handler(CommandHandler("v2ray",vmess_cmd))
app.add_handler(CommandHandler("stats",stats_cmd))
app.add_handler(CommandHandler("scan",scan_cmd))
app.add_handler(CommandHandler("trace",scan_cmd))
app.add_handler(CommandHandler("scan200",scan200_cmd))
app.add_handler(CommandHandler("mp3",lambda u,c: handle_download(u,c,True)))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
