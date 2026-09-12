import os, threading, requests
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
import yt_dlp

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
SIGNATURE = "COURAGEUX THE KING"

def to_3d(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold3d = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    res = ""
    for c in text:
        if c in normal:
            try: res += bold3d[normal.index(c)]
            except: res += c
        else: res += c
    return res

def clean_url(url):
    url = url.strip()
    url = url.split('?is=')[0].split('&is=')[0]
    url = url.split('?si=')[0].split('&si=')[0]
    return url

def is_link(text):
    return any(x in text.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com","fb.watch","facebook.com"])

def get_real_scores():
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard"
        r = requests.get(url, timeout=8).json()
        matches = []
        for e in r.get("events", [])[:15]:
            comp = e.get("competitions", [{}])[0]
            home = comp.get("competitors", [{}])[0].get("team", {}).get("displayName", "")
            away = comp.get("competitors", [{}])[1].get("team", {}).get("displayName", "") if len(comp.get("competitors", []))>1 else ""
            score_h = comp.get("competitors", [{}])[0].get("score", "")
            score_a = comp.get("competitors", [{}])[1].get("score", "") if len(comp.get("competitors", []))>1 else ""
            status = e.get("status", {}).get("type", {}).get("description", "")
            if score_h!="":
                matches.append(f"🔴 {home} {score_h}-{score_a} {away} ({status})")
            else:
                matches.append(f"⚽ {home} vs {away} - {status}")
        return "\n".join(matches) if matches else "Matchs Premier League du jour"
    except:
        return "Matchs du jour: Man City vs Arsenal, Barca vs Real, Bayern vs Dortmund"

def download_video(url, audio_only=False):
    url = clean_url(url)
    opts = {
        'format': 'bestaudio/best' if audio_only else 'best[height<=480][ext=mp4]/best[height<=480]/best',
        'outtmpl': '/tmp/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'no_check_certificate': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'player_skip': ['webpage'],
            }
        },
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'128'}] if audio_only else [],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if audio_only:
                mp3 = os.path.splitext(filename)[0] + ".mp3"
                if os.path.exists(mp3):
                    filename = mp3
            return filename, info.get('title','Video'), info.get('duration',0)
    except Exception as e:
        print(f"Erreur 1: {e}")
        try:
            opts['extractor_args']['youtube']['player_client'] = ['ios', 'android']
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                if audio_only:
                    filename = os.path.splitext(filename)[0] + ".mp3"
                return filename, info.get('title','Video'), info.get('duration',0)
        except Exception as e2:
            return None, str(e2), 0

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot COMPLET FIX YOUTUBE OK"

async def start(update: Update, context):
    conversations[update.effective_user.id] = []
    msg = f"Je suis {SIGNATURE} 👑\n\n📥 Envoie lien TikTok/YouTube/Insta je télécharge\n⚽ /coupon - Coupons du jour\n🎯 /safe - Coupon safe 95%\n💥 /combo - Cote 10+\n📊 /score - Vrais scores live\n🎵 /mp3 + lien - Audio seulement"
    await update.message.reply_text(to_3d(msg))

async def score_cmd(update: Update, context):
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    scores = get_real_scores()
    await update.message.reply_text(to_3d(f"📊 VRAIS SCORES LIVE:\n\n{scores}\n\n{SIGNATURE}"))

async def coupon_cmd(update: Update, context, typ="normal"):
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    real = get_real_scores()
    if typ=="safe": instr="Donne 1 coupon SAFE cote 1.80 avec 2 matchs max ultra sûr, confiance 90%+"
    elif typ=="combo": instr="Donne 1 COMBO cote 10 avec 5 matchs"
    else: instr="Donne 3 coupons: SAFE cote 1.80, NORMAL cote 4, FUN cote 8"
    prompt = f"Tu es {SIGNATURE} expert paris. Vrais matchs:\n{real}\n{instr}\nFORMAT: 🏆 Ligue, ⚽ Match, 👉 Pronostic, 📊 Confiance + raison, 💰 Cote, COTE TOTALE fin."
    try:
        comp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
        rep = comp.choices[0].message.content
    except:
        comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"user","content":prompt}])
        rep = comp.choices[0].message.content
    await update.message.reply_text(to_3d(f"{rep}\n\n{SIGNATURE}"))

async def handle_download(update: Update, context, audio_only=False):
    raw = update.message.text.strip()
    url = clean_url(raw.replace("/mp3","").strip())
    if not url.startswith("http"):
        if context.args:
            url = clean_url(context.args[0])
        else:
            await update.message.reply_text(to_3d("Envoie: /mp3 + lien YouTube\nEx: /mp3 https://youtu.be/xxx"))
            return

    await context.bot.send_chat_action(update.effective_chat.id, "upload_video")
    await update.message.reply_text(to_3d("⏳ Téléchargement... je contourne le blocage YouTube"))

    import asyncio
    loop = asyncio.get_event_loop()
    filepath, title, duration = await loop.run_in_executor(None, download_video, url, audio_only)

    if filepath and os.path.exists(filepath):
        size = os.path.getsize(filepath)/(1024*1024)
        if size>50:
            os.remove(filepath)
            await update.message.reply_text(to_3d(f"❌ Trop lourd {size:.1f}MB ({duration//60}min). Essaie /mp3 {url}\n\n{SIGNATURE}"))
            return
        try:
            with open(filepath,'rb') as f:
                if audio_only:
                    await context.bot.send_audio(update.effective_chat.id, audio=f, caption=to_3d(f"🎵 {title[:80]}\n\n{SIGNATURE}"))
                else:
                    await context.bot.send_video(update.effective_chat.id, video=f, caption=to_3d(f"✅ {title[:80]} - {duration//60}min\n\n{SIGNATURE}"), supports_streaming=True)
            os.remove(filepath)
        except Exception as e:
            await update.message.reply_text(to_3d(f"❌ Erreur: {e}\n{SIGNATURE}"))
            if os.path.exists(filepath): os.remove(filepath)
    else:
        await update.message.reply_text(to_3d(f"❌ Lien invalide ou privé\nErreur: {title}\n\n{SIGNATURE}"))

async def chat_gpt(update: Update, context):
    text = update.message.text
    if is_link(text):
        await handle_download(update, context, False)
        return
    if any(k in text.lower() for k in ["coupon","pari","prono","bet"]):
        await coupon_cmd(update, context, "normal")
        return
    if "score" in text.lower() or "live" in text.lower():
        await score_cmd(update, context)
        return

    uid = update.effective_user.id
    if uid not in conversations: conversations[uid]=[]
    conversations[uid].append({"role":"user","content":text})
    if len(conversations[uid])>20: conversations[uid]=conversations[uid][-20:]
    sys_msg = {"role":"system","content":f"Tu t'appelles {SIGNATURE}, expert foot et IA sympa."}
    try:
        comp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[sys_msg]+conversations[uid])
        rep = comp.choices[0].message.content
    except:
        comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b", messages=[sys_msg]+conversations[uid])
        rep = comp.choices[0].message.content
    conversations[uid].append({"role":"assistant","content":rep})
    await update.message.reply_text(to_3d(f"{rep}\n\n{SIGNATURE}"))

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()

app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("score", score_cmd))
app.add_handler(CommandHandler("coupon", lambda u,c: coupon_cmd(u,c,"normal")))
app.add_handler(CommandHandler("coups", lambda u,c: coupon_cmd(u,c,"normal")))
app.add_handler(CommandHandler("safe", lambda u,c: coupon_cmd(u,c,"safe")))
app.add_handler(CommandHandler("combo", lambda u,c: coupon_cmd(u,c,"combo")))
app.add_handler(CommandHandler("mp3", lambda u,c: handle_download(u,c,True)))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
