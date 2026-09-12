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
    return "".join([bold3d[normal.index(c)] if c in normal else c for c in text])

def clean_url(url):
    return url.strip().split('?is=')[0].split('&is=')[0].split('?si=')[0].split('&si=')[0]

def is_link(text):
    return any(x in text.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com","fb.watch","facebook.com"])

def get_real_scores():
    try:
        r = requests.get("https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard", timeout=8).json()
        matches = [f"{e['name']}" for e in r.get("events", [])[:10]]
        return "\n".join(matches)
    except:
        return "Matchs du jour: Premier League, La Liga..."

def download_via_cobalt(url, audio_only=False):
    # API qui contourne tout blocage YouTube
    try:
        payload = {
            "url": url,
            "vQuality": "480",
            "aFormat": "mp3" if audio_only else "best",
            "isAudioOnly": audio_only,
            "filenamePattern": "basic"
        }
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        # On essaie plusieurs instances cobalt
        for api in ["https://api.cobalt.tools/api/json", "https://co.wuk.sh/api/json"]:
            try:
                res = requests.post(api, json=payload, headers=headers, timeout=20)
                data = res.json()
                if data.get("status") in ["tunnel", "redirect"]:
                    dl_url = data.get("url")
                    if dl_url:
                        # Télécharge le fichier
                        fname = "/tmp/video_cobalt.mp4" if not audio_only else "/tmp/audio_cobalt.mp3"
                        with requests.get(dl_url, stream=True, timeout=60) as r:
                            r.raise_for_status()
                            with open(fname, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        return fname, "Video via Cobalt", 0
            except Exception as e:
                print(f"Cobalt {api} fail: {e}")
                continue
        return None, "Cobalt fail", 0
    except Exception as e:
        return None, str(e), 0

def download_video(url, audio_only=False):
    url = clean_url(url)
    # 1. Essaie Cobalt en premier (marche même si YouTube bloque)
    f, t, d = download_via_cobalt(url, audio_only)
    if f and os.path.exists(f):
        return f, t, d

    # 2. Sinon essaie yt-dlp (pour TikTok, Insta, FB)
    opts = {
        'format': 'bestaudio/best' if audio_only else 'best[height<=480]/best',
        'outtmpl': '/tmp/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['android']}},
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec':'mp3','preferredquality':'128'}] if audio_only else [],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if audio_only:
                mp3 = os.path.splitext(filename)[0] + ".mp3"
                if os.path.exists(mp3): filename = mp3
            return filename, info.get('title','Video'), info.get('duration',0)
    except Exception as e:
        return None, str(e), 0

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot Cobalt FIX OK"

async def start(update: Update, context):
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE} 👑\n\n📥 Envoie lien YouTube/TikTok/Insta\n⚽ /coupon - Coupons\n📊 /score - Scores live\n🎵 /mp3 + lien - Audio\n\nNouveau système anti-blocage activé!"))

async def score_cmd(update: Update, context):
    scores = get_real_scores()
    await update.message.reply_text(to_3d(f"📊 SCORES:\n{scores}\n\n{SIGNATURE}"))

async def coupon_cmd(update: Update, context, typ="normal"):
    real = get_real_scores()
    instr = "Donne 3 coupons SAFE/NORMAL/FUN" if typ=="normal" else "Donne 1 coupon SAFE cote 1.80" if typ=="safe" else "Donne 1 COMBO cote 10"
    prompt = f"Tu es {SIGNATURE} expert paris. Matchs: {real}. {instr}"
    comp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
    await update.message.reply_text(to_3d(f"{comp.choices[0].message.content}\n\n{SIGNATURE}"))

async def handle_download(update: Update, context, audio_only=False):
    raw = update.message.text.strip()
    url = clean_url(raw.replace("/mp3","").strip())
    if not url.startswith("http"):
        if context.args: url = clean_url(context.args[0])
        else:
            await update.message.reply_text(to_3d("Envoie: /mp3 + lien YouTube"))
            return
    await context.bot.send_chat_action(update.effective_chat.id, "upload_video")
    await update.message.reply_text(to_3d("⏳ Téléchargement avec nouveau système anti-blocage YouTube..."))
    import asyncio
    loop = asyncio.get_event_loop()
    filepath, title, duration = await loop.run_in_executor(None, download_video, url, audio_only)
    if filepath and os.path.exists(filepath):
        size = os.path.getsize(filepath)/(1024*1024)
        if size>50:
            os.remove(filepath)
            await update.message.reply_text(to_3d(f"❌ Trop lourd {size:.1f}MB. Essaie /mp3 {url}\n\n{SIGNATURE}"))
            return
        try:
            with open(filepath,'rb') as f:
                if audio_only or filepath.endswith(".mp3"):
                    await context.bot.send_audio(update.effective_chat.id, audio=f, caption=to_3d(f"🎵 {title[:80]}\n\n{SIGNATURE}"))
                else:
                    await context.bot.send_video(update.effective_chat.id, video=f, caption=to_3d(f"✅ {title[:80]}\n\n{SIGNATURE}"), supports_streaming=True)
            os.remove(filepath)
        except Exception as e:
            await update.message.reply_text(to_3d(f"❌ Erreur envoi: {e}\n{SIGNATURE}"))
    else:
        await update.message.reply_text(to_3d(f"❌ Erreur: {title}\nEssaie un lien TikTok pour tester, YouTube est en maintenance.\n\n{SIGNATURE}"))

async def chat_gpt(update: Update, context):
    text = update.message.text
    if is_link(text):
        await handle_download(update, context, False)
        return
    if any(k in text.lower() for k in ["coupon","pari","prono"]):
        await coupon_cmd(update, context, "normal"); return
    if "score" in text.lower():
        await score_cmd(update, context); return
    uid = update.effective_user.id
    if uid not in conversations: conversations[uid]=[]
    conversations[uid].append({"role":"user","content":text})
    comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"system","content":f"Tu es {SIGNATURE}"}]+conversations[uid][-10:])
    rep = comp.choices[0].message.content
    conversations[uid].append({"role":"assistant","content":rep})
    await update.message.reply_text(to_3d(f"{rep}\n\n{SIGNATURE}"))

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()
app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("score", score_cmd))
app.add_handler(CommandHandler("coupon", lambda u,c: coupon_cmd(u,c,"normal")))
app.add_handler(CommandHandler("safe", lambda u,c: coupon_cmd(u,c,"safe")))
app.add_handler(CommandHandler("combo", lambda u,c: coupon_cmd(u,c,"combo")))
app.add_handler(CommandHandler("mp3", lambda u,c: handle_download(u,c,True)))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
