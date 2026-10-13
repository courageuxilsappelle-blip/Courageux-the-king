import os, json, re, hashlib, base64
from pathlib import Path

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import unpad
    HAS_CRYPTO = True
except:
    HAS_CRYPTO = False
    AES = None

KEYS = [b"hc_reborn_4", b"hc_reborn___7", b"hc_reborn_7", b"hc_reborn_tester_5"]

def xor_decrypt(data: bytes, password: str):
    pwd = password.encode()
    return bytes([b ^ pwd[i % len(pwd)] for i, b in enumerate(data)])

def _try_extract_json(txt: str):
    m = re.search(r'\{.*\}', txt, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except: pass
    return None

def _aes_try(raw: bytes):
    if not HAS_CRYPTO: return None
    for key_str in KEYS:
        for key_len in [16,32]:
            variants = [
                (key_str * ((key_len // len(key_str))+1))[:key_len],
                hashlib.md5(key_str).digest(),
                hashlib.sha256(key_str).digest()[:key_len]
            ]
            for key in variants:
                for mode in ["ECB","CBC"]:
                    try:
                        if mode=="ECB":
                            cipher=AES.new(key, AES.MODE_ECB)
                            pt=unpad(cipher.decrypt(raw),16)
                        else:
                            if len(raw)<=16: continue
                            iv=raw[:16]
                            cipher=AES.new(key, AES.MODE_CBC, iv)
                            pt=unpad(cipher.decrypt(raw[16:]),16)
                        if b'{' in pt:
                            j=_try_extract_json(pt.decode('utf-8','ignore'))
                            if j: return j
                    except: continue
    return None

def decrypt(path_or_bytes, password=None):
    if isinstance(path_or_bytes, (str, Path)) and os.path.exists(str(path_or_bytes)):
        raw = Path(path_or_bytes).read_bytes()
    elif isinstance(path_or_bytes, bytes):
        raw = path_or_bytes
    else:
        raw = Path(path_or_bytes).read_bytes()

    # Si mot de passe fourni, dé-XOR d'abord
    if password:
        try:
            raw = xor_decrypt(raw, password)
            # après XOR, le fichier devient hex ou base64
            try:
                txt = raw.decode('utf-8','ignore').strip()
                # si c'est hex
                if all(c in "0123456789abcdefABCDEF" for c in txt[:100]):
                    raw = bytes.fromhex(txt)
                else:
                    txt += '='*(-len(txt)%4)
                    raw = base64.b64decode(txt)
            except:
                pass
        except:
            pass

    # 1. ancien format texte
    try:
        txt = raw.decode('utf-8','ignore')
        j=_try_extract_json(txt)
        if j: return j
        # base64 en boucle
        for _ in range(4):
            txt=txt.strip()
            txt+='='*(-len(txt)%4)
            try:
                d=base64.b64decode(txt)
                s=d.decode('utf-8','ignore')
                j=_try_extract_json(s)
                if j: return j
                txt=s
            except: break
    except: pass

    # 2. nouveau format binaire
    return _aes_try(raw)
