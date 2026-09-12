import os, re, requests, threading
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
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
    except: return "Matchs du jour: Premier League, La Liga..."

def get_api_football_data(match_query):
    try:
        key = os.getenv("API_FOOTBALL_KEY")
        if not key: return "API FOOT configurée mais en attente Live"
        headers = {"x-apisports-key": key}
        resp = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=headers, timeout=10).json()
        live = resp.get("response", [])[:5]
        info = ""
        for f in live:
            info += f"{f['teams']['home']['name']} {f['goals']['home']}-{f['goals']['away']} {f['teams']['away']['name']} | "
        return info if info else f"Analyse pour: {match_query}"
    except Exception as e:
        return f"Stats pour {match_query}"

def predict_exact_score(match_str, stats):
    prompt = f"""
Tu es COURAGEUX THE KING, expert mondial score exact.
Match: {match_str}
Infos API: {stats}
Live: {get_real_scores()}

Donne UN SEUL pronostic score exact format:

🎯 SCORE EXACT: {match_str}

🥇 PRINCIPAL: 2-1 (Confiance 62%)
   → Raison: domicile 2.1 xG

🥈 SECURITE: 1-1 (28%)

🥉 FUN: 2-0 (10%)

💡 Conseil: Double chance 1-1 + 2-1
"""
    comp = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role":"user","content":prompt}],
        temperature=0.3
    )
    return comp.choices[0].message.content

def download_video(url, audio_only=False):
    url=clean_url(url)
    cookies_path = None
    for p in ["./cookies.txt", "/tmp/cookies.txt", "cookies.txt"]:
        if os.path.exists(p): cookies_path = p; break
    vid = get_yt_id(url)
    if vid:
        for inv in ["https://inv.nadeko.net", "https://invidious.nerdvpn.de", "https://inv.tux.pizza"]:
            try:
                r=requests.get(f"{inv}/api/v1/videos/{vid}",timeout=15)
                if r.status_code==200:
                    data=r.json()
                    fmt=data.get("formatStreams",[])
                    if fmt:
                        best=next((x for x in fmt if x.get("itag")=="18"), fmt[0])
                        dl=best.get("url")
                        fname=f"/tmp/{vid}.mp4"
                        with requests.get(dl,stream=True,timeout=90) as rr:
                            with open(fname,'wb') as f:
                                for c in rr.iter_content(8192):
                                    if c: f.write(c)
                        if os.path.exists(fname) and os.path.getsize(fname)>1000:
                            return fname, data.get("title","Video"), data.get("lengthSeconds",0)
            except: continue
    opts={
        'format':'bestaudio/best' if audio_only else 'best[height<=480]/best',
        'outtmpl':'/tmp/%(title)s.%(ext)s',
        'noplaylist':True,
        'quiet':True,
        'no_check_certificate':True,
        'cookiefile': cookies_path if cookies_path else None,
        'extractor_args': {'youtube':{'player_client':['android','web']}},
        'postprocessors':[{'key':'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'128'}] if audio_only else [],
    }
    if not cookies_path: opts.pop('cookiefile')
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info=ydl.extract_info(url,download=True)
            fn=ydl.prepare_filename(info)
            if audio_only:
                mp3=os.path.splitext(fn)[0]+".mp3"
                if os.path.exists(mp3): fn=mp3
            return fn, info.get('title','Video'), info.get('duration',0)
    except Exception as e:
        return None, str(e), 0

flask_app=Flask(__name__)
@flask_app.route('/')
def home(): return "Bot COURAGEUX OK"

async def start(update,context):
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE} 👑\n\n📥 Lien YouTube/TikTok\n⚽ /coupon\n📊 /score\n🎯 /exact Man City vs Arsenal\n🎵 /mp3 + lien\n\nSCORE EXACT ACTIF!"))

async def score_cmd(update,context):
    stats=get_api_football_data("live")
    await update.message.reply_text(to_3d(f"📊 LIVE API FOOT:\n{stats}\n\n{get_real_scores()}\n\n{SIGNATURE}"))

async def coupon_cmd(update,context,typ="normal"):
    comp=groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":f"Donne coupons foot {get_real_scores()}"}])
    await update.message.reply_text(to_3d(f"{comp.choices[0].message.content}\n\n{SIGNATURE}"))

async def exact_cmd(update: Update, context):
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    if not context.args:
        await update.message.reply_text(to_3d("🎯 Tape: /exact Man City vs Arsenal"))
        return
    match_query=" ".join(context.args)
    await update.message.reply_text(to_3d(f"⏳ Analyse {match_query}..."))
    stats=get_api_football_data(match_query)
    pred=predict_exact_score(match_query, stats)
    await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))

async def handle_download(update,context,audio_only=False):
    raw=update.message.text.strip()
    url=clean_url(raw.replace("/mp3","").strip())
    if not url.startswith("http") and context.args: url=clean_url(context.args[0])
    await context.bot.send_chat_action(update.effective_chat.id,"upload_video")
    await update.message.reply_text(to_3d("⏳ Téléchargement..."))
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
        except Exception as e:
            await update.message.reply_text(to_3d(f"❌ {e}\n{SIGNATURE}"))
    else:
        await update.message.reply_text(to_3d(f"❌ Erreur: {t[:300]}\n{SIGNATURE}"))

async def chat_gpt(update,context):
    txt=update.message.text
    low=txt.lower()
    if is_link(txt):
        await handle_download(update,context,False);return
    if "exact" in low and "vs" in low:
        mq=txt.lower().replace("score exacte","").replace("score exact","").strip()
        await context.bot.send_chat_action(update.effective_chat.id, "typing")
        await update.message.reply_text(to_3d(f"⏳ Analyse {mq}..."))
        stats=get_api_football_data(mq)
        pred=predict_exact_score(mq, stats)
        await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"));return
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
app.add_handler(CommandHandler("mp3",lambda u,c: handle_download(u,c,True)))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,chat_gpt))
app.run_polling()
