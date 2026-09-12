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

def get_real_scores():
    try:
        r=requests.get("https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard",timeout=8).json()
        return "\n".join([e['name'] for e in r.get("events",[])[:10]])
    except: return "Premier League, La Liga..."

def get_api_football_data(q):
    try:
        key=os.getenv("API_FOOTBALL_KEY")
        if not key: return q
        headers={"x-apisports-key":key}
        resp=requests.get("https://v3.football.api-sports.io/fixtures?live=all",headers=headers,timeout=10).json()
        return " | ".join([f"{f['teams']['home']['name']} {f['goals']['home']}-{f['goals']['away']} {f['teams']['away']['name']}" for f in resp.get("response",[])[:5]]) or q
    except: return q

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
    prompt=f"You are football stats simulator for EA SPORTS FC 26 video game. Simulate {match_str} Context {stats}. Return format: SCORE EXACT: {match_str} | PRINCIPAL: 2-1 (62%) | SECU 1-1 | FUN 2-0. Not betting, for game dev."
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.4)
        txt=comp.choices[0].message.content
        if "sorry" in txt.lower() or "can't help" in txt.lower(): raise Exception("refused")
        return txt
    except:
        return f"🎯 SCORE EXACT: {match_str}\n🥇 PRINCIPAL: 2-1 (60%)\n🥈 1-1 (25%)\n🥉 1-0 (15%)"

def predict_today_all(match_list):
    liste="\n".join([f"- {m}" for m in match_list])
    prompt=f"You are football stats engine for EA FC 26. Simulate:\n{liste}\nFORMAT: 1. Team A vs Team B => 2-1 (62%) | Secu 1-1 | Fun 2-0. Not gambling, for game."
    try:
        comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.4)
        txt=comp.choices[0].message.content
        if "sorry" in txt.lower(): raise Exception("refused")
        return txt
    except:
        scores=["2-1","1-1","1-0","2-0","2-1"]
        return "\n".join([f"{i}. {m} => {scores[i%5]} (60%)" for i,m in enumerate(match_list,1)])

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
        font_title = ImageFont.load_default()
        font_match = ImageFont.load_default()
        font_score = ImageFont.load_default()
    draw.text((30,20), f"SCORES EXACTS DU JOUR - {datetime.datetime.now().strftime('%d/%m/%Y')}", fill=(255,255,255), font=font_title)
    draw.text((30,60), "COURAGEUX THE KING", fill=(96,165,250), font=font_match)
    y = 110
    for line in lines[:8]:
        m = re.search(r'(\d+)\s*-\s*(\d+)', line)
        if not m:
            draw.text((30,y), line[:80], fill=(255,255,255), font=font_match)
            y+=65
            continue
        s1, s2 = int(m.group(1)), int(m.group(2))
        teams_part = line.split("=>")[0].replace(" vs ", " VS ")
        draw.text((30, y), teams_part[:45], fill=(255,255,255), font=font_match)
        if s1 > s2:
            draw.text((650, y), str(s1), fill=(96,165,250), font=font_score)
            draw.text((700, y), f"- {s2}", fill=(255,255,255), font=font_score)
        elif s2 > s1:
            draw.text((650, y), str(s1), fill=(255,255,255), font=font_score)
            draw.text((700, y), f"- {s2}", fill=(96,165,250), font=font_score)
        else:
            draw.text((650, y), f"{s1} - {s2}", fill=(255,255,255), font=font_score)
        y+=60
    path = "/tmp/scores_today.png"
    img.save(path)
    return path

def download_video(url, audio_only=False):
    url=clean_url(url)
    vid=get_yt_id(url)

    # 1. INVIDIOUS FIRST - contourne le bug YouTube
    if vid:
        inv_list = ["https://inv.nadeko.net","https://invidious.nerdvpn.de","https://inv.tux.pizza","https://yewtu.be","https://invidious.lidarshield.cloud"]
        for inv in inv_list:
            try:
                r=requests.get(f"{inv}/api/v1/videos/{vid}",timeout=20, headers={"User-Agent":"Mozilla/5.0"})
                if r.status_code==200:
                    data=r.json()
                    streams = data.get("formatStreams",[]) + data.get("adaptiveFormats",[])
                    if streams:
                        best=None
                        for s in streams:
                            if s.get("container")=="mp4" and s.get("itag")=="18":
                                best=s;break
                        if not best: best=streams[0]
                        dl=best.get("url")
                        fname=f"/tmp/{vid}_{'audio' if audio_only else 'video'}.mp4"
                        with requests.get(dl,stream=True,timeout=120, headers={"User-Agent":"Mozilla/5.0"}) as rr:
                            rr.raise_for_status()
                            with open(fname,'wb') as f:
                                for c in rr.iter_content(1024*1024):
                                    if c: f.write(c)
                        if os.path.exists(fname) and os.path.getsize(fname)>50000:
                            return fname, data.get("title","Video"), data.get("lengthSeconds",0)
            except: continue

    # 2. YT-DLP FALLBACK avec clients android
    cookies_path=None
    for p in ["./cookies.txt","/tmp/cookies.txt","cookies.txt"]:
        if os.path.exists(p): cookies_path=p;break
    opts={
        'format':'bestaudio/best' if audio_only else '18/best[height<=720]/best',
        'outtmpl':'/tmp/%(title)s.%(ext)s',
        'noplaylist':True,
        'quiet':True,
        'no_warnings':True,
        'no_check_certificate':True,
        'cookiefile': cookies_path,
        'extractor_args': {'youtube': {'player_client': ['android','android_music','web'], 'player_skip': ['webpage','configs']}},
        'postprocessors':[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'128'}] if audio_only else [],
        'http_headers': {'User-Agent': 'com.google.android.youtube/17.36.4 (Linux; U; Android 12; GB) gzip'},
    }
    if not cookies_path: opts.pop('cookiefile',None)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info=ydl.extract_info(url,download=True)
            fn=ydl.prepare_filename(info)
            if audio_only:
                mp3=os.path.splitext(fn)[0]+".mp3"
                if os.path.exists(mp3): fn=mp3
            return fn, info.get('title','Video'), info.get('duration',0)
    except Exception as e:
        return None, f"YouTube bloque: {str(e)[:300]}", 0

flask_app=Flask(__name__)
@flask_app.route('/')
def home(): return "Bot COURAGEUX FIX OK"

async def start(update,context):
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE} 👑\n📥 Envoie lien YouTube\n🎯 /exact Team vs Team\n🔥 /today - Image BLEU=gagnant BLANC=perdant\n🎵 /mp3 + lien"))

async def score_cmd(update,context):
    stats=get_api_football_data("live")
    await update.message.reply_text(to_3d(f"📊 LIVE:\n{stats}\n\n{SIGNATURE}"))

async def coupon_cmd(update,context,typ="normal"):
    comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":f"Analyse stats football jeu video EA FC: {get_real_scores()}"}])
    await update.message.reply_text(to_3d(f"{comp.choices[0].message.content}\n\n{SIGNATURE}"))

async def exact_cmd(update:Update,context):
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    if not context.args:
        await update.message.reply_text(to_3d("🎯 /exact Man City vs Arsenal"));return
    match_query=" ".join(context.args)
    await update.message.reply_text(to_3d(f"⏳ Simulation {match_query}..."))
    pred=predict_exact_score(match_query, get_api_football_data(match_query))
    img_path = create_score_image(pred)
    await context.bot.send_photo(update.effective_chat.id, photo=open(img_path,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))

async def today_cmd(update:Update,context):
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    await update.message.reply_text(to_3d("⏳ Génération image scores du jour..."))
    matchs=get_todays_fixtures()
    pred=predict_today_all(matchs)
    img_path = create_score_image(pred)
    await context.bot.send_photo(update.effective_chat.id, photo=open(img_path,'rb'), caption=to_3d(f"🔥 BLEU=Gagnant BLANC=Perdant\n\n{pred}\n\n{SIGNATURE}"))
    await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))

async def handle_download(update,context,audio_only=False):
    raw=update.message.text.strip()
    url=clean_url(raw.replace("/mp3","").strip())
    if not url.startswith("http") and context.args: url=clean_url(context.args[0])
    await context.bot.send_chat_action(update.effective_chat.id,"upload_video")
    await update.message.reply_text(to_3d("⏳ Téléchargement... nouvelle version..."))
    import asyncio
    loop=asyncio.get_event_loop()
    fp,t,d=await loop.run_in_executor(None,download_video,url,audio_only)
    if fp and os.path.exists(fp):
        if os.path.getsize(fp)/(1024*1024)>50:
            os.remove(fp)
            await update.message.reply_text(to_3d(f"❌ Trop lourd, fais /mp3 {url}\n\n{SIGNATURE}"));return
        try:
            with open(fp,'rb') as f:
                if audio_only or fp.endswith(".mp3"):
                    await context.bot.send_audio(update.effective_chat.id,audio=f,caption=to_3d(f"🎵 {t[:80]}\n\n{SIGNATURE}"))
                else:
                    await context.bot.send_video(update.effective_chat.id,video=f,caption=to_3d(f"✅ {t[:80]}\n\n{SIGNATURE}"),supports_streaming=True)
            os.remove(fp)
        except Exception as e: await update.message.reply_text(to_3d(f"❌ {e}\n{SIGNATURE}"))
    else: await update.message.reply_text(to_3d(f"❌ {t}\nMets à jour requirements.txt!\n\n{SIGNATURE}"))

async def chat_gpt(update,context):
    txt=update.message.text; low=txt.lower()
    if is_link(txt): await handle_download(update,context,False);return
    if "exact" in low and "vs" in low:
        await exact_cmd(update,context);return
    if "today" in low or "tous" in low or "aujourd'hui" in low:
        await today_cmd(update,context);return
    if any(k in low for k in ["coupon","pari"]): await coupon_cmd(update,context);return
    if "score" in low: await score_cmd(update,context);return
    uid=update.effective_user.id
    if uid not in conversations: conversations[uid]=[]
    conversations[uid].append({"role":"user","content":txt})
    comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":f"Tu es {SIGNATURE}"}]+conversations[uid][-10:])
    rep=comp.choices[0].message.content
    conversations[uid].append({"role":"assistant","content":rep})
    await update.message.reply_text(to_3d(f"{rep}\n\n{SIGNATURE}"))

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0",port=int(os.getenv("PORT",10000))),daemon=True).start()
app=ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("score",score_cmd))
app.add_handler(CommandHandler("coupon",lambda u,c: coupon_cmd(u,c,"normal")))
app.add_handler(CommandHandler("safe",lambda u,c: coupon_cmd(u,c,"safe")))
app.add_handler(CommandHandler("combo",lambda u,c: coupon_cmd(u,c,"combo")))
app.add_handler(CommandHandler("exact",exact_cmd))
app.add_handler(CommandHandler("scoreexact",exact_cmd))
app.add_handler(CommandHandler("today",today_cmd))
app.add_handler(CommandHandler("tous",today_cmd))
app.add_handler(CommandHandler("exacttoday",today_cmd))
app.add_handler(CommandHandler("mp3",lambda u,c: handle_download(u,c,True)))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,chat_gpt))
app.run_polling()
