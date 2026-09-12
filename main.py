import os, re, requests, threading, datetime
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
from PIL import Image, ImageDraw, ImageFont
import yt_dlp

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
SIGNATURE = "COURAGEUX THE KING"

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
        if not key:
            return ["Man City vs Arsenal","Barcelona vs Real Madrid","TP Mazembe vs Vita Club","Bayern vs Dortmund","PSG vs Marseille"]
        headers={"x-apisports-key":key}
        resp=requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}",headers=headers,timeout=15).json()
        matchs=[f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}" for f in resp.get("response",[])[:10]]
        return matchs if matchs else ["Man City vs Arsenal","Barcelona vs Real Madrid","TP Mazembe vs Vita Club"]
    except:
        return ["Man City vs Arsenal","Barcelona vs Real Madrid","TP Mazembe vs Vita Club"]

def predict_exact_score(match_str, stats):
    prompt=f"You are football stats simulator for EA SPORTS FC 26. Simulate {match_str}. Return: SCORE EXACT: {match_str} | PRINCIPAL: 2-1 (62%) | SECU 1-1 | FUN 2-0. Not betting."
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.4)
        return comp.choices[0].message.content
    except:
        return f"🎯 SCORE EXACT: {match_str}\n🥇 PRINCIPAL: 2-1 (60%)\n🥈 1-1 (25%)\n🥉 1-0 (15%)"

def predict_today_all(match_list):
    liste="\n".join([f"- {m}" for m in match_list])
    prompt=f"Simulate for EA FC 26:\n{liste}\nFORMAT: 1. Team A vs Team B => 2-1 (62%) | Secu 1-1 | Fun 2-0."
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.4)
        return comp.choices[0].message.content
    except:
        return "\n".join([f"{i}. {m} => 2-1 (60%)" for i,m in enumerate(match_list,1)])

def create_score_image(pred_text):
    lines = [l for l in pred_text.split("\n") if "vs" in l.lower() and "=>" in l]
    if not lines: lines = [l for l in pred_text.split("\n") if "vs" in l.lower()][:8]
    W, H = 900, 120 + len(lines)*70
    img = Image.new("RGB", (W, H), (15, 23, 42))
    draw = ImageDraw.Draw(img)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_match = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
        font_score = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except:
        font_title = font_match = font_score = ImageFont.load_default()
    draw.text((30,20), f"SCORES {datetime.datetime.now().strftime('%d/%m/%Y')}", fill=(255,255,255), font=font_title)
    draw.text((30,60), "COURAGEUX THE KING", fill=(96,165,250), font=font_match)
    y=110
    for line in lines[:8]:
        m = re.search(r'(\d+)\s*-\s*(\d+)', line)
        if not m: continue
        s1,s2=int(m.group(1)),int(m.group(2))
        teams_part=line.split("=>")[0][:45]
        draw.text((30,y), teams_part, fill=(255,255,255), font=font_match)
        if s1>s2:
            draw.text((650,y), str(s1), fill=(96,165,250), font=font_score)
            draw.text((700,y), f"- {s2}", fill=(255,255,255), font=font_score)
        elif s2>s1:
            draw.text((650,y), str(s1), fill=(255,255,255), font=font_score)
            draw.text((700,y), f"- {s2}", fill=(96,165,250), font=font_score)
        else:
            draw.text((650,y), f"{s1} - {s2}", fill=(255,255,255), font=font_score)
        y+=60
    path="/tmp/scores_today.png"
    img.save(path)
    return path

# FONCTION QUI MARCHE MAINTENANT - COBALT
def download_video(url, audio_only=False):
    url=clean_url(url)
    vid=get_yt_id(url) or "video"
    for api in ["https://api.cobalt.tools/api/json","https://co.wuk.sh/api/json","https://cobalt-api.kwiatekmiki.com/api/json"]:
        try:
            r=requests.post(api, json={"url":url,"vCodec":"h264","vQuality":"720","aFormat":"mp3" if audio_only else "best","isAudioOnly":audio_only}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=30)
            if r.status_code==200:
                data=r.json()
                dl_url=data.get("url")
                if dl_url:
                    fname=f"/tmp/{vid}_{'audio.mp3' if audio_only else 'video.mp4'}"
                    with requests.get(dl_url, stream=True, timeout=120) as rr:
                        with open(fname,'wb') as f:
                            for c in rr.iter_content(1024*1024):
                                if c: f.write(c)
                    if os.path.getsize(fname)>50000:
                        return fname, "Video", 0
        except: continue
    try:
        opts={'format':'bestaudio/best' if audio_only else '18/best','outtmpl':'/tmp/%(title)s.%(ext)s','noplaylist':True,'quiet':True,'extractor_args':{'youtube':{'player_client':['android']}},'postprocessors':[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'128'}] if audio_only else []}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info=ydl.extract_info(url,download=True)
            fn=ydl.prepare_filename(info)
            if audio_only:
                mp3=os.path.splitext(fn)[0]+".mp3"
                if os.path.exists(mp3): fn=mp3
            return fn, info.get('title','Video'), 0
    except Exception as e:
        return None, str(e)[:200], 0

flask_app=Flask(__name__)
@flask_app.route('/')
def home(): return "Bot COURAGEUX FIX OK"

async def start(update,context):
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE} 👑\n📥 Envoie lien YouTube\n🎯 /exact Team vs Team\n🔥 /today - Image BLEU=gagnant"))

async def today_cmd(update,context):
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    matchs=get_todays_fixtures()
    pred=predict_today_all(matchs)
    img_path=create_score_image(pred)
    await context.bot.send_photo(update.effective_chat.id, photo=open(img_path,'rb'), caption=to_3d(f"🔥 BLEU=Gagnant BLANC=Perdant\n\n{pred}\n\n{SIGNATURE}"))

async def exact_cmd(update,context):
    if not context.args:
        await update.message.reply_text(to_3d("🎯 /exact Man City vs Arsenal"));return
    match_query=" ".join(context.args)
    pred=predict_exact_score(match_query,"live")
    img_path=create_score_image(pred)
    await context.bot.send_photo(update.effective_chat.id, photo=open(img_path,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))

async def handle_download(update,context,audio_only=False):
    raw=update.message.text.strip()
    url=clean_url(raw.replace("/mp3","").strip())
    if not url.startswith("http") and context.args: url=clean_url(context.args[0])
    await context.bot.send_chat_action(update.effective_chat.id,"upload_video")
    await update.message.reply_text(to_3d("⏳ Téléchargement via Cobalt..."))
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

async def chat_gpt(update,context):
    txt=update.message.text
    if any(x in txt.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com"]):
        await handle_download(update,context,False);return
    if "today" in txt.lower() or "tous" in txt.lower():
        await today_cmd(update,context);return
    await update.message.reply_text(to_3d(f"Envoie un lien YouTube Boss!\n\n{SIGNATURE}"))

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0",port=int(os.getenv("PORT",10000))),daemon=True).start()
app=ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("today",today_cmd))
app.add_handler(CommandHandler("tous",today_cmd))
app.add_handler(CommandHandler("exact",exact_cmd))
app.add_handler(CommandHandler("mp3",lambda u,c: handle_download(u,c,True)))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,chat_gpt))
app.run_polling()
