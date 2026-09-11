import os, threading, io
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
from PIL import Image

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}
user_data = {} # uid -> {'logo': Image, 'mode': 'logo'}
SIGNATURE = "COURAGEUX THE KING 🔥🔥🔥🔥\nwa.me/243973622250"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot KING LOGO"

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {'logo': None, 'photos': []}
    if uid not in conversations:
        conversations[uid] = []
    return user_data[uid]

async def start(update: Update, context):
    uid = update.effective_user.id
    get_user(uid)
    conversations[uid] = []
    await update.message.reply_text(
        f"👑 {SIGNATURE}\n\n"
        "📸 **MODE LOGO MIX ACTIVÉ**\n\n"
        "1. Envoie ton LOGO en photo (avec fond transparent de préférence PNG)\n"
        "2. Tape /setlogo\n"
        "3. Ensuite chaque photo que tu envoies aura ton LOGO\n\n"
        "Commandes:\n"
        "/setlogo - définir le logo (réponds à la photo du logo)\n"
        "/logo_on - activer le logo\n"
        "/logo_off - désactiver\n"
        "/clear - effacer tout"
    )

async def handle_photo(update: Update, context):
    uid = update.effective_user.id
    udata = get_user(uid)

    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    img = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")

    # Si l'utilisateur n'a pas de logo, on lui demande
    if udata['logo'] is None:
        # On considère cette photo comme logo potentiel
        udata['last_photo'] = img
        await update.message.reply_text(
            f"📸 Photo reçue!\n"
            f"Si c'est ton LOGO, tape /setlogo\n"
            f"Si c'est une photo à traiter, envoie d'abord ton logo puis /setlogo\n\n{SIGNATURE}"
        )
        return

    # MIXAGE AVEC LOGO
    base = img
    logo = udata['logo']

    # Resize logo à 20% de la largeur de la photo
    base_w, base_h = base.size
    logo_w = int(base_w * 0.22) # 22% de la largeur
    logo_h = int(logo_w * logo.height / logo.width)
    logo_resized = logo.resize((logo_w, logo_h), Image.LANCZOS)

    # Position: bas-droite avec marge
    margin = int(base_w * 0.03)
    pos = (base_w - logo_w - margin, base_h - logo_h - margin)

    # Créer la photo finale
    # Convertir base en RGBA pour la transparence
    if base.mode!= 'RGBA':
        base = base.convert('RGBA')

    final = base.copy()
    final.paste(logo_resized, pos, logo_resized) # avec transparence

    # Convertir en RGB pour envoi JPEG
    final_rgb = Image.new("RGB", final.size, (255,255,255))
    final_rgb.paste(final, mask=final.split()[3])

    bio = io.BytesIO()
    bio.name = "logo_mix.jpg"
    final_rgb.save(bio, 'JPEG', quality=95)
    bio.seek(0)

    await update.message.reply_photo(
        photo=bio,
        caption=f"✅ Photo traitée avec ton LOGO\n👑 {SIGNATURE}"
    )
    # Envoie aussi en document HD
    bio2 = io.BytesIO()
    bio2.name = "HD_logo_mix.png"
    final.save(bio2, 'PNG')
    bio2.seek(0)
    await update.message.reply_document(
        document=bio2,
        filename="HD_logo_mix.png",
        caption=f"📁 Version HD PNG\n{SIGNATURE}"
    )

async def setlogo_command(update: Update, context):
    uid = update.effective_user.id
    udata = get_user(uid)

    if 'last_photo' not in udata or udata['last_photo'] is None:
        await update.message.reply_text(f"❌ Envoie d'abord ton LOGO en photo, puis tape /setlogo en réponse à la photo\n\n{SIGNATURE}")
        return

    # Si le logo est en réponse à un message, on prend la photo du message cité
    if update.message.reply_to_message and update.message.reply_to_message.photo:
        photo_file = await update.message.reply_to_message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()
        logo_img = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")
    else:
        logo_img = udata['last_photo']

    udata['logo'] = logo_img
    await update.message.reply_text(f"✅ LOGO enregistré! Maintenant envoie n'importe quelle photo, je vais mettre ton logo dessus auto.\n\n{SIGNATURE}")
    # Preview du logo
    bio = io.BytesIO()
    bio.name = "logo.png"
    logo_img.save(bio, 'PNG')
    bio.seek(0)
    await update.message.reply_photo(photo=bio, caption=f"Ton logo actuel - {SIGNATURE}")

async def logo_on(update: Update, context):
    uid = update.effective_user.id
    udata = get_user(uid)
    if udata['logo'] is None:
        await update.message.reply_text(f"❌ Pas de logo défini! Envoie logo + /setlogo\n{SIGNATURE}")
    else:
        await update.message.reply_text(f"✅ Mode LOGO activé!\n{SIGNATURE}")

async def clear_command(update: Update, context):
    uid = update.effective_user.id
    user_data[uid] = {'logo': None, 'photos': [], 'last_photo': None}
    conversations[uid] = []
    await update.message.reply_text(f"🗑️ Tout effacé! Renvoie ton logo.\n{SIGNATURE}")

async def chat_gpt(update: Update, context):
    uid = update.effective_user.id
    if uid not in conversations: conversations[uid] = []
    conversations[uid].append({"role":"user","content":update.message.text})
    conversations[uid]=conversations[uid][-20:]
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role":"system","content":f"Tu es {SIGNATURE}"}]+conversations[uid])
    rep = comp.choices[0].message.content
    conversations[uid].append({"role":"assistant","content":rep})
    await update.message.reply_text(f"{rep}\n\n— {SIGNATURE}")

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()
app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setlogo", setlogo_command))
app.add_handler(CommandHandler("logo_on", logo_on))
app.add_handler(CommandHandler("clear", clear_command))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
