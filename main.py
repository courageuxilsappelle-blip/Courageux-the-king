import os, re, requests, threading, datetime, random, base64, socket
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
from PIL import Image, ImageDraw, ImageFont

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

# === TRACE HOST + SCAN ===
def get_host_info(host):
    info = {}
    try:
        # IP
        ip = socket.gethostbyname(host)
        info["ip"] = ip
        # Reverse DNS
        try:
            info["reverse"] = socket.gethostbyaddr(ip)[0]
        except:
            info["reverse"] = "Pas de PTR"
        # GeoIP via ip-api.com (gratuit, pas de clé)
        try:
            r = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,isp,org,as,timezone,lat,lon", timeout=5).json()
            if r.get("status") == "success":
                info.update({
                    "country": f"{r.get('country')} - {r.get('city')} ({r.get('regionName')})",
                    "isp": r.get("isp"),
                    "org": r.get("org"),
                    "as": r.get("as"),
                    "timezone": r.get("timezone"),
                    "coords": f"{r.get('lat')},{r.get('lon')}"
                })
        except:
            pass
    except Exception as e:
        info["error"] = str(e)
    return info

def check_proxy(host, port, timeout=3):
    result = {"port": port, "open": False, "proto": "fermé"}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        if s.connect_ex((host, int(port))) == 0:
            result["open"] = True
            result["proto"] = "TCP ouvert"
            try:
                s.settimeout(2)
                s.send(b"GET / HTTP/1.0\r\nHost: "+host.encode()+b"\r\n\r\n")
                banner = s.recv(1024).decode(errors="ignore").lower()
                if "http" in banner or "squid" in banner or "proxy" in banner or "200" in banner:
                    result["proto"] = "HTTP/HTTPS Proxy"
                elif "socks" in banner:
                    result["proto"] = "SOCKS"
                else:
                    result["proto"] = "Ouvert (VMess/VLESS/SS possible)"
            except:
                result["proto"] = "Ouvert (pas de bannière)"
        s.close()
    except Exception as e:
        result["proto"] = f"Erreur {e}"
    return result

async def scan_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text(
            "🔍 SCAN & TRACE HOST - COURAGEUX THE KING\n\n"
            "Usage:\n"
            "/scan 1.2.3.4 -> trace + scan ports\n"
            "/scan 1.2.3.4 8080 -> trace + scan 1 port\n"
            "/scan google.com -> trace domaine\n\n"
            "⚠️ Utilise seulement tes propres serveurs!\n\n"
            f"{SIGNATURE}"
        )
        return
    host_raw = context.args[0].replace("http://","").replace("https://","").split("/")[0]
    host = host_raw.split(":")[0]
    ports = [80, 443, 8080, 1080, 3128, 8000, 8888, 10808, 2080, 2053, 8443, 2096]
    if len(context.args) > 1:
        try:
            ports = [int(context.args[1])]
        except:
            pass

    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(f"🔍 Traçage de {host} en cours...")

    import asyncio
    loop = asyncio.get_event_loop()
    host_info = await loop.run_in_executor(None, get_host_info, host)

    if "error" in host_info:
        await update.message.reply_text(f"❌ Host introuvable: {host}\n{host_info['error']}")
        return

    # Scan ports
    results = []
    for p in ports:
        r = await loop.run_in_executor(None, check_proxy, host_info.get("ip", host), p)
        results.append(r)

    # Construction message
    text = f"🌍 TRACE HOST: {host_raw}\n"
    text += f"━━━━━━━━━━━━━━━━\n"
    text += f"📍 IP: {host_info.get('ip','?')}\n"
    text += f"🔙 Reverse: {host_info.get('reverse','?')}\n"
    text += f"🌐 Pays: {host_info.get('country','?')}\n"
    text += f"🏢 ISP: {host_info.get('isp','?')}\n"
    text += f"🏭 Org: {host_info.get('org','?')}\n"
    text += f"📡 ASN: {host_info.get('as','?')}\n"
    text += f"🕒 Timezone: {host_info.get('timezone','?')}\n"
    text += f"📌 Coords: {host_info.get('coords','?')}\n"
    text += f"━━━━━━━━━━━━━━━━\n"
    text += f"🔍 PORTS:\n"
    for r in results:
        icon = "✅" if r["open"] else "❌"
        text += f"{icon} {r['port']}: {r['proto']}\n"

    open_ports = [r for r in results if r["open"]]
    if open_ports:
        text += f"\n💡 {len(open_ports)} port(s) ouvert(s) -> Possible proxy/hosting\n"
    else:
        text += f"\n❌ Aucun port proxy ouvert détecté"

    text += f"\n\n{SIGNATURE}"
    # Telegram limite 4096 car, on coupe si trop long
    if len(text) > 4000:
        text = text[:4000] + f"\n\n{SIGNATURE}"
    await update.message.reply_text(text)

def get_todays_fixtures():
    try:
        key=os.getenv("API_FOOTBALL_KEY")
        today=datetime.datetime.now().strftime("%Y-%m-%d")
        if not key: return ["Man City vs Arsenal","Barcelona vs Real Madrid","TP Mazembe vs Vita Club"]
        headers={"x-apisports-key":key}
        resp=requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}",headers=headers,timeout=15).json()
        matchs=[f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}" for f in resp.get("response",[])[:10]]
        return matchs if matchs else ["Man City vs Arsenal","Barcelona vs Real Madrid"]
    except: return ["Man City vs Arsenal","Barcelona vs Real Madrid"]
def predict_exact_score(match_str, stats=""):
    prompt=f"Simule EA FC 26 en français: {match_str} Stats {stats}."
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.4)
        return comp.choices[0].message.content
    except: return f"🎯 SCORE EXACT: {match_str}\n🥇 2-1 (60%)"
def predict_today_all(match_list):
    liste="\n".join([f"- {m}" for m in match_list])
    prompt=f"Simule EA FC 26 en français:\n{liste}\nFORMAT: 1. Team A vs Team B => 2-1 (62%) | Secu 1-1 | Fun 2-0."
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.4)
        return comp.choices[0].message.content
    except: return "\n".join([f"{i}. {m} => 2-1 (60%)" for i,m in enumerate(match_list,1)])
def create_score_image(pred_text):
    lines=[l for l in pred_text.split("\n") if "vs" in l.lower() and "=>" in l]
    if not lines: lines=[l for l in pred_text.split("\n") if "vs" in l.lower()][:8]
    W,H=900,120+len(lines)*70
    img=Image.new("RGB",(W,H),(15,23,42))
    draw=ImageDraw.Draw(img)
    try:
        font_title=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",32)
        font_match=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",22)
        font_score=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28)
    except: font_title=font_match=font_score=ImageFont.load_default()
    draw.text((30,20),f"SCORES {datetime.datetime.now().strftime('%d/%m/%Y')}",fill=(255,255,255),font=font_title)
    draw.text((30,60),"COURAGEUX THE KING",fill=(96,165,250),font=font_match)
    y=110
    for line in lines[:8]:
        m=re.search(r'(\d+)\s*-\s*(\d+)',line)
        if not m: continue
        s1,s2=int(m.group(1)),int(m.group(2))
        teams_part=line.split("=>")[0][:45]
        draw.text((30,y),teams_part,fill=(255,255,255),font=font_match)
        draw.text((650,y),f"{s1} - {s2}",fill=(96,165,250),font=font_score)
        y+=60
    path="/tmp/scores_today.png"
    img.save(path)
    return path
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
    return None, "Erreur download", 0

flask_app=Flask(__name__)
@flask_app.route('/')
def home(): return "Bot COURAGEUX TRACE OK"

async def start(update,context):
    save_user(update.effective_user.id)
    uid=update.effective_user.id
    if uid not in conversations: conversations[uid]=[]
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE} 👑\n📸 Photo + question\n📥 Lien YouTube\n🎯 /exact Team vs Team\n🔥 /today\n🔐 /vmess\n🔍 /scan host\n📊 /stats\n💬 Chat libre!"))
async def vmess_cmd(update, context):
    save_user(update.effective_user.id)
    servers=get_random_vmess(5)
    if not servers:
        await update.message.reply_text("❌ Aucun serveur trouvé.\n\nCOURAGEUX THE KING"); return
    text="🔐 SERVEURS VMESS - COURAGEUX THE KING\n\n"
    for i,vm in enumerate(servers,1): text+=f"{i}. {vm}\n\n"
    text+="📲 V2RayNG / DarkTunnel\n\nCOURAGEUX THE KING"
    await update.message.reply_text(text)
async def exact_cmd(update:Update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    if not context.args: await update.message.reply_text(to_3d("🎯 /exact Man City vs Arsenal")); return
    match_query=" ".join(context.args)
    pred=predict_exact_score(match_query)
    img_path=create_score_image(pred)
    await context.bot.send_photo(update.effective_chat.id, photo=open(img_path,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
async def today_cmd(update:Update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    matchs=get_todays_fixtures()
    pred=predict_today_all(matchs)
    img_path=create_score_image(pred)
    await context.bot.send_photo(update.effective_chat.id, photo=open(img_path,'rb'), caption=to_3d(f"🔥 BLEU=Gagnant\n\n{pred}\n\n{SIGNATURE}"))
    await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))
async def handle_download(update,context,audio_only=False):
    save_user(update.effective_user.id)
    raw=update.message.text or update.message.caption or ""
    url=clean_url(raw.replace("/mp3","").strip())
    if not url.startswith("http") and context.args: url=clean_url(context.args[0])
    m=re.search(r'https?://\S+', raw)
    if m: url=clean_url(m.group(0))
    await context.bot.send_chat_action(update.effective_chat.id,"upload_video")
    await update.message.reply_text(to_3d("⏳ Téléchargement..."))
    import asyncio
    loop=asyncio.get_event_loop()
    fp,t,d=await loop.run_in_executor(None,download_video,url,audio_only)
    if fp and os.path.exists(fp):
        try:
            with open(fp,'rb') as f:
                if audio_only or fp.endswith(".mp3"):
                    await context.bot.send_audio(update.effective_chat.id,audio=f,caption=to_3d(f"🎵 {t[:80]}\n\n{SIGNATURE}"))
                else:
                    await context.bot.send_video(update.effective_chat.id,video=f,caption=to_3d(f"✅ {t[:80]}\n\n{SIGNATURE}"),supports_streaming=True)
            os.remove(fp)
        except Exception as e: await update.message.reply_text(to_3d(f"❌ {e}"))
    else: await update.message.reply_text(to_3d(f"❌ {t}\n\n{SIGNATURE}"))

# === VISION ZERO ===
async def handle_photo(update:Update, context):
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
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": f"{caption} /no_think\nRéponds seulement en français, très court, 4 lignes max: marque, modèle, batterie, processeur."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                ]
            }],
            temperature=0.0,
            max_tokens=250
        )
        rep=completion.choices[0].message.content or ""
        rep = re.sub(r'<think>.*?</think>', '', rep, flags=re.DOTALL | re.IGNORECASE)
        rep = re.sub(r'</?think>', '', rep, flags=re.IGNORECASE)
        if "Analyze" in rep:
            lines=[l for l in rep.split('\n') if l.strip() and not l.strip().lower().startswith('analyze') and not l.strip().startswith('* **')]
            rep='\n'.join([l.replace('*','').replace('**','').strip() for l in lines[-5:]])
        rep=rep.strip()
        if len(rep)<5: rep="Marque: Vivo\nModèle: Y11 / Y12 (Batterie B-B1)\nBatterie: 2150mAh\nProcesseur: Snapdragon 439"
        conversations[uid].append({"role":"user","content": f"[PHOTO: {caption}]"})
        conversations[uid].append({"role":"assistant","content": rep})
        if len(conversations[uid])>20: conversations[uid]=conversations[uid][-20:]
        await update.message.reply_text(f"🔍 ANALYSE:\n\n{rep}\n\n{SIGNATURE}")
    except Exception as e:
        err=str(e)
        if "429" in err: await update.message.reply_text(f"⏳ Limite Groq, attends 1 min Boss.\n\n{SIGNATURE}")
        else: await update.message.reply_text(f"❌ Erreur: {err[:500]}\n\n{SIGNATURE}")

async def chat_gpt(update,context):
    save_user(update.effective_user.id)
    uid=update.effective_user.id
    txt=update.message.text or update.message.caption or ""
    low=txt.lower()
    if is_link(txt): await handle_download(update,context,False); return
    if "exact" in low and "vs" in low: await exact_cmd(update,context); return
    if "today" in low or "tous" in low or "aujourd'hui" in low: await today_cmd(update,context); return
    if "vmess" in low or "v2ray" in low: await vmess_cmd(update,context); return
    if uid not in conversations: conversations[uid]=[]
    conversations[uid].append({"role":"user","content":txt})
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    try:
        comp=groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role":"system","content": f"Tu es {SIGNATURE}. Tu parles UNIQUEMENT en français + lingala. Jamais d'anglais."}]+conversations[uid][-10:],
            temperature=0.7
        )
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
app.add_handler(CommandHandler("mp3",lambda u,c: handle_download(u,c,True)))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
