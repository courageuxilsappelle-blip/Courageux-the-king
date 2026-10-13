import os, json, re, hashlib, base64
from pathlib import Path

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_CRYPTO = True
except:
    HAS_CRYPTO = False
    AES = None

KEYS = [b"hc_reborn_4", b"hc_reborn___7", b"hc_reborn_7", b"hc_reborn_tester_5", b"hc_reborn_5"]

def _try_old_format(txt):
    try:
        m = re.search(r'\{.*\}', txt, re.DOTALL)
        if m:
            j = json.loads(m.group(0))
            if isinstance(j, dict):
                return j
        # base64 old
        for _ in range(5):
            txt = txt.strip()
            txt += '=' * (-len(txt) % 4)
            try:
                d = base64.b64decode(txt)
                s = d.decode('utf-8','ignore')
                if '{' in s:
                    m = re.search(r'\{.*\}', s, re.DOTALL)
                    if m:
                        return json.loads(m.group(0))
                txt = s
            except:
                break
    except:
        pass
    return None

def _try_new_aes(raw):
    if not HAS_CRYPTO:
        return None
    for key_str in KEYS:
        for key_len in [16, 24, 32]:
            variants = [
                (key_str * ((key_len // len(key_str))+1))[:key_len],
                hashlib.md5(key_str).digest(),
                hashlib.sha256(key_str).digest()[:key_len]
            ]
            for key in variants:
                # ECB
                try:
                    cipher = AES.new(key, AES.MODE_ECB)
                    pt = unpad(cipher.decrypt(raw), 16)
                    if b'{' in pt:
                        t = pt.decode('utf-8','ignore')
                        m = re.search(r'\{.*\}', t, re.DOTALL)
                        if m:
                            return json.loads(m.group(0))
                except: pass
                # CBC avec IV
                try:
                    if len(raw) > 16:
                        iv = raw[:16]
                        cipher = AES.new(key, AES.MODE_CBC, iv)
                        pt = unpad(cipher.decrypt(raw[16:]), 16)
                        if b'{' in pt:
                            t = pt.decode('utf-8','ignore')
                            m = re.search(r'\{.*\}', t, re.DOTALL)
                            if m:
                                return json.loads(m.group(0))
                except: pass
    return None

def decrypt(path_or_bytes):
    if isinstance(path_or_bytes, (str, Path)) and os.path.exists(str(path_or_bytes)):
        raw = Path(path_or_bytes).read_bytes()
    elif isinstance(path_or_bytes, bytes):
        raw = path_or_bytes
    else:
        raw = Path(path_or_bytes).read_bytes()

    # 1. Essaie ancien format (texte)
    try:
        txt = raw.decode('utf-8','ignore')
        old = _try_old_format(txt)
        if old:
            return old
    except: pass

    # 2. Essaie nouveau format (binaire hc_reborn_4) - ton CRGFI.hc
    new = _try_new_aes(raw)
    if new:
        return new

    return None
