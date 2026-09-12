import os, threading
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
conversations = {}

SIGNATURE = "COURAGEUX THE KING"

# Convertisseur texte normal -> texte 3D
def to_3d(text):
    normal = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    bold3d = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
    # Note: j'ai mis un mapping simple, on garde les accents
    res = ""
    for c in text:
        if c in normal:
            res += bold3d[normal.index(c)]
        else:
            res += c
    return res

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot 3D OK"

async def start(update: Update, context):
    conversations[update.effective_user.id] = []
    msg = f"Je suis {SIGNATURE} 👑 ton ChatGPT sur Telegram! Je me souviens de tout!"
    await update.message.reply_text(to_3d(msg))

async def chat_gpt(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text

    await context.bot.send_chat_action(update.effective_chat.id, "typing")

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({"role": "user", "content": text})
    if len(conversations[user_id]) > 20:
        conversations[user_id] = conversations[user_id][-20:]

    messages_to_groq = [
        {"role": "system", "content": f"Tu t'appelles {SIGNATURE}, assistant IA utile, français, drôle. Ne mets JAMAIS ta signature."}
    ] + conversations[user_id]

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_to_groq
        )
        reponse = completion.choices[0].message.content
    except:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages_to_groq
        )
        reponse = completion.choices[0].message.content

    conversations[user_id].append({"role": "assistant", "content": reponse})

    # TOUT EN 3D - UNE SEULE SIGNATURE
    full_text = f"{reponse}\n\n{SIGNATURE}"
    await update.message.reply_text(to_3d(full_text))

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()

app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
