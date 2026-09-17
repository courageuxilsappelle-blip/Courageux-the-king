import os
import re
import json
import base64
import binascii
import asyncio
import hashlib
import struct
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask
from threading import Thread

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

try:
    from Crypto.Cipher import AES
except Exception:
    AES = None

try:
    import msgpack
except Exception:
    msgpack = None


# ============================================================
# CONFIGURATION
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN/TELEGRAM_BOT_TOKEN est manquant.")

# Dark Tunnel
DT_KEY_256 = b"$B&E)H@McQfThWmZq4t7w!z%C*F-JaNd"
DT_KEY_192 = b"F)J@NcRfUjXn2r4u7x!A%D*G"
DT_IV = bytes.fromhex("232e39185523184a5723586242200e05")


# ============================================================
# KEEP-ALIVE FLASK
# ============================================================

app_flask = Flask(__name__)


@app_flask.route("/")
def home():
    return "Bot is running."


def run_flask():
    port = int(os.getenv("PORT", "8080"))
    app_flask.run(host="0.0.0.0", port=port)


def keep_alive():
    Thread(target=run_flask, daemon=True).start()


# ============================================================
# UTILITAIRES
# ============================================================

def _safe_b64decode(value: str) -> bytes:
    value = value.strip()
    value += "=" * (-len(value) % 4)
    return base64.b64decode(value, validate=False)


def _aes_cfb_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    if AES is None:
        raise RuntimeError("PyCryptodome n'est pas installé.")
    cipher = AES.new(key, AES.MODE_CFB, iv=iv, segment_size=128)
    return cipher.decrypt(data)


def _parse_msgpack(data: bytes) -> Any:
    if msgpack is None:
        raise RuntimeError("msgpack n'est pas installé.")
    return msgpack.unpackb(data, raw=False, strict_map_key=False)


def _decrypt_encrypted_fields(obj: Any) -> Any:
    """
    Décode récursivement les structures Dark Tunnel connues.
    Cette fonction concerne uniquement le format Dark Tunnel pris en charge
    par le bot, pas les fichiers EHI.
    """
    if isinstance(obj, dict):
        return {k: _decrypt_encrypted_fields(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_decrypt_encrypted_fields(v) for v in obj]
    return obj


def _normalize_dark_json(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    return {"data": obj}


def decrypt_dark_tunnel_file(path: str) -> Dict[str, Any]:
    """
    Décode le format texte Dark Tunnel attendu par le bot.
    Les EHI ne passent JAMAIS par cette fonction.
    """
    raw = Path(path).read_bytes()

    try:
        text = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise ValueError(
            "Le fichier n'est pas un fichier Dark Tunnel texte UTF-8. "
            "Il s'agit probablement d'un format binaire différent."
        ) from exc

    # Exemple attendu : vpnplus://BASE64(...)
    if "://" not in text:
        raise ValueError("Format Dark Tunnel non reconnu.")

    scheme, payload = text.split("://", 1)
    payload = payload.strip()

    if not payload:
        raise ValueError("Payload Dark Tunnel vide.")

    try:
        encrypted = _safe_b64decode(payload)
    except Exception as exc:
        raise ValueError("Payload Base64 invalide.") from exc

    # Couche AES-CFB 256
    decrypted = _aes_cfb_decrypt(encrypted, DT_KEY_256, DT_IV)

    # Tentative MessagePack
    try:
        obj = _parse_msgpack(decrypted)
    except Exception:
        # Certains fichiers peuvent contenir directement du JSON après
        # la première couche.
        try:
            obj = json.loads(decrypted.decode("utf-8"))
        except Exception as exc:
            raise ValueError(
                "Impossible d'interpréter le contenu Dark Tunnel."
            ) from exc

    obj = _decrypt_encrypted_fields(obj)
    result = _normalize_dark_json(obj)
    result["_scheme"] = scheme
    return result


# ============================================================
# EXTRACTION DE CONFIGS VMESS / TRANSPORT
# ============================================================

def _extract_v2ray_configs(obj: Any) -> list:
    results = []

    def walk(x):
        if isinstance(x, dict):
            # Recherche d'URI courantes
            for key, value in x.items():
                if isinstance(value, str):
                    if value.startswith(("vmess://", "vless://", "trojan://", "ss://")):
                        results.append(value)
                    elif key.lower() in {
                        "vmess", "vless", "trojan", "shadowsocks", "ss"
                    }:
                        results.append(value)
                walk(value)

        elif isinstance(x, list):
            for item in x:
                walk(item)

        elif isinstance(x, str):
            for prefix in ("vmess://", "vless://", "trojan://", "ss://"):
                if prefix in x:
                    pos = x.find(prefix)
                    results.append(x[pos:].split()[0])

    walk(obj)

    # Déduplication
    seen = set()
    unique = []
    for item in results:
        if item not in seen:
            seen.add(item)
            unique.append(item)

    return unique


def _extract_transport_details(obj: Any) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        return {}

    keys = [
        "host",
        "server",
        "address",
        "port",
        "path",
        "sni",
        "tls",
        "network",
        "type",
        "protocol",
    ]

    result = {}
    for key in keys:
        if key in obj:
            result[key] = obj[key]
    return result


def load_vmess(path: str) -> list:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return []
    return _extract_v2ray_configs(data)


def get_random_vmess(configs: list) -> Optional[str]:
    if not configs:
        return None
    import random
    return random.choice(configs)


# ============================================================
# EHI : INSPECTION BINAIRE SANS DÉCHIFFREMENT DE SECRETS
# ============================================================

def inspect_ehi_file(path: str) -> Dict[str, Any]:
    """
    EHI (HTTP Injector) est un conteneur binaire.
    Cette fonction évite l'erreur UTF-8 en ne faisant PAS raw.decode("utf-8").

    Elle renvoie uniquement des métadonnées non sensibles :
      - taille
      - signature/header
      - version lisible si présente
      - aperçu hexadécimal du header

    Elle ne tente pas d'extraire les identifiants, mots de passe, SSH,
    payloads privés ou autres secrets du fichier.
    """
    raw = Path(path).read_bytes()

    header = raw[:128]
    header_hex = header[:32].hex(" ")

    # Recherche prudente d'une version du type 6.5.0 dans le header.
    version_match = re.search(rb"\b\d+\.\d+\.\d+\b", header)
    version = version_match.group(0).decode("ascii", errors="ignore") if version_match else None

    # Plusieurs versions d'EHI commencent par une structure binaire
    # contenant la chaîne "ehi".
    signature_pos = header.find(b"ehi")

    return {
        "size": len(raw),
        "signature": "ehi" if signature_pos >= 0 else None,
        "signature_offset": signature_pos if signature_pos >= 0 else None,
        "version": version,
        "header_hex": header_hex,
    }


# ============================================================
# RÉPONSES TELEGRAM
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Bonjour !\n\n"
        "Envoie-moi un fichier de configuration.\n"
        "Les fichiers EHI sont détectés comme fichiers binaires afin "
        "d'éviter l'erreur UTF-8."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Commandes disponibles :\n"
        "/start - démarrer le bot\n"
        "/help - afficher cette aide\n\n"
        "Formats reconnus : .ehi, .plus, .dark, .hc, .hci"
    )


async def handle_config_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document:
        return

    filename = document.file_name or "config"
    suffix = Path(filename).suffix.lower()

    accepted = {".plus", ".ehi", ".hc", ".hci", ".dark"}

    if suffix not in accepted:
        await update.message.reply_text(
            "❌ Format non pris en charge.\n"
            "Formats : .ehi, .plus, .dark, .hc, .hci"
        )
        return

    tmp_dir = Path("downloads")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", filename)
    path = tmp_dir / safe_name

    try:
        tg_file = await document.get_file()
        await tg_file.download_to_drive(custom_path=str(path))
    except Exception as exc:
        await update.message.reply_text(
            f"❌ Erreur pendant le téléchargement : {exc}"
        )
        return

    # --------------------------------------------------------
    # EHI : traitement binaire séparé
    # --------------------------------------------------------
    if suffix == ".ehi":
        try:
            info = inspect_ehi_file(str(path))

            version_text = info["version"] or "non détectée"
            signature_text = (
                "EHI détecté"
                if info["signature"] == "ehi"
                else "signature EHI non trouvée dans les 128 premiers octets"
            )

            await update.message.reply_text(
                "📦 Fichier EHI détecté\n\n"
                f"📄 Nom : {filename}\n"
                f"📏 Taille : {info['size']} octets\n"
                f"🔖 {signature_text}\n"
                f"📱 Version : {version_text}\n"
                f"🔢 Header : {info['header_hex']}\n\n"
                "ℹ️ Le fichier EHI est binaire : il ne doit pas être "
                "décodé directement avec UTF-8. Le bot évite donc "
                "l'erreur « codec can't decode byte ». "
                "L'extraction de secrets protégés n'est pas effectuée."
            )
        except Exception as exc:
            await update.message.reply_text(
                f"❌ Impossible d'inspecter le fichier EHI : {exc}"
            )
        finally:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
        return

    # --------------------------------------------------------
    # Dark Tunnel
    # --------------------------------------------------------
    if suffix in {".plus", ".dark"}:
        try:
            loop = asyncio.get_running_loop()
            cfg = await loop.run_in_executor(
                None,
                decrypt_dark_tunnel_file,
                str(path),
            )

            vmess = _extract_v2ray_configs(cfg)
            details = _extract_transport_details(cfg)

            message = "✅ Fichier Dark Tunnel traité.\n\n"

            if vmess:
                message += f"🔗 Configurations détectées : {len(vmess)}\n"
            else:
                message += "🔗 Aucune URI VMess/VLESS/Trojan/SS détectée.\n"

            if details:
                message += "\n📋 Informations de transport :\n"
                for key, value in details.items():
                    message += f"• {key}: {value}\n"

            await update.message.reply_text(message)

        except Exception as exc:
            await update.message.reply_text(
                f"❌ Erreur de déchiffrement Dark Tunnel : {exc}"
            )
        finally:
            try:
                path.unlink(missing_ok=True)
            except Exception:
                pass
        return

    # --------------------------------------------------------
    # HC / HCI : ne pas envoyer à un décodeur Dark Tunnel
    # --------------------------------------------------------
    if suffix in {".hc", ".hci"}:
        await update.message.reply_text(
            "📦 Fichier HC/HCI détecté.\n\n"
            "Ce format utilise un conteneur/chiffrement différent de "
            "Dark Tunnel. Il n'est pas envoyé au décodeur EHI/Dark Tunnel "
            "afin d'éviter les erreurs de décodage."
        )

        try:
            path.unlink(missing_ok=True)
        except Exception:
            pass
        return


# ============================================================
# HANDLER TEXTE
# ============================================================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""

    if text.startswith(("vmess://", "vless://", "trojan://", "ss://")):
        await update.message.reply_text(
            "🔗 URI de configuration détectée."
        )
    else:
        await update.message.reply_text(
            "Envoie un fichier de configuration ou utilise /help."
        )


# ============================================================
# MAIN
# ============================================================

def main():
    keep_alive()

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))

    # Tous les documents passent par le routeur qui distingue EHI,
    # Dark Tunnel et les autres formats.
    application.add_handler(
        MessageHandler(filters.Document.ALL, handle_config_file)
    )

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    print("🤖 Bot démarré.")
    application.run_polling()


if __name__ == "__main__":
    main()
