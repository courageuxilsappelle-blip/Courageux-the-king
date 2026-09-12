import os, threading, requests, datetime
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
SIGNATURE = "COURAGEUX THE KING"

def to_3d(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    bold3d = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
    res = ""
    for c in text:
        if c in normal:
            try: res += bold3d[normal.index(c)]
            except: res += c
        else: res += c
    return res

def get_real_scores():
    """API ESPN gratuite - VRAIS scores, pas besoin de clé"""
    leagues = ["eng.1", "esp.1", "ger.1", "ita.1", "fra.1", "uefa.champions"]
    all_matches = []

    for league in leagues:
        try:
            url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
            r = requests.get(url, timeout=8)
            data = r.json()
            for event in data.get("events", [])[:3]:
                name = event.get("name", "")
                status = event.get("status", {}).get("type", {}).get("description", "")
                comp = event.get("competitions", [{}])[0]
                home = comp.get("competitors", [{}])[0].get("team", {}).get("displayName", "")
                away = comp.get("competitors", [{}])[1].get("team", {}).get("displayName", "") if len(comp.get("competitors", []))>1 else ""
                score_home = comp.get("competitors", [{}])[0].get("score", "")
                score_away = comp.get("competitors", [{}])[1].get("score", "") if len(comp.get("competitors", []))>1 else ""

                if score_home!= "" and score_away!= "":
                    all_matches.append(f"🔴 LIVE {name}: {home} {score_home}-{score_away} {away} ({status})")
                else:
                    all_matches.append(f"⚽ {name}: {home} vs {away} - {status}")
        except:
            continue

    if not all_matches:
        # Secours si ESPN bug
        return "Matchs du jour: Premier League, La Liga, Serie A, Bundesliga, Ligue 1 - Donne les meilleurs affiches de ce week-end"

    return "\n".join(all_matches[:15])

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot REAL SCORE OK"

async def start(update: Update, context):
    conversations[update.effective_user.id] = []
    msg = f"Je suis {SIGNATURE} 👑\nBot avec VRAIS SCORES EN DIRECT!\n\n/score - Vrais scores live\n/coupon - Coupon du jour\n/safe - Coupon safe"
    await update.message.reply_text(to_3d(msg))

async def score_cmd(update: Update, context):
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    scores = get_real_scores()
    await update.message.reply_text(to_3d(f"📊 VRAIS SCORES LIVE:\n\n{scores}\n\n{SIGNATURE}"))

async def coupon_cmd(update: Update, context, typ="normal"):
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    real_data = get_real_scores()

    if typ == "safe":
        instr = "Donne 1 coupon SAFE cote 1.80 avec 2 matchs max ultra sûr"
    elif typ == "combo":
        instr = "Donne 1 gros COMBO cote 10 avec 5 matchs"
    else:
        instr = "Donne 3 coupons: SAFE cote 1.80, NORMAL cote 4, FUN cote 8"

    prompt = f"""
    Tu es {SIGNATURE}, expert paris sportifs.
    Voici les VRAIS matchs / scores actuels:
    {real_data}

    {instr}
    FORMAT:
    🏆 Ligue
    ⚽ Equipe A vs Equipe B
    👉 Pronostic:...
    📊 Confiance: XX% + 1 phrase raison
    💰 Cote: X.XX

    COTE TOTALE à la fin. Utilise seulement des matchs réels.
    """

    try:
        comp = groq_client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role":"user","content":prompt}])
        rep = comp.choices[0].message.content
    except:
        comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"user","content":prompt}])
        rep = comp.choices[0].message.content

    await update.message.reply_text(to_3d(f"{rep}\n\n{SIGNATURE}"))

async def chat_gpt(update: Update, context):
    txt = update.message.text.lower()
    if any(k in txt for k in ["score", "live", "direct"]):
        await score_cmd(update, context); return
    if any(k in txt for k in ["coupon", "pari", "prono", "bet"]):
        await coupon_cmd(update, context); return

    uid = update.effective_user.id
    if uid not in conversations: conversations[uid] = []
    conversations[uid].append({"role":"user","content":txt})
    comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"system","content":f"Tu es {SIGNATURE}. Réponds court."}] + conversations[uid][-10:])
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
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
