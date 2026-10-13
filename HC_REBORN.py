# HC_REBORN.py - Décodeur pour HTTP Custom 5.x / 2026 (hc_reborn_4)
import os, json, re, hashlib

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_CRYPTO = True
except:
    HAS_CRYPTO = False

KEYS = [b"hc_reborn_4", b"hc_reborn___7", b"hc_reborn_7", b"hc_reborn_tester_5"]

def decrypt(path_or_bytes):
    from pathlib import Path
    if isinstance(path_or_bytes, (str, Path)) and os.path.exists(str(path_or_bytes)):
        raw = Path(path_or_bytes).read_bytes()
    elif isinstance(path_or_bytes, bytes):
        raw = path_or_bytes
    else:
        raw = Path(path_or_bytes).read_bytes()

    if not HAS_CRYPTO:
        return None

    # Nouveau format est binaire AES
    for key_str in KEYS:
        for key_len in [16, 32]:
            # 3 façons de dériver la clé
            key_variants = [
                (key_str * ((key_len // len(key_str))+1))[:key_len],
                hashlib.md5(key_str).digest(),
                hashlib.sha256(key_str).digest()[:key_len]
            ]
            for key in key_variants:
                # Test ECB
                try:
                    cipher = AES.new(key, AES.MODE_ECB)
                    pt = unpad(cipher.decrypt(raw), 16)
                    if b'{' in pt and (b'config' in pt or b'ssh' in pt):
                        txt = pt.decode('utf-8','ignore')
                        m = re.search(r'\{.*\}', txt, re.DOTALL)
                        if m:
                            return json.loads(m.group(0))
                        return json.loads(txt)
                except:
                    pass
                # Test CBC (IV = 16 premiers bytes)
                try:
                    if len(raw) > 16:
                        iv = raw[:16]
                        cipher = AES.new(key, AES.MODE_CBC, iv)
                        pt = unpad(cipher.decrypt(raw[16:]), 16)
                        if b'{' in pt and (b'config' in pt or b'ssh' in pt):
                            txt = pt.decode('utf-8','ignore')
                            m = re.search(r'\{.*\}', txt, re.DOTALL)
                            if m:
                                return json.loads(m.group(0))
                            return json.loads(txt)
                except:
                    pass
    return None