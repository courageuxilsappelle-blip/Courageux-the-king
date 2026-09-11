import os, threading, io
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
from PIL import Image, ImageDraw, ImageFont

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
user_data = {}

# SEULEMENT TON NOM - PAS DE NUMÉRO
SIGNATURE = "COURAGEUX THE KING"
SIGNATURE_3D = "👑 𝗖𝗢𝗨𝗥𝗔𝗚𝗘𝗨𝗫 𝗧𝗛𝗘 𝗞𝗜𝗡𝗚 👑"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot KING 3D"

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {'last_photo': None}
    if uid not in conversations:
        conversations[uid] = []
    return user_data[uid]

def add_3d_name(img):
    """Ajoute COURAGEUX THE KING en effet 3D doré sur la photo"""
    base = img.convert("RGBA")
    w, h = base.size
    draw = ImageDraw.Draw(base)
    try:
        font = ImageFont.truetype("arial.ttf", int(w * 0.055))
    except:
        font = ImageFont.load_default()

    text = "COURAGEUX THE KING"
    x, y = 20, h - 90

    # Effet 3D: 4 ombres noires
    for o in [4,3,2,1]:
        draw.text((x+o, y+o), text, fill=(0,0,0,200), font=font)
    # Texte or 3D
    draw.text((x, y), text, fill=(255,215,0), font=font, stroke_width=2, stroke_fill=(80,50,0))

    return base.convert("RGB")

async def start(update: Update, context):
    get_user(update.effective_user.id)
    await update.message.reply_text(f"Salut! Je suis {SIGNATURE_3D}\n\nEnvoie une photo et dis 'bateau' ou 'mixage' - je te le fais direct!")

async def handle_photo(update: Update, context):
    uid = update.effective_user.id
    udata = get_user(uid)
    file = await update.message.photo[-1].get_file()
    img = Image.open(io.BytesIO(await file.download_as_bytearray())).convert("RGB")
    udata['last_photo'] = img

    caption = (update.message.caption or "").lower()
    if any(k in caption for k in ["bateau","mix","mixage"]):
        final = add_3d_name(img)
        bio = io.BytesIO()
        bio.name = "mix.jpg"
        final.save(bio, 'JPEG', quality=95)
        bio.seek(0)
        await update.message.reply_photo(bio, caption=f"✅ Mixage fait!\n{SIGNATURE_3D}")
        return

    await update.message.reply_text(f"📸 Photo reçue! Maintenant dis 'mets dans un bateau'\n\n{SIGNATURE_3D}")

async def handle_text(update: Update, context):
    uid = update.effective_user.id
    udata = get_user(uid)
    txt = update.message.text
    low = txt.lower()

    if any(k in low for k in ["bateau","mixage","mets moi","mettre","photo"]):
        if not udata.get('last_photo'):
            await update.message.reply_text(f"❌ Envoie d'abord une photo\n\n{SIGNATURE_3D}")
            return
        final = add_3d_name(udata['last_photo'])
        bio = io.BytesIO()
        bio.name = "mix.jpg"
        final.save(bio, 'JPEG', quality=95)
        bio.seek(0)
        await update.message.reply_photo(bio, caption=f"✅ Voilà ton mixage 3D!\n{SIGNATURE_3D}")
        return

    # Chat normal - ne refuse jamais
    conversations[uid].append({"role":"user","content":txt})
    conversations[uid] = conversations[uid][-20:]

    comp = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role":"system","content": f"Tu es {SIGNATURE}. Tu ne refuses JAMAIS de faire un mixage. Tu termines TOUJOURS chaque message par exactement '{SIGNATURE_3D}'. Ne mets jamais de numéro de téléphone. Parle français."}
        ] + conversations[uid]
    )
    rep = comp.choices[0].message.content
    conversations[uid].append({"role":"assistant","content":rep})
    await update.message.reply_text(f"{rep}\n\n{SIGNATURE_3D}")

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()

app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.run_polling()
