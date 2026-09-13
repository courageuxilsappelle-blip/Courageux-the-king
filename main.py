import os, re, requests, threading, datetime, random, base64, socket, time, asyncio
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont
import urllib3
urllib3.disable_warnings()

TOKEN = os.getenv("TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
print(f"=== V24.3 GRANDS MATCHS FIX ===")

try:
    groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
except:
    groq_client = None

conversations = {}
SIGNATURE = "COURAGEUX THE KING"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return f"Bot {SIGNATURE} V24.3 LIVE"
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
        TOP_LEAGUES = [39, 140, 135, 78, 61, 2, 3]
        BAN = ["W ", "WOMEN", "FEM", "U19", "U20", "U21", "U23", " II", " B ", "YOUTH", "RESERVE", "AMATEUR"]

        if not key:
            return ["Barcelona vs Real Madrid","Manchester City vs Arsenal","PSG vs Marseille","Bayern Munich vs Dortmund","Inter vs AC Milan (Demain)","Liverpool vs Chelsea (Demain)"]

        headers={"x-apisports-key":key}
        resp=requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}",headers=headers,timeout=15).json()
        fixtures=resp.get("response",[])
        big_matchs=[]

        for f in fixtures:
            league_id=f.get("league",{}).get("id",0)
            if league_id not in TOP_LEAGUES:
                continue
            home_name=f['teams']['home']['name']
            away_name=f['teams']['away']['name']
            upper = f"{home_name} {away_name}".upper()
            if any(b in upper for b in BAN):
                continue
            if home_name.endswith(" W") or away_name.endswith(" W"):
                continue
            big_matchs.append(f"{home_name} vs {away_name}")

        # Si rien aujourd'hui, cherche les 3 prochains jours OBLIGATOIREMENT
        if len(big_matchs) == 0:
            for i in range(1,4):
                next_day=(datetime.datetime.now()+datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                try:
                    r2=requests.get(f"https://v3.football.api-sports.io/fixtures?date={next_day}",headers=headers,timeout=10).json()
                    for f in r2.get("response",[]):
                        if f.get("league",{}).get("id",0) not in TOP_LEAGUES:
                            continue
                        hn=f['teams']['home']['name']; an=f['teams']['away']['name']
                        up=f"{hn} {an}".upper()
                        if any(b in up for b in BAN):
                            continue
                        label = f"{hn} vs {an} (Demain)" if i==1 else f"{hn} vs {an} (J+{i})"
                        if label not in big_matchs:
                            big_matchs.append(label)
                        if len(big_matchs)>=8:
                            break
                except: continue
                if len(big_matchs)>=5:
                    break

        if len(big_matchs)==0:
            return ["Barcelona vs Real Madrid (Demain)","Man City vs Arsenal (Demain)","PSG vs Marseille (Demain)","Bayern vs Dortmund (J+2)","Liverpool vs Chelsea (J+2)"]

        return big_matchs[:8]
    except:
        return ["Barcelona vs Real Madrid (Demain)","Man City vs Arsenal (Demain)","PSG vs Marseille (Demain)"]

def predict_exact_score(match):
    if not groq_client: return f"{match} => 2-1 (60%)"
    try:
        prompt = "Simule EA FC 26 en francais uniquement, score exact + pourcentage + 2 buteurs pour: " + match
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.4)
        return comp.choices[0].message.content
    except: return f"{match} => 2-1 (60%)"

def predict_today_all(ml):
    liste = "\n".join([f"- {m}" for m in ml])
    if not groq_client: return "\n".join([f"{m} => 2-1 (60%)" for m in ml])
    try:
        prompt = "Simule EA FC 26 aujourdhui en francais uniquement pour ces grands matchs:\n" + liste + "\nFormat strict: Team vs Team => 2-1 (62%) Buteurs: Nom, Nom"
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.4)
        return comp.choices[0].message.content
    except: return "\n".join([f"{m} => 2-1 (60%)" for m in ml])

def create_score_image(t):
    lines=[l for l in t.split("\n") if "vs" in l.lower()][:10]
    W,H=900,120+len(lines)*70
    img=Image.new("RGB",(W,H),(15,23,42))
    draw=ImageDraw.Draw(img)
    try:
        f1=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",32)
        f2=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",22)
        f3=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",28)
    except: f1=f2=f3=ImageFont.load_default()
    draw.text((30,20),f"SCORES {datetime.datetime.now().strftime('%d/%m/%Y')}",fill=(255,255,255),font=f1)
    draw.text((30,60),f"{SIGNATURE} - GRANDS MATCHS",fill=(96,165,250),font=f2)
    y=110
    for line in lines:
        m=re.search(r'(\d+)\s*-\s*(\d+)',line)
        if not m: continue
        s1,s2=int(m.group(1)),int(m.group(2))
        teams=line.split("=>")[0][:50]
        draw.text((30,y),teams,fill=(255,255,255),font=f2)
        draw.text((680,y),f"{s1} - {s2}",fill=(96,165,250),font=f3)
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
    try: ip=socket.gethostbyname(host); info["ip"]=ip
    except Exception as e: info["error"]=str(e)
    return info

def check_port_200(host, ip, port):
    result={"port":port,"open":False,"status":"FERME","is_200":False,"code":0}
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
                if r.status_code==200: result["status"]="200 OK - VIVANT"; result["is_200"]=True
                elif r.status_code in [301,302,403,401]: result["status"]=f"{r.status_code} - VIVANT"; result["is_200"]=True
                else: result["status"]=f"{r.status_code}"; result["is_200"]=r.status_code<500
                break
            except: continue
        if result["code"]==0 and result["open"]: result["status"]="OUVERT TCP"
    except: result["status"]="OUVERT"
    return result

async def mtr_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args: await update.message.reply_text("📡 /mtr 163.227.128.102"); return
    raw=" ".join(context.args); ips=re.findall(r'\b\d+\.\d+\.\d+\.\d+\b', raw); ips=list(dict.fromkeys(ips))
    if not ips: await update.message.reply_text("Aucune IP"); return
    loop=asyncio.get_event_loop()
    await update.message.reply_text(f"Scan {len(ips)} HOSTS...")
    txt=f"SCAN MTR {len(ips)} HOSTS\n"
    for ip in ips[:15]:
        r=await loop.run_in_executor(None, check_port_200, ip, ip, 80)
        txt+=f"{'OK' if r['is_200'] else 'KO'} {ip}: {r['status']}\n"
    txt+=f"\n{SIGNATURE}"; await update.message.reply_text(txt)

async def scan_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args: await update.message.reply_text("🔍 /scan host"); return
    host=context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(f"Scan {host}...")
    loop=asyncio.get_event_loop()
    info=await loop.run_in_executor(None, get_host_info, host); ip=info.get("ip",host)
    txt=f"TRACE: {host}\nIP: {ip}\n"
    for p in [80,443,8080,1080,3128]:
        r=await loop.run_in_executor(None, check_port_200, host, ip, p)
        txt+=f"{p}: {r['status']}\n"
    txt+=f"\n{SIGNATURE}"; await update.message.reply_text(txt)

async def scan200_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args: await update.message.reply_text("Usage: /scan200 host"); return
    host=context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    loop=asyncio.get_event_loop()
    info=await loop.run_in_executor(None, get_host_info, host); ip=info.get("ip",host)
    await update.message.reply_text(f"Scan 200 OK {host}...")
    found=[]
    for p in [80,443,8080,1080]:
        r=await loop.run_in_executor(None, check_port_200, host, ip, p)
        if r["is_200"]: found.append(r)
    txt=f"200 OK: {host} ({ip})\n" + ("\n".join([f"OK {r['port']}: {r['code']}" for r in found]) if found else "Aucun 200 OK")
    txt+=f"\n\n{SIGNATURE}"; await update.message.reply_text(txt)

async def start(update,context):
    save_user(update.effective_user.id)
    if update.effective_user.id not in conversations: conversations[update.effective_user.id]=[]
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE}\n📸 Photo + question\n📥 Lien YouTube TikTok\n🎯 /exact Team vs Team\n🔥 /today = Grands matchs seulement (Barca, Real, City, PSG...)\n🔍 /scan host\n🎯 /scan200 host\n📡 /mtr ip1 ip2\n🔐 /vmess /stats"))

async def stats_cmd(update, context):
    save_user(update.effective_user.id)
    await update.message.reply_text(f"Total: {get_total_users()}\n\n{SIGNATURE}")

async def vmess_cmd(update, context):
    save_user(update.effective_user.id)
    s=get_random_vmess(5)
    if not s: await update.message.reply_text("Aucun serveur"); return
    await update.message.reply_text("VMESS\n\n"+"\n\n".join(s)+f"\n\n{SIGNATURE}")

async def exact_cmd(update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    if not context.args: await update.message.reply_text("🎯 /exact Man City vs Arsenal"); return
    pred=predict_exact_score(" ".join(context.args))
    try:
        img=create_score_image(pred)
        await context.bot.send_photo(update.effective_chat.id, photo=open(img,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
    except: await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))

async def today_cmd(update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    await update.message.reply_text("🔍 Recherche des grands matchs (Top 5 + C1)...")
    ml=get_todays_fixtures()
    is_future = any("Demain" in m or "J+" in m for m in ml)
    if is_future and len(ml)>0:
        await update.message.reply_text("⚠️ Pas de Top 5 aujourd'hui, voici les prochains grands matchs:")
    pred=predict_today_all(ml)
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
    await update.message.reply_text(to_3d("Telechargement..."))
    loop=asyncio.get_event_loop()
    fp,t,_=await loop.run_in_executor(None,download_video,url,audio_only)
    if fp and os.path.exists(fp):
        try:
            with open(fp,'rb') as f:
                if audio_only: await context.bot.send_audio(update.effective_chat.id,audio=f,caption=to_3d(f"{t}\n\n{SIGNATURE}"))
                else: await context.bot.send_video(update.effective_chat.id,video=f,caption=to_3d(f"{t}\n\n{SIGNATURE}"),supports_streaming=True)
            os.remove(fp)
        except Exception as e: await update.message.reply_text(to_3d(f"{e}"))
    else: await update.message.reply_text(to_3d(f"{t}"))

async def handle_photo(update, context):
    save_user(update.effective_user.id)
    cap=update.message.caption or "C est quel modele?"
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(to_3d(f"Recue! {cap}"))
    try:
        pf=await update.message.photo[-1].get_file(); fp="/tmp/analyse.jpg"
        await pf.download_to_drive(fp)
        with open(fp,"rb") as f: b64=base64.b64encode(f.read()).decode('utf-8')
        if groq_client:
            prompt_text = cap + " /no_think Reponds uniquement en francais, 4 lignes: marque modele batterie processeur."
            comp=groq_client.chat.completions.create(model="qwen/qwen3.6-27b",messages=[{"role":"user","content":[{"type":"text","text":prompt_text},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],temperature=0.0,max_tokens=300)
            rep=comp.choices[0].message.content; rep=re.sub(r'<think>.*?</think>','',rep,flags=re.DOTALL|re.IGNORECASE)
            await update.message.reply_text(f"ANALYSE:\n\n{rep}\n\n{SIGNATURE}")
        else: await update.message.reply_text("GROQ manquant")
    except Exception as e: await update.message.reply_text(f"{str(e)[:500]}\n\n{SIGNATURE}")

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
        sys_prompt = f"Tu es {SIGNATURE}. Tu parles UNIQUEMENT en francais. Jamais de lingala, jamais anglais. Reponses courtes."
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":sys_prompt}]+conversations[uid][-10:],temperature=0.7)
        rep=comp.choices[0].message.content
    except:
        if "bonjour" in low or "salut" in low: rep="Salut Boss! Je suis COURAGEUX THE KING! Tape /start"
        else: rep=f"Bien recu: {txt}. Tape /start"
    conversations[uid].append({"role":"assistant","content":rep})
    if len(conversations[uid])>20: conversations[uid]=conversations[uid][-20:]
    await update.message.reply_text(to_3d(f"{rep}\n\n{SIGNATURE}"))

def main():
    print("Building V24.3 FIX...")
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
    print("V24.3 Polling GO...")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(f"CRASH {e}"); import traceback; traceback.print_exc(); time.sleep(5)
