import json, base64, hashlib
from Crypto.Cipher import AES

def decrypt(path, password=None):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
        
        # Si pas chiffré
        if "data" not in str(data) and "payload" not in str(data).lower():
            # essaie de retourner tel quel
            return data

        # Récupère la partie chiffrée (différentes versions HC)
        enc_b64 = None
        if isinstance(data, dict):
            enc_b64 = data.get('data') or data.get('payload') or data.get('d')
        
        if not enc_b64:
            # fichier non chiffré
            return data

        enc = base64.b64decode(enc_b64)

        if not password:
            return None

        # ESSAIE 1 : password direct en clé AES (16/24/32 bytes paddé)
        # ESSAIE 2 : SHA256(password)
        # ESSAIE 3 : MD5(password)
        tries = []
        pwd_bytes = password.strip().encode()
        tries.append(hashlib.sha256(pwd_bytes).digest()) # le plus courant
        tries.append(hashlib.md5(pwd_bytes).digest())
        tries.append(hashlib.sha256(pwd_bytes.lower()).digest())
        # paddé à 32
        tries.append(pwd_bytes.ljust(32, b'\0')[:32])

        for key in tries:
            try:
                # HC utilise souvent AES CBC avec IV au début ou ECB
                # Try ECB
                cipher = AES.new(key, AES.MODE_ECB)
                dec = cipher.decrypt(enc)
                # enlève padding
                dec = dec.rstrip(b'\x00').rstrip(b'\x08').rstrip(b'\x04').rstrip(b'\x10')
                # essaie PKCS7
                try:
                    pad_len = dec[-1]
                    if pad_len < 32:
                        dec = dec[:-pad_len]
                except: pass
                text = dec.decode('utf-8', errors='ignore')
                if '{' in text and '}' in text:
                    return json.loads(text[text.find('{'):text.rfind('}')+1])
            except: continue

            try:
                # Try CBC IV = 16 premiers bytes de enc
                iv = enc[:16]
                ct = enc[16:]
                cipher = AES.new(key, AES.MODE_CBC, iv)
                dec = cipher.decrypt(ct)
                pad_len = dec[-1]
                if pad_len < 32:
                    dec = dec[:-pad_len]
                text = dec.decode('utf-8', errors='ignore')
                if '{' in text:
                    return json.loads(text[text.find('{'):text.rfind('}')+1])
            except: continue
        
        return None
    except Exception as e:
        print(f"DECRYPT ERROR: {e}")
        return None
