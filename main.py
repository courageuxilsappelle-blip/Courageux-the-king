import os
import re
import requests
import threading
import datetime
import random
import base64
import socket
import time
import asyncio
import textwrap

from flask import Flask
from groq import Groq
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters
)

from PIL import Image, ImageDraw, ImageFont

import urllib3
urllib3.disable_warnings()


# =========================================================
# CONFIGURATION
# =========================================================

TOKEN = os.getenv("TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

print("=== V25.3 FULL + PDF + EXACT FIX ===")

try:
    groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
except Exception as e:
    print("Erreur Groq:", e)
    groq_client = None


# =========================================================
# MEMOIRE
# =========================================================

conversations = {}

SIGNATURE = "COURAGEUX THE KING"


# =========================================================
# FLASK
# =========================================================

flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    return f"Bot {SIGNATURE} V25.3 FULL LIVE"


def run_flask():
    try:
        flask_app.run(
            host="0.0.0.0",
            port=int(os.getenv("PORT", 10000)),
            use_reloader=False
        )
    except Exception as e:
        print("Flask Error:", e)


threading.Thread(
    target=run_flask,
    daemon=True
).start()

time.sleep(1)


# =========================================================
# UTILISATEURS
# =========================================================

USERS_FILE = "users.txt"


def save_user(uid):
    try:
        if not os.path.exists(USERS_FILE):
            open(USERS_FILE, "w").close()

        with open(USERS_FILE, "r") as f:
            d = f.read()

        if str(uid) not in d:
            with open(USERS_FILE, "a") as f:
                f.write(f"{uid}\n")

    except Exception:
        pass


def get_total_users():
    try:
        with open(USERS_FILE, "r") as f:
            return len([l for l in f if l.strip()])
    except Exception:
        return 0


# =========================================================
# TEXTE 3D
# =========================================================

def to_3d(t):
    try:
        n = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "abcdefghijklmnopqrstuvwxyz"
            "0123456789"
        )

        b = (
            "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
            "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
            "𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
        )

        return "".join(
            b[n.index(c)] if c in n else c
            for c in t
        )

    except Exception:
        return t


# =========================================================
# PDF
# =========================================================

def create_pdf_book(title, content):
    try:
        pages = []

        W, H = 800, 1100

        wrapper = textwrap.TextWrapper(width=70)

        img = Image.new(
            "RGB",
            (W, H),
            (255, 255, 255)
        )

        draw = ImageDraw.Draw(img)

        try:
            f_title = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                40
            )

            f_text = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                20
            )

        except Exception:
            f_title = f_text = ImageFont.load_default()

        draw.text(
            (50, 400),
            title[:30],
            fill=(0, 0, 0),
            font=f_title
        )

        draw.text(
            (50, 500),
            f"Par {SIGNATURE}",
            fill=(100, 100, 100),
            font=f_text
        )

        pages.append(img)

        words = wrapper.wrap(content)

        for i in range(0, len(words), 35):

            img = Image.new(
                "RGB",
                (W, H),
                (255, 255, 255)
            )

            draw = ImageDraw.Draw(img)

            y = 50

            for line in words[i:i + 35]:

                draw.text(
                    (50, y),
                    line,
                    fill=(0, 0, 0),
                    font=f_text
                )

                y += 28

            pages.append(img)

        safe_title = re.sub(
            r"[^a-zA-Z0-9_-]",
            "_",
            title[:15]
        )

        pdf_path = f"/tmp/{safe_title}.pdf"

        pages[0].save(
            pdf_path,
            "PDF",
            resolution=100.0,
            save_all=True,
            append_images=pages[1:]
        )

        return pdf_path

    except Exception as e:
        print(f"PDF Error: {e}")
        return None


# =========================================================
# URL / VIDEO
# =========================================================

def clean_url(u):
    return (
        u.strip()
        .split("?is=")[0]
        .split("&is=")[0]
        .split("?si=")[0]
    )


def get_yt_id(u):
    m = re.search(
        r"(?:v=|be/|shorts/|embed/)"
        r"([A-Za-z0-9_-]{11})",
        u
    )

    return m.group(1) if m else None


def is_link(t):
    return any(
        x in t.lower()
        for x in [
            "http://",
            "https://",
            "tiktok.com",
            "youtu",
            "instagram.com",
            "fb.watch",
            "facebook.com"
        ]
    )


def download_video(url, audio_only=False):

    url = clean_url(url)

    vid = get_yt_id(url) or "video"

    for api in [
        "https://api.cobalt.tools/api/json",
        "https://co.wuk.sh/api/json"
    ]:

        try:

            r = requests.post(
                api,
                json={
                    "url": url,
                    "vCodec": "h264",
                    "vQuality": "720",
                    "aFormat": "mp3"
                    if audio_only else "best",
                    "isAudioOnly": audio_only
                },
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json"
                },
                timeout=30
            )

            if r.status_code == 200:

                dl = r.json().get("url")

                if dl:

                    fname = (
                        f"/tmp/{vid}_audio.mp3"
                        if audio_only
                        else f"/tmp/{vid}_video.mp4"
                    )

                    with requests.get(
                        dl,
                        stream=True,
                        timeout=120
                    ) as rr:

                        with open(fname, "wb") as f:

                            for c in rr.iter_content(
                                1024 * 1024
                            ):

                                if c:
                                    f.write(c)

                    if os.path.getsize(fname) > 50000:
                        return fname, "Video", 0

        except Exception:
            continue

    return None, "Erreur téléchargement", 0


# =========================================================
# VMESS
# =========================================================

def load_vmess():

    try:

        env = os.getenv("VMESS_DATA")

        if env:
            return [
                l.strip()
                for l in env.splitlines()
                if l.strip().startswith("vmess://")
            ]

        if os.path.exists("vmess.txt"):

            with open("vmess.txt", "r") as f:

                return [
                    l.strip()
                    for l in f
                    if l.strip().startswith("vmess://")
                ]

        return []

    except Exception:
        return []


def get_random_vmess(n=5):

    a = load_vmess()

    if not a:
        return None

    return random.sample(
        a,
        min(n, len(a))
    )


# =========================================================
# SCAN
# =========================================================

def get_host_info(host):

    info = {}

    try:
        ip = socket.gethostbyname(host)
        info["ip"] = ip

    except Exception as e:
        info["error"] = str(e)

    return info


def check_port_200(host, ip, port):

    result = {
        "port": port,
        "open": False,
        "status": "FERME",
        "is_200": False,
        "code": 0
    }

    try:

        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        s.settimeout(2)

        if s.connect_ex(
            (ip, int(port))
        ) != 0:

            s.close()
            return result

        s.close()

        result["open"] = True

    except Exception:
        return result

    try:

        for u in [
            f"http://{host}:{port}",
            f"https://{host}:{port}"
        ]:

            try:

                r = requests.get(
                    u,
                    timeout=4,
                    verify=False,
                    headers={
                        "User-Agent": "Mozilla/5.0"
                    }
                )

                result["code"] = r.status_code

                if r.status_code == 200:

                    result["status"] = "200 OK"
                    result["is_200"] = True

                elif r.status_code in [
                    301,
                    302,
                    403,
                    401
                ]:

                    result["status"] = (
                        f"{r.status_code} - VIVANT"
                    )

                    result["is_200"] = True

                else:

                    result["status"] = (
                        f"{r.status_code}"
                    )

                    result["is_200"] = (
                        r.status_code < 500
                    )

                break

            except Exception:
                continue

        if result["code"] == 0 and result["open"]:
            result["status"] = "OUVERT TCP"

    except Exception:
        result["status"] = "OUVERT"

    return result


# =========================================================
# MATCHS DU JOUR
# =========================================================

def get_todays_fixtures():

    fallback = [
        "Man United vs Man City",
        "Levante vs Barcelona",
        "Napoli vs Bologna"
    ]

    try:

        key = os.getenv("API_FOOTBALL_KEY")

        if not key:
            return fallback

        headers = {
            "x-apisports-key": key
        }

        today = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )

        resp = requests.get(
            "https://v3.football.api-sports.io/fixtures",
            params={"date": today},
            headers=headers,
            timeout=15
        )

        data = resp.json()

        fixtures = data.get("response", [])

        big = []

        for f in fixtures:

            league_id = (
                f.get("league", {})
                .get("id", 0)
            )

            if league_id not in [
                39,
                140,
                135,
                78,
                61,
                2,
                3
            ]:
                continue

            home = (
                f.get("teams", {})
                .get("home", {})
                .get("name")
            )

            away = (
                f.get("teams", {})
                .get("away", {})
                .get("name")
            )

            if home and away:

                big.append(
                    f"{home} vs {away}"
                )

        return (
            big[:8]
            if len(big) >= 2
            else fallback
        )

    except Exception:
        return fallback


# =========================================================
# ⭐ EXACT SCORE - CORRIGÉ
# =========================================================

def predict_exact_score(match):

    if not groq_client:

        return (
            f"⚽ {match}\n\n"
            f"🎯 Score exact estimé : 2-1\n"
            f"📊 Confiance estimative : 62%\n\n"
            f"⚠️ Prédiction et non garantie."
        )

    try:

        prompt = f"""
Tu es un analyste de football.

Match demandé :
{match}

Fais une analyse et donne une prédiction de score.

Réponds exactement avec cette structure :

⚽ MATCH
{match}

🎯 SCORE EXACT PRÉDIT
[score]

🏆 RÉSULTAT PRÉDIT
[équipe gagnante, nul ou résultat]

📊 OVER / UNDER 2.5
[réponse]

🤝 BTTS
[Oui ou Non]

📈 CONFIANCE ESTIMATIVE
[pourcentage]

📝 ANALYSE
[analyse courte]

IMPORTANT :
- Il s'agit d'une prédiction.
- Ne présente pas le score comme un résultat réel.
- N'invente pas de score déjà joué.
- Réponds uniquement en français.
"""

        comp = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant spécialisé "
                        "dans l'analyse football."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.4,
            max_tokens=1000
        )

        result = comp.choices[0].message.content

        if not result:
            raise Exception(
                "Réponse Groq vide"
            )

        return result

    except Exception as e:

        print("EXACT ERROR:", e)

        return (
            f"⚽ {match}\n\n"
            f"🎯 SCORE EXACT PRÉDIT : 2-1\n"
            f"📊 CONFIANCE ESTIMATIVE : 62%\n\n"
            f"⚠️ Prédiction automatique, "
            f"pas une garantie."
        )


# =========================================================
# IMAGE DES SCORES
# =========================================================

def create_score_image(t):

    lines = [
        l for l in t.split("\n")
        if "vs" in l.lower()
    ][:10]

    if not lines:
        lines = [
            "Man Utd vs Man City => 2-1 (62%)"
        ]

    W = 950
    H = 140 + len(lines) * 65

    img = Image.new(
        "RGB",
        (W, H),
        (15, 23, 42)
    )

    draw = ImageDraw.Draw(img)

    try:

        f1 = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/"
            "DejaVuSans-Bold.ttf",
            32
        )

        f2 = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/"
            "DejaVuSans-Bold.ttf",
            20
        )

    except Exception:

        f1 = f2 = ImageFont.load_default()

    draw.text(
        (30, 20),
        f"SCORES {datetime.datetime.now().strftime('%d/%m/%Y')}",
        fill=(255, 255, 255),
        font=f1
    )

    y = 110

    for line in lines:

        m = re.search(
            r"(\d+)\s*-\s*(\d+)",
            line
        )

        if not m:
            continue

        s1 = int(m.group(1))
        s2 = int(m.group(2))

        teams = (
            line.split("=>")[0]
            .strip()[:48]
        )

        draw.text(
            (30, y),
            teams,
            fill=(255, 255, 255),
            font=f2
        )

        draw.text(
            (700, y),
            f"{s1} - {s2}",
            fill=(96, 165, 250),
            font=f1
        )

        y += 60

    p = "/tmp/scores.png"

    img.save(p)

    return p


# =========================================================
# /START
# =========================================================

async def start(update, context):

    save_user(
        update.effective_user.id
    )

    await update.message.reply_text(
        to_3d(
            f"Je suis {SIGNATURE}\n"
            f"📸 Photo\n"
            f"📥 Lien YT/TikTok\n"
            f"🎯 /exact Team vs Team\n"
            f"🔥 /today\n"
            f"🔍 /scan host\n"
            f"📚 /pdf sujet\n"
            f"🔐 /vmess /stats"
        )
    )


# =========================================================
# /STATS
# =========================================================

async def stats_cmd(update, context):

    save_user(
        update.effective_user.id
    )

    await update.message.reply_text(
        f"Total: {get_total_users()}\n"
        f"{SIGNATURE}"
    )


# =========================================================
# /VMESS
# =========================================================

async def vmess_cmd(update, context):

    save_user(
        update.effective_user.id
    )

    s = get_random_vmess(5)

    if not s:

        await update.message.reply_text(
            "Aucun serveur"
        )

        return

    await update.message.reply_text(
        "VMESS\n\n"
        + "\n\n".join(s)
        + f"\n\n{SIGNATURE}"
    )


# =========================================================
# /PDF
# =========================================================

async def pdf_cmd(update, context):

    save_user(
        update.effective_user.id
    )

    if not context.args:

        await update.message.reply_text(
            "📚 /pdf + sujet\n"
            "Ex: /pdf guide business"
        )

        return

    sujet = " ".join(context.args)

    await update.message.reply_text(
        f"📚 Generation livre: {sujet}... 20s"
    )

    try:

        if not groq_client:
            raise Exception(
                "GROQ_API_KEY manquante"
            )

        prompt = (
            f"Ecris un livre complet en francais "
            f"sur: {sujet}. "
            f"5 chapitres, intro, conclusion, "
            f"conseils. 1500 mots minimum."
        )

        comp = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=4000
        )

        contenu = comp.choices[0].message.content

        loop = asyncio.get_event_loop()

        pdf_path = await loop.run_in_executor(
            None,
            create_pdf_book,
            sujet,
            contenu
        )

        if pdf_path and os.path.exists(pdf_path):

            with open(pdf_path, "rb") as f:

                await context.bot.send_document(
                    update.effective_chat.id,
                    document=f,
                    filename=f"{sujet[:20]}.pdf",
                    caption=to_3d(
                        f"Livre: {sujet}\n"
                        f"{SIGNATURE}"
                    )
                )

            os.remove(pdf_path)

        else:

            await update.message.reply_text(
                contenu[:4000]
            )

    except Exception as e:

        await update.message.reply_text(
            f"Erreur PDF: {e}"
        )


# =========================================================
# /MTR
# =========================================================

async def mtr_cmd(update, context):

    save_user(
        update.effective_user.id
    )

    if not context.args:

        await update.message.reply_text(
            "📡 /mtr 1.1.1.1 8.8.8.8"
        )

        return

    raw = " ".join(context.args)

    ips = re.findall(
        r"\b\d+\.\d+\.\d+\.\d+\b",
        raw
    )

    ips = list(dict.fromkeys(ips))

    if not ips:

        await update.message.reply_text(
            "Aucune IP"
        )

        return

    loop = asyncio.get_event_loop()

    await update.message.reply_text(
        f"Scan {len(ips)} HOSTS..."
    )

    txt = (
        f"SCAN MTR {len(ips)} HOSTS\n"
    )

    for ip in ips[:15]:

        r = await loop.run_in_executor(
            None,
            check_port_200,
            ip,
            ip,
