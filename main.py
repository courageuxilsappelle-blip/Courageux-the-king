import os, threading, requests, re
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

def get_yt_id(url):
    m = re.search(r'(?:v=|be/|shorts/|embed/)([A-Za-z0-9_-]{11})', url)
    return m.group(1) if m else None

def is_link(text):
    return any(x in text.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com","fb.watch","facebook.com"])

def get_real_scores():
    try:
        r = requests.get("https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard", timeout=8).json()
        return "\n".join([e['name'] for e in r.get("events", [])[:10]])
    except:
        return "Matchs du jour"

def download_youtube_via_piped(url, audio_only=False):
    vid = get_yt_id(url)
    if not vid:
        return None, "ID YouTube non trouvé", 0

    # Liste d'instances Piped (si une tombe, l'autre marche)
    piped_instances = [
        "https://pipedapi.kavin.rocks",
        "https://pipedapi.adminforge.de",
        "https://api.piped.yt",
        "https://pipedapi.drgns.space"
    ]

    for api in piped_instances:
        try:
            print(f"Essaie Piped: {api}")
            r = requests.get(f"{api}/streams/{vid}", timeout=15)
            if r.status_code!= 200:
                continue
            data = r.json()

            if audio_only:
                streams = data.get("audioStreams", [])
                if not streams: continue
                best = streams[0] # meilleur audio
                dl_url = best.get("url")
                ext = ".mp3"
            else:
                streams = data.get("videoStreams", [])
                if not streams: continue
                # Prend 480p ou 360p pour rester <50MB
                best = None
                for q in ["480p", "360p", "720p"]:
                    for s in streams:
                        if s.get("quality") == q and s.get("mimeType","").startswith("video/mp4"):
                            best = s
                            break
                    if best: break
                if not best:
                    best = streams[0]
                dl_url = best.get("url")
                ext = ".mp4"

            if not dl_url:
                continue

            fname = f"/tmp/{vid}{ext}"
            print(f"Download from Piped: {dl_url[:100]}")
            with requests.get(dl_url, stream=True, timeout=90) as rr:
                rr.raise_for_status()
                with open(fname, 'wb') as f:
                    for chunk in rr.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

            if os.path.exists(fname) and os.path.getsize(fname) > 1000:
                return fname, data.get("title", "Video"), data.get("duration", 0)

        except Exception as e:
            print(f"Piped {api} fail: {e}")
            continue

    return None, "Piped fail", 0

def download_video(url, audio_only=False):
    url = clean_url(url)

    # Si c'est YouTube -> utilise Piped (anti-bot)
    if "youtu" in url or "youtube.com" in url:
        f, t, d = download_youtube_via_piped(url, audio_only)
        if f:
            return f, t, d

    # Pour TikTok / Insta / FB -> yt-dlp marche encore
    opts = {
        'format': 'bestaudio/best' if audio_only else 'best[height<=480]/best',
        'outtmpl': '/tmp/%(title)s.%(ext)s',
        'noplaylist': True,
        'quiet': True,
        'no_check_certificate': True,
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
def home(): return "Bot Piped FIX OK"

async def start(update: Update, context):
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE} 👑\n\n📥 Envoie lien YouTube/TikTok/Insta\n⚽ /coupon\n📊 /score\n🎵 /mp3 + lien\n\nNouveau système Piped activé - YouTube débloqué!"))

async def score_cmd(update: Update, context):
    await update.message.reply_text(to_3d(f"📊 {get_real_scores()}\n\n{SIGNATURE}"))

async def coupon_cmd(update: Update, context, typ="normal"):
    real = get_real_scores()
    prompt = f"Tu es {SIGNATURE} expert paris. Matchs: {real}. Donne 3 coupons."
    comp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
    await update.message.reply_text(to_3d(f"{comp.choices[0].message.content}\n\n{SIGNATURE}"))

async def handle_download(update: Update, context, audio_only=False):
    raw = update.message.text.strip()
    url = clean_url(raw.replace("/mp3","").strip())
    if not url.startswith("http") and context.args:
        url = clean_url(context.args[0])

    await context.bot.send_chat_action(update.effective_chat.id, "upload_video")
    await update.message.reply_text(to_3d("⏳ Téléchargement via Piped (contourne blocage YouTube)... 20s max"))

    import asyncio
    loop = asyncio.get_event_loop()
    filepath, title, duration = await loop.run_in_executor(None, download_video, url, audio_only)

    if filepath and os.path.exists(filepath):
        size = os.path.getsize(filepath)/(1024*1024)
        if size>50:
            os.remove(filepath)
            await update.message.reply_text(to_3d(f"❌ {size:.1f}MB trop lourd. Fais /mp3 {url}\n\n{SIGNATURE}"))
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
        await update.message.reply_text(to_3d(f"❌ Piped surchargé, réessaie dans 30s.\nErreur: {title[:200]}\n\n{SIGNATURE}"))

async def chat_gpt(update: Update, context):
    text = update.message.text
    if is_link(text):
        await handle_download(update, context, False); return
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
