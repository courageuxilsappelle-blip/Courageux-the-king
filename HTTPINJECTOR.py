import base64
import json
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad

KEYS = [
    hashlib.sha256(b"httpinjector").digest(),
    hashlib.sha256(b"evozi").digest(),
    hashlib.sha256(b"Shutdown key 1234567890123").digest(),
    b"0123456789abcdef0123456789abcdef",
    b"qwertyuiopasdfghjklzxcvbnmqwerty",
]

IVS = [
    b"\x00"*16,
    b"0123456789abcdef",
    bytes.fromhex("0102030405060708090a0b0c0d0e0f10"),
]

def find_json(text: str):
    if not text or "{" not in text:
        return None
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        cand = text[start:end]
        json.loads(cand)
        return cand
    except:
        return None

def try_aes_decrypt(data: bytes):
    if len(data) < 16:
        return None
    data = data[:len(data)//16*16]
    for key in KEYS:
        for iv in IVS:
            try:
                k = key[:32]
                if len(k) not in (16,24,32):
                    k = hashlib.sha256(k).digest()
                cipher = AES.new(k, AES.MODE_CBC, iv)
                pt = cipher.decrypt(data)
                try:
                    pt = unpad(pt, 16)
                except:
                    pass
                txt = pt.decode('utf-8', errors='ignore')
                if "{" in txt:
                    j = find_json(txt)
                    if j and len(j) > 30:
                        return j
            except:
                continue
    return None

def run(file_bytes: bytes):
    # 1 - direct json
    try:
        j = find_json(file_bytes.decode('utf-8', errors='ignore'))
        if j:
            return j
    except:
        pass

    # 2 - format v6.5.0 : payload commence à 441 (après header ehi + version + bloc 417)
    # Ton fichier HHHTO.txt fait 11496 octets, le gros blob est à 441
    offsets_to_try = [441, 20, 24, 0]
    for off in offsets_to_try:
        if off >= len(file_bytes):
            continue
        chunk = file_bytes[off:]
        # test AES direct
        res = try_aes_decrypt(chunk)
        if res:
            return res
        res = try_aes_decrypt(chunk[:8000])
        if res:
            return res
        # test base64 + AES
        try:
            b64_part = chunk[:10000].decode('utf-8', errors='ignore').strip()
            dec = base64.b64decode(b64_part, validate=False)
            j = find_json(dec.decode('utf-8', errors='ignore'))
            if j:
                return j
            res = try_aes_decrypt(dec)
            if res:
                return res
        except:
            pass

    return None

def decrypt_ehi(d): return run(d)
def decode(d): return run(d)
def decrypt(d): return run(d)
