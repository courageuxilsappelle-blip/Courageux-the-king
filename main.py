import os, threading, base64, hashlib
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
from cryptography.fernet import Fernet

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- MEMOIRE ---
conversations = {} # {user_id: [{"role":"user", "content":...},...]}
waiting_decrypt = {} # {user_id: fichier_chiffré_bytes}

def get_fernet(password: str):
    key = base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())
    return Fernet(key)

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot IA Courageux en ligne avec mémoire!"

async def start(update: Update, context):
    conversations[update.effective_user.id] = []
    await update.message.reply_text("Je suis Courageux, ton ChatGPT sur Telegram 👑 Je me souviens maintenant de tout! Dis-moi tout!")

async def handle_document(update: Update, context):
    file = await update.message.document.get_file()
    data = await file.download_as_bytearray()
    waiting_decrypt[update.effective_user.id] = bytes(data)
    await update.message.reply_text("Fichier.dark reçu ✅\nEnvoie maintenant le MOT DE PASSE pour le déchiffrer:")

async def chat_gpt(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text

    # Si il attendait un mot de passe pour déchiffrer
    if user_id in waiting_decrypt:
        try:
            fernet = get_fernet(text)
            decrypted = fernet.decrypt(waiting_decrypt[user_id])
            del waiting_decrypt[user_id]
            # Supprime le mot de passe du chat par sécurité
            await update.message.delete()
            await update.message.reply_document(document=decrypted, filename="fichier_dechiffre.dat", caption="Voilà déchiffré ✅ J'ai supprimé ton mot de passe pour ta sécurité.")
            return
        except:
            await update.message.reply_text("Mot de passe incorrect ❌ Réessaye:")
            return

    await context.bot.send_chat_action(update.effective_chat.id, "typing")

    # Crée mémoire si nouvelle personne
    if user_id not in conversations:
        conversations[user_id] = []

    # Ajoute message utilisateur
    conversations[user_id].append({"role": "user", "content": text})

    # Garde seulement les 10 derniers échanges
    if len(conversations[user_id]) > 20:
        conversations[user_id] = conversations[user_id][-20:]

    try:
        # On envoie le system + tout l'historique
        messages_to_groq = [
            {"role": "system", "content": "Tu t'appelles Courageux, tu es un assistant IA très utile, tu parles en français, tu es drôle et intelligent comme ChatGPT. Tu te souviens de la conversation précédente."}
        ] + conversations[user_id]

        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=messages_to_groq
        )
        reponse = completion.choices[0].message.content

        # On garde la réponse dans la mémoire
        conversations[user_id].append({"role": "assistant", "content": reponse})

        await update.message.reply_text(reponse)
    except Exception as e:
        await update.message.reply_text(f"Erreur IA: {e}")

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT",10000))), daemon=True).start()

app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
app.run_polling()
