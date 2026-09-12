import os, re, requests, threading, datetime, random, base64, socket, time, asyncio
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont
import urllib3
urllib3.disable_warnings()

TOKEN = os.getenv("TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
print(f"=== V23 FR ONLY TOKEN={bool(TOKEN)} GROQ={bool(GROQ_KEY)} ===")

try:
    groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
except:
    groq_client = None

conversations = {}
SIGNATURE = "COURAGEUX THE KING"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return f"Bot {SIGNATURE} V23 LIVE"
threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), use_reloader=False), daemon=True).start()
time.sleep(2)

USERS_FILE="users.txt"
def save_user(uid):
    try:
        if not os.path.exists(USERS_FILE): open(USERS_FILE,"w").close()
        with open(USERS_FILE,"r") as f: d=f.read()
        if str(uid) not in d:
            with open(USERS_FILE,"a") as f: f.write(f"{uid}\n")
    except: pass
def get_total_users():
    try:
        with open(USERS_FILE,"r") as f: return len([l for l in f if l.strip()])
    except: return 0

def to_3d(t):
    try:
        n="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        b="𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
        return "".join([b[n.index(c)] if c in n else c for c in t])
    except: return t

def clean_url(u): return u.strip().split('?is=')[0].split('&is=')[0].split('?si=')[0]
def get_yt_id(u):
    m=re.search(r'(?:v=|be/|shorts/|embed/)([A-Za-z0-9_-]{11})',u)
    return m.group(1) if m else None
def is_link(t): return any(x in t.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com","fb.watch","facebook.com"])

def load_vmess():
    try:
        env=os.getenv("VMESS_DATA")
        if env: return [l.strip() for l in env.splitlines() if l.strip().startswith("vmess://")]
        if os.path.exists("vmess.txt"):
            with open("vmess.txt","r") as f: return [l.strip() for l in f if l.strip().startswith("vmess://")]
        return []
    except: return []
def get_random_vmess(n=5):
    a=load_vmess()
    return random.sample(a, min(n,len(a))) if a else None

def get_todays_fixtures():
    try:
        key=os.getenv("API_FOOTBALL_KEY")
        today=datetime.datetime.now().strftime("%Y-%m-%d")
        if not key: return ["Man City vs Arsenal","Barcelona vs Real Madrid","PSG vs Lyon","Bayern vs Dortmund","Liverpool vs Chelsea"]
        headers={"x-apisports-key":key}
        resp=requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}",headers=headers,timeout=15).json()
        m=[f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}" for f in resp.get("response",[])[:10]]
        return m if m else ["Man City vs Arsenal","Barcelona vs Real Madrid"]
    except: return ["Man City vs Arsenal","Barcelona vs Real Madrid","PSG vs Lyon"]

def predict_exact_score(match):
    if not groq_client: return f"🎯 {match} => 2-1 (60%)"
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":f"Simule EA FC 26 en français uniquement, score exact + pourcentage + buteurs: {match}"}],temperature=0.4)
        return comp.choices[0].message.content
    except Exception as e: return f"🎯 {match} => 2-1 (60%)"

def predict_today_all(ml):
    liste="\n".join([f"- {m}" for m in ml])
    if not groq_client: return "\n".join([f"{m} => 2-1 (60%)" for m in ml])
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":f"Simule EA FC 26 aujourd'hui en français uniquement:\n{liste}\nFORMAT: Team vs Team => 2-1 (62%) Buteurs:"}],temperature=0.4)
        return comp.choices[0].message.content
    except: return "\n".join([f"{m} => 2-1 (60%)" for m in ml])

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
    draw.text((30,60),f"{SIGNATURE}",fill=(96,165,250),font=f2)
    y=110
    for line in lines:
        m=re.search(r'(\d+)\s*-\s*(\d+)',line)
        if not m: continue
        s1,s2=int(m.group(1)),int(m.group(2))
        teams=line.split("=>")[0][:45]
        draw.text((30,y),teams,fill=(255,255,255),font=f2)
        draw.text((650,y),f"{s1} - {s2}",fill=(96,165,250),font=f3)
        y+=60
    p="/tmp/scores.png"; img.save(p); return p

def download_video(url, audio_only=False):
    url=clean_url(url); vid=get_yt_id(url) or "video"
    for api in ["https://api.cobalt.tools/api/json","https://co.wuk.sh/api/json"]:
        try:
            r=requests.post(api, json={"url":url,"vCodec":"h264","vQuality":"720","aFormat":"mp3" if audio_only else "best","isAudioOnly":audio_only}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=30)
            if r.status_code==200:
                dl=r.json().get("url")
                if dl:
                    fname=f"/tmp/{vid}_{'audio.mp3' if audio_only else 'video.mp4'}"
                    with requests.get(dl, stream=True, timeout=120) as rr:
                        with open(fname,'wb') as f:
                            for c in rr.iter_content(1024*1024):
                                if c: f.write(c)
                    if os.path.getsize(fname)>50000: return fname,"Video",0
        except: continue
    return None,"Erreur",0

def get_host_info(host):
    info={}
    try:
        ip=socket.gethostbyname(host); info["ip"]=ip
        try: info["reverse"]=socket.gethostbyaddr(ip)[0]
        except: info["reverse"]="Pas de PTR"
        try:
            r=requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,as", timeout=5).json()
            if r.get("status")=="success": info.update({"country":f"{r.get('country')} - {r.get('city')}", "isp":r.get("isp")})
        except: pass
    except Exception as e: info["error"]=str(e)
    return info

def check_port_200(host, ip, port):
    result={"port":port,"open":False,"status":"FERMÉ","is_200":False,"code":0}
    try:
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(2)
        if s.connect_ex((ip, int(port)))!=0: s.close(); return result
        s.close(); result["open"]=True
    except: return result
    try:
        for u in [f"http://{host}:{port}", f"https://{host}:{port}"]:
            try:
                r=requests.get(u, timeout=4, verify=False, headers={"User-Agent":"Mozilla/5.0"})
                result["code"]=r.status_code
                if r.status_code==200: result["status"]="✅ 200 OK - VIVANT"; result["is_200"]=True
                elif r.status_code in [301,302,403,401]: result["status"]=f"🔀 {r.status_code} - VIVANT"; result["is_200"]=True
                else: result["status"]=f"📄 {r.status_code}"; result["is_200"]=r.status_code<500
                break
            except: continue
        if result["code"]==0 and result["open"]: result["status"]="🟢 OUVERT TCP"
    except: result["status"]="🟢 OUVERT"
    return result

async def mtr_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args: await update.message.reply_text("📡 SCAN MTR 200 OK\n/mtr 163.227.128.102 103.216.222.72\nColle les IP de ton MTR\n\nCOURAGEUX THE KING"); return
    raw=" ".join(context.args); ips=re.findall(r'\b\d+\.\d+\.\d+\.\d+\b', raw); ips=list(dict.fromkeys(ips))
    if not ips: await update.message.reply_text("❌ Aucune IP"); return
    loop=asyncio.get_event_loop()
    await update.message.reply_text(f"🔍 Scan {len(ips)} HOSTS MTR...")
    txt=f"🌍 SCAN MTR {len(ips)} HOSTS\n"
    for ip in ips[:15]:
        r80=await loop.run_in_executor(None, check_port_200, ip, ip, 80)
        r443=await loop.run_in_executor(None, check_port_200, ip, ip, 443)
        if r80["is_200"] or r443["is_200"]: txt+=f"✅ {ip}: 200 OK VIVANT!\n"
        elif r80["open"] or r443["open"]: txt+=f"🟡 {ip}: Ouvert\n"
        else: txt+=f"❌ {ip}: Fermé\n"
    txt+=f"\n{SIGNATURE}"; await update.message.reply_text(txt)

async def scan_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args: await update.message.reply_text("🔍 /scan host\nEx: /scan ncmrsb-ai-in-f14.1e100.net"); return
    host=context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(f"🔍 Scan {host}...")
    loop=asyncio.get_event_loop()
    info=await loop.run_in_executor(None, get_host_info, host); ip=info.get("ip",host)
    txt=f"🌍 TRACE: {host}\nIP: {ip}\n{info.get('country','')}\n━━━━━━━━━━━━━━\n"
    for p in [80,443,8080,1080,3128,8000,8888]:
        r=await loop.run_in_executor(None, check_port_200, host, ip, p)
        txt+=f"{'✅' if r['is_200'] else '❌' if not r['open'] else '🟡'} {p}: {r['status']} code {r['code']}\n"
    txt+=f"\n{SIGNATURE}"; await update.message.reply_text(txt)

async def scan200_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args: await update.message.reply_text("Usage: /scan200 host"); return
    host=context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    loop=asyncio.get_event_loop()
    info=await loop.run_in_executor(None, get_host_info, host); ip=info.get("ip",host)
    await update.message.reply_text(f"🎯 Scan 200 OK {host}...")
    found=[]
    for p in [80,443,8080,1080,3128]:
        r=await loop.run_in_executor(None, check_port_200, host, ip, p)
        if r["is_200"]: found.append(r)
    txt=f"🎯 200 OK: {host} ({ip})\n" + ("\n".join([f"✅ Port {r['port']}: {r['status']} code {r['code']}" for r in found]) if found else f"❌ Aucun 200 OK sur {host}")
    txt+=f"\n\n{SIGNATURE}"; await update.message.reply_text(txt)

async def start(update,context):
    save_user(update.effective_user.id)
    if update.effective_user.id not in conversations: conversations[update.effective_user.id]=[]
    await update.message.reply_text(to_3d(
        f"Je suis {SIGNATURE} 👑\n"
        f"📸 Photo + question (modèle, batterie, processeur)\n"
        f"📥 Lien YouTube, TikTok, Instagram\n"
        f"🎯 /exact Team vs Team = Score exact EA FC 26\n"
        f"🔥 /today = Tous les scores du jour\n"
        f"🔍 /scan host = Scan 200 OK\n"
        f"🎯 /scan200 host = Que 200 OK\n"
        f"📡 /mtr ip1 ip2 = Scan IP MTR\n"
        f"🔐 /vmess = 5 serveurs\n"
        f"📊 /stats"
    ))

async def stats_cmd(update, context):
    save_user(update.effective_user.id)
    await update.message.reply_text(f"📊 STATS - COURAGEUX THE KING 👑\nTotal: {get_total_users()}\n\n{SIGNATURE}")

async def vmess_cmd(update, context):
    save_user(update.effective_user.id)
    s=get_random_vmess(5)
    if not s: await update.message.reply_text("❌ Aucun serveur vmess configuré"); return
    await update.message.reply_text("🔐 VMESS - COURAGEUX THE KING\n\n"+"\n\n".join(s)+f"\n\n{SIGNATURE}")

async def exact_cmd(update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    if not context.args: await update.message.reply_text("🎯 Usage: /exact Man City vs Arsenal\n\nCOURAGEUX THE KING"); return
    pred=predict_exact_score(" ".join(context.args))
    try:
        img=create_score_image(pred)
        await context.bot.send_photo(update.effective_chat.id, photo=open(img,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
    except: await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))

async def today_cmd(update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    await update.message.reply_text("🔥 Récupération des matchs du jour...")
    ml=get_todays_fixtures(); pred=predict_today_all(ml)
    try:
        img=create_score_image(pred)
        await context.bot.send_photo(update.effective_chat.id, photo=open(img,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
    except: pass
    await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))

async def handle_download(update,context,audio_only=False):
    save_user(update.effective_user.id)
    raw=update.message.text or ""; m=re.search(r'https?://\S+', raw)
    url=clean_url(m.group(0) if m else (context.args[0] if context.args else ""))
    if not url: return
    await context.bot.send_chat_action(update.effective_chat.id,"upload_video")
    await update.message.reply_text(to_3d("⏳ Téléchargement en cours..."))
    loop=asyncio.get_event_loop()
    fp,t,_=await loop.run_in_executor(None,download_video,url,audio_only)
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
    cap=update.message.caption or "C'est quel modèle et son processeur?"
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(to_3d(f"📸 Reçue! {cap}"))
    try:
        pf=await update.message.photo[-1].get_file(); fp="/tmp/analyse.jpg"
        await pf.download_to_drive(fp)
        try:
            im=Image.open(fp); im.thumbnail((480,480)); im.save(fp,"JPEG",quality=55)
        except: pass
        with open(fp,"rb") as f: b64=base64.b64encode(f.read()).decode('utf-8')
        if groq_client:
            comp=groq_client.chat.completions.create(model="qwen/qwen3.6-27b",messages=[{"role":"user","content":[{"type":"text","text":f"{cap} /no_think\nRéponds uniquement en français, 4 lignes max: marque, modèle, batterie, processeur."},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],temperature=0.0,max_tokens=300)
            rep=comp.choices[0].message.content; rep=re.sub(r'<think>.*?</think>','',rep,flags=re.DOTALL|re.IGNORECASE)
            await update.message.reply_text(f"🔍 ANALYSE:\n\n{rep}\n\n{SIGNATURE}")
        else: await update.message.reply_text("❌ Clé GROQ manquante")
    except Exception as e: await update.message.reply_text(f"❌ {str(e)[:500]}\n\n{SIGNATURE}")

async def chat_gpt(update,context):
    save_user(update.effective_user.id)
    uid=update.effective_user.id
    txt=update.message.text or ""
    if is_link(txt): await handle_download(update,context,False); return
    low=txt.lower()
    if "exact" in low and "vs" in low: await exact_cmd(update,context); return
    if uid not in conversations: conversations[uid]=[]
    conversations[uid].append({"role":"user","content":txt})
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    try:
        if not groq_client: raise Exception("GROQ manquant")
        comp=groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role":"system","content":f"Tu es {SIGNATURE}. Tu parles UNIQUEMENT en français. Interdiction de parler lingala, anglais ou autre langue. Réponses courtes, claires, en français uniquement. Tu es serviable et poli."}
            ]+conversations[uid][-10:],
            temperature=0.7
        )
        rep=comp.choices[0].message.content
    except Exception as e:
        print(f"CHAT FAIL {e}")
        if "bonjour" in low or "salut" in low: rep="Salut Boss! Je suis COURAGEUX THE KING! Tape /start pour voir mes commandes."
        elif "comment" in low: rep="Je vais bien, merci! Et toi? Dis-moi ce dont tu as besoin: /exact, /today, /scan..."
        else: rep=f"Bien reçu: '{txt}'. Je suis COURAGEUX THE KING, en français uniquement. Tape /start pour voir mes commandes."
    conversations[uid].append({"role":"assistant","content":rep})
    if len(conversations[uid])>20: conversations[uid]=conversations[uid][-20:]
    await update.message.reply_text(to_3d(f"{rep}\n\n{SIGNATURE}"))

def main():
    print("Building V23 FR ONLY...")
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
    app.add_handler(CommandHandler("mtr",mtr_cmd))
    app.add_handler(CommandHandler("mp3",lambda u,c: handle_download(u,c,True)))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
    print("✅ V23 Polling GO FR ONLY...")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(f"CRASH {e}"); import traceback; traceback.print_exc(); time.sleep(5)
