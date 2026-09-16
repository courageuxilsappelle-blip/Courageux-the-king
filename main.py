import os, threading
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- MEMOIRE ---
conversations = {}  # {user_id: [{"role":"user", "content":...},...]}

# Signature 3D seulement - PAS DE NUMÉRO
SIGNATURE_3D = "👑 𝗖𝗢𝗨𝗥𝗔𝗚𝗘𝗨𝗫 𝗧𝗛𝗘 𝗞𝗜𝗡𝗚 👑"

flask_app = Flask(__name__)


@flask_app.route('/')
def home():
    return "Bot IA Courageux en ligne avec mémoire 3D!"


async def start(update: Update, context):
    conversations[update.effective_user.id] = []

    await update.message.reply_text(
        f"Je suis ton ChatGPT sur Telegram {SIGNATURE_3D}\n"
        f"Je me souviens de la conversation! Dis-moi tout!"
    )


# =========================================================
# NOUVELLE COMMANDE /EXACT
# =========================================================

async def exact(update: Update, context):

    if not context.args:
        await update.message.reply_text(
            f"⚽ Utilisation :\n"
            f"/exact Real Madrid vs Olympique\n\n"
            f"{SIGNATURE_3D}"
        )
        return

    match = " ".join(context.args)

    await context.bot.send_chat_action(
        update.effective_chat.id,
        "typing"
    )

    try:

        messages_exact = [
            {
                "role": "system",
                "content": f"""
Tu es {SIGNATURE_3D}, un assistant spécialisé
dans l'analyse des matchs de football.

L'utilisateur va te donner un match.

Analyse le match demandé et donne :

⚽ Match
🎯 Score exact prédit
🏆 Résultat prédit
📊 Over/Under 2.5
🤝 BTTS
📈 Une courte analyse

Le score exact est une PRÉDICTION et non une garantie.
Ne présente jamais une prédiction comme un résultat certain.

Réponds en français.

Termine toujours par :
{SIGNATURE_3D}
"""
            },
            {
                "role": "user",
                "content": f"Analyse ce match : {match}"
            }
        ]

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_exact
        )

        reponse = completion.choices[0].message.content

        await update.message.reply_text(
            reponse
        )

    except Exception as e:

        await update.message.reply_text(
            f"Erreur IA : {e}\n\n{SIGNATURE_3D}"
        )


# =========================================================
# CHAT GPT NORMAL
# =========================================================

async def chat_gpt(update: Update, context):
    user_id = update.effective_user.id
    text = update.message.text

    await context.bot.send_chat_action(
        update.effective_chat.id,
        "typing"
    )

    # Crée mémoire si nouvelle personne
    if user_id not in conversations:
        conversations[user_id] = []

    # Ajoute message utilisateur
    conversations[user_id].append(
        {
            "role": "user",
            "content": text
        }
    )

    # Garde seulement les 10 derniers échanges (20 messages)
    if len(conversations[user_id]) > 20:
        conversations[user_id] = conversations[user_id][-20:]

    try:

        messages_to_groq = [
            {
                "role": "system",
                "content": f"""
Tu t'appelles COURAGEUX THE KING.

Tu es un assistant IA très utile,
tu parles en français,
tu es drôle et intelligent comme ChatGPT.

Tu te souviens de la conversation précédente.

Tu termines TOUJOURS tes messages par :
{SIGNATURE_3D}

Ne mets jamais de numéro de téléphone.
"""
            }
        ] + conversations[user_id]

        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_to_groq
        )

        reponse = completion.choices[0].message.content

        # On garde la réponse dans la mémoire
        conversations[user_id].append(
            {
                "role": "assistant",
                "content": reponse
            }
        )

        await update.message.reply_text(
            f"{reponse}\n\n{SIGNATURE_3D}"
        )

    except Exception as e:

        # Modèle de secours si le premier bug
        try:

            completion = groq_client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=messages_to_groq
            )

            reponse = completion.choices[0].message.content

            conversations[user_id].append(
                {
                    "role": "assistant",
                    "content": reponse
                }
            )

            await update.message.reply_text(
                f"{reponse}\n\n{SIGNATURE_3D}"
            )

        except Exception as e2:

            await update.message.reply_text(
                f"Erreur IA: {e2}\n\n{SIGNATURE_3D}"
            )


# =========================================================
# SERVEUR FLASK
# =========================================================

threading.Thread(
    target=lambda: flask_app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 10000))
    ),
    daemon=True
).start()


# =========================================================
# TELEGRAM
# =========================================================

app = ApplicationBuilder().token(
    os.getenv("TOKEN")
).build()


# Commande /start
app.add_handler(
    CommandHandler("start", start)
)

# Commande /exact AJOUTÉE
app.add_handler(
    CommandHandler("exact", exact)
)

# Messages normaux
app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        chat_gpt
    )
)


# =========================================================
# DÉMARRAGE
# =========================================================

app.run_polling()
