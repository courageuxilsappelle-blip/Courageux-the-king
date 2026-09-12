import os, re, requests, threading, datetime, random, base64
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
from PIL import Image, ImageDraw, ImageFont
import yt_dlp

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
SIGNATURE = "COURAGEUX THE KING"

# === VMESS ===
VMESS_FILE = "vmess.txt"
def load_vmess():
    try:
        env_data = os.getenv("VMESS_DATA")
        if env_data:
            return [l.strip() for l in env_data.splitlines() if l.strip().startswith("vmess://")]
        if os.path.exists(VMESS_FILE):
            with open(VMESS_FILE, "r") as f:
                return [l.strip() for l in f if l.strip().startswith("vmess://")]
        return []
    except: return []
def get_random_vmess(n=5):
    all_servers = load_vmess()
    if not all_servers: return None
    return random.sample(all_servers, min(n, len(all_servers)))

def to_3d(t):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold3d = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    return "".join([bold3d[normal.index(c)] if c in normal else c for c in t])

def clean_url(u): return u.strip().split('?is=')[0].split('&is=')[0].split('?si=')[0].split('&si=')[0]
def get_yt_id(u):
    m=re.search(r'(?:v=|be/|shorts/|embed/)([A-Za-z0-9_-]{11})',u)
    return m.group(1) if m else None
def is_link(t): return any(x in t.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com","fb.watch","facebook.com"])
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
    prompt=f"Simule EA FC 26: {match_str} Stats {stats}. Format: SCORE EXACT: {match_str} | PRINCIPAL: 2-1 (62%) | SECU 1-1 | FUN 2-0"
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.4)
        return comp.choices[0].message.content
    except: return f"🎯 SCORE EXACT: {match_str}\n🥇 2-1 (60%)"
def predict_today_all(match_list):
    liste="\n".join([f"- {m}" for m in match_list])
    prompt=f"Simulate EA FC 26:\n{liste}\nFORMAT: 1. Team A vs Team B => 2-1 (62%) | Secu 1-1 | Fun 2-0."
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
def home(): return "Bot COURAGEUX QWEN VISION OK"

async def start(update,context):
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE} 👑\n📸 Envoie PHOTO + question je vois tout\n📥 Lien YouTube\n🎯 /exact Team vs Team\n🔥 /today\n🔐 /vmess\n💬 Chat libre!"))

async def vmess_cmd(update, context):
    servers = get_random_vmess(5)
    if not servers:
        await update.message.reply_text("❌ Aucun serveur trouvé.\n\nCOURAGEUX THE KING")
        return
    text = "🔐 SERVEURS VMESS ACTIFS - COURAGEUX THE KING\n\n"
    for i, vm in enumerate(servers, 1):
        text += f"{i}. {vm}\n\n"
    text += "📲 Copie colle dans V2RayNG / DarkTunnel\n✅ Lien brut importable\n\nCOURAGEUX THE KING"
    await update.message.reply_text(text)

async def exact_cmd(update:Update,context):
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    if not context.args: await update.message.reply_text(to_3d("🎯 /exact Man City vs Arsenal"));return
    match_query=" ".join(context.args)
    pred=predict_exact_score(match_query)
    img_path=create_score_image(pred)
    await context.bot.send_photo(update.effective_chat.id, photo=open(img_path,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
async def today_cmd(update:Update,context):
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    matchs=get_todays_fixtures()
    pred=predict_today_all(matchs)
    img_path=create_score_image(pred)
    await context.bot.send_photo(update.effective_chat.id, photo=open(img_path,'rb'), caption=to_3d(f"🔥 BLEU=Gagnant\n\n{pred}\n\n{SIGNATURE}"))
    await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))

async def handle_download(update,context,audio_only=False):
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

# === VISION FIX 2026 - QWEN ===
async def handle_photo(update:Update, context):
    caption = update.message.caption or ""
    question = caption if caption else "Analyse cette photo en détail, c'est quel site et à quoi ça sert?"
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(to_3d(f"📸 Reçue!\n❓ {question}\n⏳ Analyse avec Qwen..."))
    try:
        photo_file = await update.message.photo[-1].get_file()
        file_path = "/tmp/analyse.jpg"
        await photo_file.download_to_drive(file_path)
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')

        completion = groq_client.chat.completions.create(
            model="qwen/qwen3.6-27b",
            messages=[
                {"role":"user","content":[
                    {"type":"text","text": question + " Réponds en français simple + un peu lingala."},
                    {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}
                ]}
            ],
            temperature=0.5,
            max_tokens=1200
        )
        rep = completion.choices[0].message.content
        if "</think>" in rep:
            rep = rep.split("</think>")[-1].strip()
        await update.message.reply_text(f"🔍 ANALYSE:\n\n{rep}\n\n{SIGNATURE}")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur vision: {str(e)[:600]}\n\n{SIGNATURE}")

async def chat_gpt(update,context):
    txt=update.message.text or update.message.caption or ""
    low=txt.lower()
    if is_link(txt): await handle_download(update,context,False);return
    if "exact" in low and "vs" in low: await exact_cmd(update,context);return
    if "today" in low or "tous" in low or "aujourd'hui" in low: await today_cmd(update,context);return
    if "vmess" in low or "v2ray" in low: await vmess_cmd(update,context);return
    uid=update.effective_user.id
    if uid not in conversations: conversations[uid]=[]
    conversations[uid].append({"role":"user","content":txt})
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":f"Tu es {SIGNATURE}, assistant intelligent, français + lingala."}]+conversations[uid][-10:],temperature=0.7)
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
app.add_handler(CommandHandler("mp3",lambda u,c: handle_download(u,c,True)))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
