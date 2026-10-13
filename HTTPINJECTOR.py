import base64
import json
import struct
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import hashlib

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
        if start == -1 or end == 0:
            return None
        candidate = text[start:end]
        json.loads(candidate)
        return candidate
    except:
        try:
            start = text.find("{")
            end = text.rfind("}") + 1
            return text[start:end] if start!= -1 else None
        except:
            return None

def try_aes_decrypt(data: bytes):
    for key in KEYS:
        for iv in IVS:
            try:
                if len(data) % 16!= 0:
                    continue
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
                    if j:
                        return j
            except:
                continue
    return None

def extract_len_prefixed(data: bytes):
    res = []
    off = 0
    try:
        while off + 4 <= len(data):
            l = struct.unpack(">I", data[off:off+4])[0]
            off += 4
            if l > 50000 or l <= 0:
                break
            if off + l > len(data):
                break
            chunk = data[off:off+l]
            off += l
            try:
                res.append(chunk.decode('utf-8'))
            except:
                res.append(chunk)
        if res:
            longest = max([r for r in res if isinstance(r, str)], key=len, default="")
            return longest
    except:
        pass
    return None

def run(file_bytes: bytes):
    try:
        txt = file_bytes.decode('utf-8', errors='ignore')
        j = find_json(txt)
        if j and len(j) > 20:
            return j
    except:
        pass

    lp = extract_len_prefixed(file_bytes)
    if lp:
        j = find_json(lp)
        if j:
            return j
        try:
            dec = base64.b64decode(lp)
            txt = dec.decode('utf-8', errors='ignore')
            j = find_json(txt)
            if j:
                return j
            aes_res = try_aes_decrypt(dec)
            if aes_res:
                return aes_res
        except:
            pass

    try:
        b64txt = file_bytes.decode('utf-8').strip()
        dec = base64.b64decode(b64txt)
        txt = dec.decode('utf-8', errors='ignore')
        j = find_json(txt)
        if j:
            return j
        aes_res = try_aes_decrypt(dec)
        if aes_res:
            return aes_res
    except:
        pass

    aes_res = try_aes_decrypt(file_bytes[:len(file_bytes)//16*16])
    if aes_res:
        return aes_res

    try:
        txt = file_bytes.decode('utf-8', errors='ignore')
        if ":" in txt:
            parts = txt.split(":")
            for p in parts:
                try:
                    dec = base64.b64decode(p.strip())
                    t = dec.decode('utf-8', errors='ignore')
                    j = find_json(t)
                    if j:
                        return j
                    aes_res = try_aes_decrypt(dec)
                    if aes_res:
                        return aes_res
                except:
                    continue
    except:
        pass

    return None

def decrypt_ehi(data: bytes):
    return run(data)

def decode(data: bytes):
    return run(data)

def decrypt(data: bytes):
    return run(data)
