import os, re, requests, threading, datetime, random, base64, socket, time, asyncio
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont
import urllib3
urllib3.disable_warnings()

TOKEN = os.getenv("TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
conversations = {}
SIGNATURE = "COURAGEUX THE KING"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return f"Bot {SIGNATURE} V19 LIVE"

def run_flask():
    flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), use_reloader=False)
threading.Thread(target=run_flask, daemon=True).start()
time.sleep(2)

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

# === FOOT ===
def get_todays_fixtures():
    try:
        key=os.getenv("API_FOOTBALL_KEY")
        today=datetime.datetime.now().strftime("%Y-%m-%d")
        if not key: return ["Man City vs Arsenal","Barcelona vs Real Madrid","PSG vs Lyon","Bayern vs Dortmund","Liverpool vs Chelsea"]
        headers={"x-apisports-key":key}
        resp=requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}",headers=headers,timeout=15).json()
        matchs=[f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}" for f in resp.get("response",[])[:10]]
        return matchs if matchs else ["Man City vs Arsenal","Barcelona vs Real Madrid"]
    except: return ["Man City vs Arsenal","Barcelona vs Real Madrid"]

def predict_exact_score(m,s=""):
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":f"Simule EA FC 26 en français, donne score exact + % et buteurs: {m} {s}"}],temperature=0.4)
        return comp.choices[0].message.content
    except: return f"🎯 {m} => 2-1 (60%) Buteur: Haaland"

def predict_today_all(ml):
    liste="\n".join([f"- {m}" for m in ml])
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":f"Simule EA FC 26 aujourd'hui en français:\n{liste}\nFORMAT STRICT:\nTeam vs Team => 2-1 (62%) Buteurs:..."}],temperature=0.4)
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
                dl=r.json().get("url")
                if dl:
                    fname=f"/tmp/{vid}_{'audio.mp3' if audio_only else 'video.mp4'}"
                    with requests.get(dl, stream=True, timeout=120) as rr:
                        with open(fname,'wb') as f:
                            for c in rr.iter_content(1024*1024):
                                if c: f.write(c)
                    if os.path.getsize(fname)>50000: return fname, "Video", 0
        except: continue
    return None, "Erreur", 0

# === MTR + SCAN ===
def get_host_info(host):
    info={}
    try:
        ip=socket.gethostbyname(host)
        info["ip"]=ip
        try: info["reverse"]=socket.gethostbyaddr(ip)[0]
        except: info["reverse"]="Pas de PTR"
        try:
            r=requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,as", timeout=5).json()
            if r.get("status")=="success": info.update({"country":f"{r.get('country')} - {r.get('city')}", "isp":r.get("isp"), "org":r.get("org"), "as":r.get("as")})
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
                if r.status_code==200: result["status"]="✅ 200 OK - VIVANT"; result["is_200"]=True
                elif r.status_code in [301,302,403,401]: result["status"]=f"🔀 {r.status_code} - VIVANT"; result["is_200"]=True
                else: result["status"]=f"📄 {r.status_code}"; result["is_200"]=r.status_code<500
                break
            except: continue
        if result["code"]==0 and result["open"]: result["status"]="🟢 OUVERT TCP"
    except: result["status"]="🟢 OUVERT"
    return result

def get_mtr_real(host):
    try:
        session=requests.Session()
        session.headers.update({"Accept":"application/json","User-Agent":"Mozilla/5.0"})
        r=session.get(f"https://check-host.net/check-mtr?host={host}&max_nodes=1", timeout=15)
        data=r.json()
        request_id=data.get("request_id")
        nodes=data.get("nodes",{})
        if not request_id: return {"error":"Pas de request_id"}
        result_url=f"https://check-host.net/check-result/{request_id}"
        final_data=None
        for _ in range(12):
            time.sleep(1.5)
            rr=session.get(result_url, timeout=15)
            if rr.status_code!=200: continue
            j=rr.json()
            for node,val in j.items():
                if val and isinstance(val, list) and len(val)>0 and val[0] and val[0][0]!=None:
                    final_data=j; break
            if final_data: break
        if not final_data: return {"error":"Timeout MTR"}
        for node_key,hops in final_data.items():
            if not hops or not hops[0]: continue
            mtr_list=hops[0]
            parsed=[]
            if isinstance(mtr_list, dict) and "result" in mtr_list: mtr_list=mtr_list["result"]
            if isinstance(mtr_list, list):
                for idx,hop in enumerate(mtr_list,1):
                    if not hop: continue
                    if isinstance(hop, dict):
                        ip=hop.get("address") or hop.get("ip") or "?"
                        hostn=hop.get("host") or ""
                        asn=hop.get("asn") or ""
                        parsed.append({"n":idx,"ip":ip,"host":hostn,"asn":asn})
            if parsed: return {"node":node_key,"hops":parsed,"nodes_info":nodes}
        return {"error":"Aucun HOTE"}
    except Exception as e: return {"error":str(e)}

async def mtrace_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("🌍 /mtrace host\nEx: /mtrace ncmrsb-ai-in-f14.1e100.net\n\nCOURAGEUX THE KING"); return
    host=context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    await update.message.reply_text(f"🌍 MTR TRACE {host}... 10-15s")
    loop=asyncio.get_event_loop()
    data=await loop.run_in_executor(None, get_mtr_real, host)
    if "error" in data:
        await update.message.reply_text(f"❌ {data['error']}\n\n{SIGNATURE}"); return
    hops=data.get("hops",[])
    text=f"🌍 MTR TRACE: {host}\n━━━━━━━━━━━━━━\n# HÔTE ASN\n"
    for h in hops[:15]:
        ip=h.get("ip","?")[:18]
        asn=h.get("asn","-")
        if not asn or asn=="-":
            try:
                r=requests.get(f"http://ip-api.com/json/{ip}?fields=as", timeout=2).json()
                asn=r.get("as","")[:12]
            except: asn="-"
        text+=f"{h['n']}. {ip} {asn}\n"
    text+=f"━━━━━━━━━━━━━━\n💡 /mtr {' '.join([h['ip'] for h in hops if h['ip']!='?' and not h['ip'].startswith('172.')][:5])}\n\n{SIGNATURE}"
    if len(text)>4000: text=text[:4000]
    await update.message.reply_text(text)

async def mtr_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("📡 /mtr ip1 ip2 ip3\nEx: /mtr 163.227.128.102 103.216.222.72\n\nCOURAGEUX THE KING"); return
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
        if r80["is_200"] or r443["is_200"]: found.append(ip); txt+=f"✅ {ip}: 200 OK VIVANT!\n"
        elif r80["open"] or r443["open"]: txt+=f"🟡 {ip}: Ouvert\n"
        else: txt+=f"❌ {ip}: Fermé\n"
    if found: txt+=f"\n🎯 {len(found)} AVEC 200 OK: {' '.join(found)}\n"
    txt+=f"\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def scan_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args: await update.message.reply_text("🔍 /scan host"); return
    host=context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(f"🔍 Scan {host}...")
    loop=asyncio.get_event_loop()
    host_info=await loop.run_in_executor(None, get_host_info, host)
    ip=host_info.get("ip",host)
    txt=f"🌍 TRACE: {host} IP:{ip}\n"
    for p in [80,443,8080,1080,3128,8000,8888]:
        r=await loop.run_in_executor(None, check_port_200, host, ip, p)
        txt+=f"{'✅' if r['is_200'] else '❌' if not r['open'] else '🟡'} {p}: {r['status']} code {r['code']}\n"
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
    txt=f"🎯 200 OK: {host} ({ip})\n" + ("\n".join([f"✅ {r['port']}: code {r['code']} VIVANT" for r in found]) if found else f"❌ Aucun 200 OK sur {host}")
    txt+=f"\n\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def start(update,context):
    save_user(update.effective_user.id)
    if update.effective_user.id not in conversations: conversations[update.effective_user.id]=[]
    msg = (
        f"Je suis {SIGNATURE} 👑\n"
        "📸 Photo + question (modèle, batterie, processeur)\n"
        "📥 Lien YouTube / TikTok / Insta\n"
        "🎯 /exact Team vs Team = Score exact EA FC 26\n"
        "🔥 /today = Tous les scores du jour\n"
        "🌍 /mtrace host = VRAI MTR TRACE comme ton image\n"
        "🔍 /scan host = Scan 200 OK\n"
        "🎯 /scan200 host = Que 200 OK\n"
        "📡 /mtr ip1 ip2 = Scan IP MTR\n"
        "🔐 /vmess = 5 serveurs\n"
        "📊 /stats"
    )
    await update.message.reply_text(to_3d(msg))

async def stats_cmd(update, context):
    save_user(update.effective_user.id)
    await update.message.reply_text(f"📊 STATS - COURAGEUX THE KING 👑\nTotal: {get_total_users()}\n{SIGNATURE}")

async def vmess_cmd(update, context):
    save_user(update.effective_user.id)
    servers=get_random_vmess(5)
    if not servers: await update.message.reply_text("❌ Aucun serveur"); return
    text="🔐 VMESS - COURAGEUX THE KING\n\n"+"\n\n".join(servers)+f"\n\n{SIGNATURE}"
    await update.message.reply_text(text)

async def exact_cmd(update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    if not context.args:
        await update.message.reply_text("🎯 Usage: /exact Man City vs Arsenal\n\nCOURAGEUX THE KING"); return
    match_text=" ".join(context.args)
    pred=predict_exact_score(match_text)
    try:
        img=create_score_image(pred)
        await context.bot.send_photo(update.effective_chat.id, photo=open(img,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
    except:
        await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))

async def today_cmd(update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    await update.message.reply_text("🔥 Récupération matchs du jour...")
    matchs=get_todays_fixtures()
    pred=predict_today_all(matchs)
    try:
        img=create_score_image(pred)
        await context.bot.send_photo(update.effective_chat.id, photo=open(img,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
    except: pass
    await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))

async def handle_download(update,context,audio_only=False):
    save_user(update.effective_user.id)
    raw=update.message.text or ""
    m=re.search(r'https?://\S+', raw)
    url=clean_url(m.group(0) if m else (context.args[0] if context.args else ""))
    if not url: return
    await context.bot.send_chat_action(update.effective_chat.id,"upload_video")
    await update.message.reply_text(to_3d("⏳ Téléchargement..."))
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
    await update.message.reply_text(to_3d(f"📸 Reçue! {caption}"))
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
        if groq_client:
            completion=groq_client.chat.completions.create(
                model="qwen/qwen3.6-27b",
                messages=[{"role":"user","content":[{"type":"text","text":f"{caption} /no_think\nRéponds seulement en français, 4 lignes max: marque, modèle, batterie, processeur."},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],
                temperature=0.0, max_tokens=250)
            rep=completion.choices[0].message.content or ""
            rep=re.sub(r'<think>.*?</think>','',rep,flags=re.DOTALL|re.IGNORECASE)
            rep=re.sub(r'</?think>','',rep,flags=re.IGNORECASE)
            await update.message.reply_text(f"🔍 ANALYSE:\n\n{rep}\n\n{SIGNATURE}")
        else:
            await update.message.reply_text("❌ GROQ manquant")
    except Exception as e:
        await update.message.reply_text(f"❌ {str(e)[:500]}\n\n{SIGNATURE}")

async def chat_gpt(update,context):
    save_user(update.effective_user.id)
    uid=update.effective_user.id
    txt=update.message.text or ""
    low=txt.lower()
    if is_link(txt):
        await handle_download(update,context,False); return
    if "exact" in low and "vs" in low:
        await exact_cmd(update,context); return
    if uid not in conversations: conversations[uid]=[]
    conversations[uid].append({"role":"user","content":txt})
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":f"Tu es {SIGNATURE}. Tu parles français + lingala, tu es le Roi Courageux, serviable, fun, tu réponds à toutes les questions."}]+conversations[uid][-10:],temperature=0.7)
        rep=comp.choices[0].message.content
    except Exception as e:
        rep=f"Yo Boss! Je suis là! Erreur: {e}"
        if "429" in str(e): rep="⏳ Limite atteinte, attends 1 min Boss!"
    conversations[uid].append({"role":"assistant","content":rep})
    if len(conversations[uid])>20: convers
