#!/usr/bin/env python3

# ============================
# Script : GBL-Cloud-243 Decryptor
# Code by : @bonyml
# ============================

import argparse
import base64
import hashlib
import json
import sys
import urllib.request
import urllib.error

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


# ============================================================
# CONFIGURATION
# ============================================================

URL_CUSTOM = (
    "https://raw.githubusercontent.com/"
    "Patrick07846/AppTns1/refs/heads/main/App1"
)

URL_FREE = URL_CUSTOM
URL_PREMIUM = URL_FREE

AES_MODE = "AES/CBC/PKCS5Padding"
CHARSET = "UTF-8"
HASH_ALGORITHM = "SHA-256"
KEY_ALGORITHM = "AES"

ERROR_PREFIX = "Error on getting data: "
ERROR_MARKER = "Error al obtener datos"

# Clé de déchiffrement de la configuration principale.
DECRYPTION_KEY = "tns243custom-vip"

# Clé utilisée par ServersActivity pour les champs serveur.
SERVER_FIELD_KEY = "Key: =Kenova_code"

# Alphabet personnalisé obtenu par StringFog.decrypt().
SYMBOLS = (
    "!?-="
    "\u2206\u00d7\u00f7"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789+/"
)[:65]


# ============================================================
# BASE64 PERSONNALISÉ
# ============================================================

def custom_base64_decode(value: str) -> bytes:
    """Convertit le Base64 personnalisé en Base64 standard."""

    translated = []

    for char in value.strip():
        if char.isspace():
            continue

        index = SYMBOLS.find(char)

        if index < 0 or index > 64:
            raise ValueError(
                f"Caractère absent de l'alphabet personnalisé : {char!r}"
            )

        if index < 26:
            translated.append(chr(index + 65))
        elif index < 52:
            translated.append(chr(index + 71))
        elif index < 62:
            translated.append(chr(index - 4))
        elif index == 62:
            translated.append("+")
        elif index == 63:
            translated.append("/")
        else:
            translated.append("=")

    return base64.b64decode(
        "".join(translated),
        validate=False,
    )


def custom_base64_encode(data: bytes) -> str:
    """Convertit le Base64 standard en Base64 personnalisé."""

    standard = base64.b64encode(data).decode("ascii")
    result = []

    for char in standard:
        if "A" <= char <= "Z":
            result.append(SYMBOLS[ord(char) - 65])

        elif "a" <= char <= "z":
            result.append(SYMBOLS[ord(char) - 71])

        elif "0" <= char <= "9":
            result.append(SYMBOLS[ord(char) + 4])

        elif char == "+":
            result.append(SYMBOLS[62])

        elif char == "/":
            result.append(SYMBOLS[63])

        elif char == "=":
            result.append(SYMBOLS[64])

        else:
            raise ValueError(
                f"Caractère Base64 inattendu : {char!r}"
            )

    return "".join(result)


# ============================================================
# AES Encrypt - Decrypt
# ============================================================

def generate_key(password: str) -> bytes:
    """Génère la clé AES à partir du SHA-256 du mot de passe."""

    return hashlib.sha256(
        password.encode(CHARSET)
    ).digest()


def decrypt_data(password: str, encrypted_text: str) -> str:
    """
    Déchiffre une chaîne avec :
      - SHA-256 comme dérivation de clé ;
      - AES-256-CBC ;
      - un IV de 16 octets nuls ;
      - un padding PKCS5/PKCS7.
    """

    encrypted_bytes = custom_base64_decode(encrypted_text)

    if not encrypted_bytes:
        raise ValueError("Données chiffrées vides")

    if len(encrypted_bytes) % AES.block_size != 0:
        raise ValueError("Longueur AES invalide")

    cipher = AES.new(
        generate_key(password),
        AES.MODE_CBC,
        iv=bytes(16),
    )

    plaintext = cipher.decrypt(encrypted_bytes)
    plaintext = unpad(
        plaintext,
        AES.block_size,
        style="pkcs7",
    )

    return plaintext.decode(CHARSET)


def encrypt_data(password: str, plaintext: str) -> str:
    """Chiffre un texte et renvoie son Base64 personnalisé."""

    cipher = AES.new(
        generate_key(password),
        AES.MODE_CBC,
        iv=bytes(16),
    )

    encrypted = cipher.encrypt(
        pad(
            plaintext.encode(CHARSET),
            AES.block_size,
            style="pkcs7",
        )
    )

    return custom_base64_encode(encrypted)


# ============================================================
# VALIDATION DU TEXTE DÉCHIFFRÉ
# ============================================================

def is_valid_plaintext(value: str) -> bool:
    """
    Vérifie que le texte est exploitable.

    Cette validation écarte les caractères de contrôle inattendus.
    Elle ne garantit pas, à elle seule, que la bonne clé a été utilisée.
    """

    if not value:
        return False

    if any(
        ord(char) < 32 and char not in "\r\n\t"
        for char in value
    ):
        return False

    return True


# ============================================================
# DÉCHIFFREMENT RÉCURSIF DES OBJETS JSON
# ============================================================

def recursive_decrypt(
    value,
    passwords=None,
    max_depth=50,
    _depth=0,
    _stats=None,
):
    """
    Parcourt récursivement les dictionnaires, listes et chaînes.

    Pour chaque chaîne :
      1. Essaie les clés candidates dans l'ordre.
      2. Conserve la valeur originale si le déchiffrement échoue.
      3. Si le résultat est un JSON valide, parcourt ce JSON.
      4. Sinon, retourne le texte déchiffré.

    Les nombres, booléens et valeurs nulles sont conservés.
    """

    if passwords is None:
        passwords = [DECRYPTION_KEY]

    elif isinstance(passwords, str):
        passwords = [passwords]

    if _stats is None:
        _stats = {
            "decrypted": 0,
            "failed": 0,
            "json_parsed": 0,
        }

    if _depth >= max_depth:
        return value

    # Dictionnaires : traiter chaque valeur.
    if isinstance(value, dict):
        return {
            key: recursive_decrypt(
                item,
                passwords=passwords,
                max_depth=max_depth,
                _depth=_depth + 1,
                _stats=_stats,
            )
            for key, item in value.items()
        }

    # Listes : traiter chaque élément.
    if isinstance(value, list):
        return [
            recursive_decrypt(
                item,
                passwords=passwords,
                max_depth=max_depth,
                _depth=_depth + 1,
                _stats=_stats,
            )
            for item in value
        ]

    # Ne pas traiter les nombres, booléens, null ou chaînes vides.
    if not isinstance(value, str) or not value.strip():
        return value

    candidate = value.strip()

    # Essayer successivement les clés candidates.
    for password in passwords:
        try:
            plaintext = decrypt_data(password, candidate)

        except Exception:
            continue

        if not is_valid_plaintext(plaintext):
            continue

        _stats["decrypted"] += 1

        # Si le résultat est du JSON, analyser son contenu.
        try:
            nested = json.loads(plaintext)

        except (json.JSONDecodeError, ValueError):
            return plaintext

        _stats["json_parsed"] += 1

        return recursive_decrypt(
            nested,
            passwords=passwords,
            max_depth=max_depth,
            _depth=_depth + 1,
            _stats=_stats,
        )

    # Aucune clé n'a permis un déchiffrement exploitable.
    _stats["failed"] += 1
    return value


# ============================================================
# DÉCHIFFREMENT EXPLICITE DES CHAMPS SERVEUR
# ============================================================

SERVER_FIELDS = (
    "ServerIP",
    "ProxyIP",
    "ProxyPort",
    "ServerUser",
    "ServerPass",
    "ServerPort",
    "SSLPort",
    "Payload",
    "SNI",
    "Slowchave",
    "Nameserver",
    "Slowdns",
    "udpserver",
    "udpauth",
    "udpobfs",
    "udpbuffer",
    "udpdown",
    "udpup",
    "v2rayJson",
)


def decrypt_server_fields(value, max_depth=50, _depth=0, _stats=None):
    """
    Déchiffre explicitement les champs connus de ServersActivity
    avec SERVER_FIELD_KEY.

    Parcourt également les listes et les structures JSON imbriquées.
    Les champs absents et les valeurs non textuelles sont conservés.
    """

    if _stats is None:
        _stats = {
            "decrypted": 0,
            "failed": 0,
        }

    if _depth >= max_depth:
        return value

    if isinstance(value, list):
        return [
            decrypt_server_fields(
                item,
                max_depth=max_depth,
                _depth=_depth + 1,
                _stats=_stats,
            )
            for item in value
        ]

    if not isinstance(value, dict):
        return value

    result = {}

    for key, item in value.items():
        if key in SERVER_FIELDS and isinstance(item, str) and item.strip():
            try:
                plaintext = decrypt_data(
                    SERVER_FIELD_KEY,
                    item.strip(),
                )

                if is_valid_plaintext(plaintext):
                    result[key] = plaintext
                    _stats["decrypted"] += 1
                else:
                    result[key] = item
                    _stats["failed"] += 1

            except Exception:
                result[key] = item
                _stats["failed"] += 1

        elif isinstance(item, (dict, list)):
            result[key] = decrypt_server_fields(
                item,
                max_depth=max_depth,
                _depth=_depth + 1,
                _stats=_stats,
            )

        else:
            result[key] = item

    return result


# ============================================================
# TÉLÉCHARGEMENT DE LA CONFIGURATION
# ============================================================

def download_config(url: str) -> str:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:
            lines = response.read().decode(CHARSET).splitlines()

            # Correspond au comportement Java qui concatène les lignes.
            return "".join(lines)

    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
    ) as exc:
        return ERROR_PREFIX + str(exc)


def update_config(mode: str) -> str:
    urls = {
        "custom": URL_CUSTOM,
        "free": URL_FREE,
        "premium": URL_PREMIUM,
    }

    response = download_config(urls[mode])

    if response.startswith(ERROR_PREFIX):
        raise RuntimeError(response)

    if ERROR_MARKER in response:
        raise RuntimeError(response)

    try:
        return decrypt_data(DECRYPTION_KEY, response)

    except Exception as exc:
        raise RuntimeError(
            "Échec du déchiffrement de la réponse distante."
        ) from exc


# ============================================================
# INTERFACE 
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Télécharge, déchiffre et analyse une configuration JSON."
        )
    )

    parser.add_argument(
        "--mode",
        choices=("custom", "free", "premium"),
        default="free",
        help="Type de configuration distante à télécharger.",
    )

    parser.add_argument(
        "--encrypt-test",
        metavar="TEXTE",
        help="Chiffre un texte avec la clé principale.",
    )

    parser.add_argument(
        "--recursive-decrypt",
        action="store_true",
        help="Déchiffre récursivement les chaînes du JSON.",
    )

    parser.add_argument(
        "--server-fields",
        action="store_true",
        help=(
            "Déchiffre aussi les champs serveur connus "
            "avec Key: =Kenova_code."
        ),
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=50,
        help="Profondeur maximale du parcours récursif.",
    )

    parser.add_argument(
        "--input-json",
        metavar="FICHIER",
        help="Utilise un fichier JSON local au lieu du serveur.",
    )

    args = parser.parse_args()

    if args.max_depth < 1:
        parser.error("--max-depth doit être supérieur ou égal à 1")

    if args.encrypt_test is not None:
        print(
            encrypt_data(
                DECRYPTION_KEY,
                args.encrypt_test,
            )
        )
        return

    try:
        # Charger la configuration.
        if args.input_json:
            with open(
                args.input_json,
                "r",
                encoding=CHARSET,
            ) as file:
                data = json.load(file)

        else:
            result = update_config(args.mode)
            data = json.loads(result)

        # Déchiffrement récursif générique.
        if args.recursive_decrypt:
            stats = {
                "decrypted": 0,
                "failed": 0,
                "json_parsed": 0,
            }

            data = recursive_decrypt(
                data,
                passwords=[
                    DECRYPTION_KEY,
                    SERVER_FIELD_KEY,
                ],
                max_depth=args.max_depth,
                _stats=stats,
            )

            print(
                "[Récursivité] "
                f"déchiffrés={stats['decrypted']}, "
                f"échecs={stats['failed']}, "
                f"JSON analysés={stats['json_parsed']}",
                file=sys.stderr,
            )

        # Déchiffrement ciblé des champs serveur.
        if args.server_fields:
            stats = {
                "decrypted": 0,
                "failed": 0,
            }

            data = decrypt_server_fields(
                data,
                max_depth=args.max_depth,
                _stats=stats,
            )

            print(
                "[Champs serveur] "
                f"déchiffrés={stats['decrypted']}, "
                f"échecs={stats['failed']}",
                file=sys.stderr,
            )

        # Afficher le JSON final.
        print(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False,
            )
        )

    except Exception as exc:
        print(
            f"Erreur : {exc}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
