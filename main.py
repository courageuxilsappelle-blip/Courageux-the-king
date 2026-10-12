import os, re, requests, threading, datetime, random, base64, socket, time, asyncio, textwrap, json, tempfile, unicodedata, subprocess, hashlib, hmac, struct, sys
from pathlib import Path
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont
import urllib3
import msgpack
urllib3.disable_warnings()

TOKEN = os.getenv("TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
print("=== V25.4 DARK TUNNEL DECODER ===")

try:
    groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
except:
    groq_client = None

conversations = {}
SIGNATURE = "COURAGEUX THE KING"

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"Bot {SIGNATURE} V25.5 DARK TUNNEL LIVE"

threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)), use_reloader=False), daemon=True).start()
time.sleep(1)

USERS_FILE = "users.txt"
def save_user(uid):
    try:
        if not os.path.exists(USERS_FILE):
            open(USERS_FILE,"w").close()
        with open(USERS_FILE,"r") as f:
            d = f.read()
        if str(uid) not in d:
            with open(USERS_FILE,"a") as f:
                f.write(f"{uid}\n")
    except:
        pass

def get_total_users():
    try:
        with open(USERS_FILE,"r") as f:
            return len([l for l in f if l.strip()])
    except:
        return 0

def to_3d(t):
    try:
        n = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        b = "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
        return "".join([b[n.index(c)] if c in n else c for c in t])
    except:
        return t

def create_pdf_book(title, content):
    try:
        pages = []
        W, H = 800, 1100
        wrapper = textwrap.TextWrapper(width=70)
        img = Image.new("RGB", (W, H), (255,255,255))
        draw = ImageDraw.Draw(img)
        try:
            f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
            f_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
        except:
            f_title = f_text = ImageFont.load_default()
        draw.text((50, 400), title[:30], fill=(0,0,0), font=f_title)
        draw.text((50, 500), f"Par {SIGNATURE}", fill=(100,100,100), font=f_text)
        pages.append(img)
        words = wrapper.wrap(content)
        for i in range(0, len(words), 35):
            img = Image.new("RGB", (W, H), (255,255,255))
            draw = ImageDraw.Draw(img)
            y = 50
            for line in words[i:i+35]:
                draw.text((50, y), line, fill=(0,0,0), font=f_text)
                y += 28
            pages.append(img)
        pdf_path = f"/tmp/{title[:15].replace(' ','_')}.pdf"
        pages[0].save(pdf_path, "PDF", resolution=100.0, save_all=True, append_images=pages[1:])
        return pdf_path
    except Exception as e:
        print(f"PDF Error {e}")
        return None

def clean_url(u):
    return u.strip().split('?is=')[0].split('&is=')[0].split('?si=')[0]

def get_yt_id(u):
    m = re.search(r'(?:v=|be/|shorts/|embed/)([A-Za-z0-9_-]{11})', u)
    return m.group(1) if m else None

def is_link(t):
    return any(x in t.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com","fb.watch","facebook.com"])

def load_vmess():
    try:
        env = os.getenv("VMESS_DATA")
        if env:
            return [l.strip() for l in env.splitlines() if l.strip().startswith("vmess://")]
        if os.path.exists("vmess.txt"):
            with open("vmess.txt","r") as f:
                return [l.strip() for l in f if l.strip().startswith("vmess://")]
        return []
    except:
        return []

def get_random_vmess(n=5):
    a = load_vmess()
    return random.sample(a, min(n,len(a))) if a else None

def get_host_info(host):
    info = {}
    try:
        ip = socket.gethostbyname(host)
        info["ip"] = ip
    except Exception as e:
        info["error"] = str(e)
    return info

def check_blacklist_dns(ip):
    blacklists = [
        "zen.spamhaus.org",
        "bl.spamcop.net",
        "b.barracudacentral.org",
        "proxy.bl.gweep.ca",
        "dnsbl.sorbs.net",
        "all.s5h.net",
        "cbl.abuseat.org"
    ]
    try:
        reversed_ip = ".".join(reversed(ip.split(".")))
        listed = []
        clean = 0
        for bl in blacklists:
            try:
                query = f"{reversed_ip}.{bl}"
                socket.gethostbyname(query)
                listed.append(bl)
            except socket.gaierror:
                clean += 1
            except:
                pass
        return listed, clean, len(blacklists)
    except:
        return [], 0, 7

def check_port_200(host, ip, port):
    result = {"port":port,"open":False,"status":"FERME","is_200":False,"code":0}
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        if s.connect_ex((ip, int(port)))!= 0:
            s.close()
            return result
        s.close()
        result["open"] = True
    except:
        return result
    try:
        for u in [f"http://{host}:{port}", f"https://{host}:{port}"]:
            try:
                r = requests.get(u, timeout=4, verify=False, headers={"User-Agent":"Mozilla/5.0"})
                result["code"] = r.status_code
                if r.status_code == 200:
                    result["status"] = "200 OK"
                    result["is_200"] = True
                elif r.status_code in [301,302,403,401]:
                    result["status"] = f"{r.status_code} - VIVANT"
                    result["is_200"] = True
                else:
                    result["status"] = f"{r.status_code}"
                    result["is_200"] = r.status_code < 500
                break
            except:
                continue
        if result["code"] == 0 and result["open"]:
            result["status"] = "OUVERT TCP"
    except:
        result["status"] = "OUVERT"
    return result

def download_video(url, audio_only=False):
    url = clean_url(url)
    vid = get_yt_id(url) or "video"
    for api in ["https://api.cobalt.tools/api/json","https://co.wuk.sh/api/json"]:
        try:
            r = requests.post(api, json={"url":url,"vCodec":"h264","vQuality":"720","aFormat":"mp3" if audio_only else "best","isAudioOnly":audio_only}, headers={"Accept":"application/json","Content-Type":"application/json"}, timeout=30)
            if r.status_code == 200:
                dl = r.json().get("url")
                if dl:
                    fname = f"/tmp/{vid}_{'audio.mp3' if audio_only else 'video.mp4'}"
                    with requests.get(dl, stream=True, timeout=120) as rr:
                        with open(fname,'wb') as f:
                            for c in rr.iter_content(1024*1024):
                                if c:
                                    f.write(c)
                    if os.path.getsize(fname) > 50000:
                        return fname,"Video",0
        except:
            continue
    return None,"Erreur",0

def get_todays_fixtures():
    REAL = ["Man United vs Man City","Levante vs Barcelona","Napoli vs Bologna"]
    try:
        key = os.getenv("API_FOOTBALL_KEY")
        if not key:
            return REAL
        headers = {"x-apisports-key":key}
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        resp = requests.get(f"https://v3.football.api-sports.io/fixtures?date={today}",headers=headers,timeout=15).json()
        fixtures = resp.get("response",[])
        big = []
        for f in fixtures:
            if f.get("league",{}).get("id",0) not in [39,140,135,78,61,2,3]:
                continue
            big.append(f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}")
        return big[:8] if len(big)>=2 else REAL
    except:
        return REAL

def predict_exact_score(match):
    if not groq_client:
        return f"{match} => 2-1 (62%) Buteurs: Haaland"
    try:
        prompt = "Score exact EA FC 26 en francais pour: " + match
        comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.4)
        return comp.choices[0].message.content
    except:
        return f"{match} => 2-1 (62%)"

def create_score_image(t):
    lines = [l for l in t.split("\n") if "vs" in l.lower()][:10]
    if not lines:
        lines = ["Man Utd vs Man City => 2-1 (62%)"]
    W,H = 950,140+len(lines)*65
    img = Image.new("RGB",(W,H),(15,23,42))
    draw = ImageDraw.Draw(img)
    try:
        f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",32)
        f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",20)
    except:
        f1 = f2 = ImageFont.load_default()
    draw.text((30,20),f"SCORES {datetime.datetime.now().strftime('%d/%m/%Y')}",fill=(255,255,255),font=f1)
    y = 110
    for line in lines:
        m = re.search(r'(\d+)\s*-\s*(\d+)',line)
        if not m:
            continue
        s1,s2 = int(m.group(1)),int(m.group(2))
        teams = line.split("=>")[0][:48].strip()
        draw.text((30,y),teams,fill=(255,255,255),font=f2)
        draw.text((700,y),f"{s1} - {s2}",fill=(96,165,250),font=f1)
        y += 60
    p = "/tmp/scores.png"
    img.save(p)
    return p

async def start(update,context):
    save_user(update.effective_user.id)
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE}\n📸 Photo\n📥 Lien YT/TikTok\n🎯 /exact Team vs Team\n🔥 /today\n🔍 /scan host\n📚 /pdf sujet\n🔐 /vmess /stats\n🛡️ /bl ip = blacklist check"))

async def stats_cmd(update,context):
    save_user(update.effective_user.id)
    await update.message.reply_text(f"Total: {get_total_users()}\n{SIGNATURE}")

async def vmess_cmd(update,context):
    save_user(update.effective_user.id)
    s = get_random_vmess(5)
    if not s:
        await update.message.reply_text("Aucun serveur")
        return
    await update.message.reply_text("VMESS\n\n"+"\n\n".join(s)+f"\n\n{SIGNATURE}")

async def pdf_cmd(update,context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("📚 /pdf + sujet Ex: /pdf guide business")
        return
    sujet = " ".join(context.args)
    await update.message.reply_text(f"📚 Generation livre: {sujet}... 20s")
    try:
        prompt = f"Ecris un livre complet en francais sur: {sujet}. 5 chapitres, intro, conclusion, conseils. 1500 mots minimum."
        comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":prompt}],temperature=0.7,max_tokens=4000)
        contenu = comp.choices[0].message.content
        loop = asyncio.get_event_loop()
        pdf_path = await loop.run_in_executor(None, create_pdf_book, sujet, contenu)
        if pdf_path and os.path.exists(pdf_path):
            with open(pdf_path,'rb') as f:
                await context.bot.send_document(update.effective_chat.id, document=f, filename=f"{sujet[:20]}.pdf", caption=to_3d(f"Livre: {sujet}\n{SIGNATURE}"))
            os.remove(pdf_path)
        else:
            await update.message.reply_text(contenu[:4000])
    except Exception as e:
        await update.message.reply_text(f"Erreur PDF: {e}")

async def mtr_cmd(update,context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("📡 /mtr 1.1.1.1 8.8.8.8")
        return
    raw = " ".join(context.args)
    ips = re.findall(r'\b\d+\.\d+\.\d+\.\d+\b', raw)
    ips = list(dict.fromkeys(ips))
    if not ips:
        await update.message.reply_text("Aucune IP")
        return
    loop = asyncio.get_event_loop()
    await update.message.reply_text(f"Scan {len(ips)} HOSTS...")
    txt = f"SCAN MTR {len(ips)} HOSTS\n"
    for ip in ips[:15]:
        r = await loop.run_in_executor(None, check_port_200, ip, ip, 80)
        txt += f"{'OK' if r['is_200'] else 'KO'} {ip}: {r['status']}\n"
    txt += f"\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def scan_cmd(update,context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("🔍 /scan host")
        return
    host = context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, get_host_info, host)
    ip = info.get("ip",host)
    txt = f"TRACE: {host}\nIP: {ip}\n"
    for p in [80,443,8080,1080,3128]:
        r = await loop.run_in_executor(None, check_port_200, host, ip, p)
        txt += f"{p}: {r['status']}\n"
    txt += f"\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def scan200_cmd(update,context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Usage: /scan200 host")
        return
    host = context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, get_host_info, host)
    ip = info.get("ip",host)
    await update.message.reply_text(f"Scan 200 OK {host}...")
    found = []
    for p in [80,443,8080,1080]:
        r = await loop.run_in_executor(None, check_port_200, host, ip, p)
        if r["is_200"]:
            found.append(r)
    txt = f"200 OK: {host} ({ip})\n" + ("\n".join([f"OK {r['port']}: {r['code']}" for r in found]) if found else "Aucun 200 OK")
    txt += f"\n\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def bl_cmd(update,context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("🛡️ Usage: /bl 34.120.159.235")
        return
    ip = context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    try:
        if not re.match(r'^\d+\.\d+\.\d+\.\d+$', ip):
            ip = socket.gethostbyname(ip)
    except:
        pass
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(f"🛡️ Vérif blacklist {ip}... 5s")
    loop = asyncio.get_event_loop()
    listed, clean, total = await loop.run_in_executor(None, check_blacklist_dns, ip)

    if not listed:
        txt = f"✅ IP Not Listed (Good!)\n\nIP: {ip}\n"
        txt += f"Status: PROPRE ✅\n"
        txt += f"Listes checkées: {total}\n"
        txt += f"Propres: {clean}/{total}\n\n"
        txt += f"all.s5h.net: Not Listed\n"
        txt += f"b.barracudacentral.org: Not Listed\n"
        txt += f"bl.spamcop.net: Not Listed\n"
        txt += f"proxy.bl.gweep.ca: Not Listed (pas proxy spam)\n"
        txt += f"\n{SIGNATURE}"
    else:
        txt = f"❌ IP Listed (Bad!)\n\nIP: {ip}\n"
        txt += f"Blacklistée sur {len(listed)}/{total}:\n"
        for bl in listed:
            txt += f"❌ {bl}\n"
        txt += f"\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def exact_cmd(update,context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("🎯 /exact Man City vs Arsenal")
        return
    pred = predict_exact_score(" ".join(context.args))
    try:
        img = create_score_image(pred)
        await context.bot.send_photo(update.effective_chat.id, photo=open(img,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
    except:
        await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))

async def today_cmd(update,context):
    save_user(update.effective_user.id)
    await context.bot.send_chat_action(update.effective_chat.id,"typing")
    ml = get_todays_fixtures()
    pred = "\n".join([f"{m} => 2-1 (62%)" for m in ml])
    if groq_client:
        try:
            liste = "\n".join([f"- {m}" for m in ml])
            comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"user","content":f"Scores EA FC 26 francais:\n{liste}"}],temperature=0.4)
            pred = comp.choices[0].message.content
        except:
            pass
    try:
        img = create_score_image(pred)
        await context.bot.send_photo(update.effective_chat.id, photo=open(img,'rb'), caption=to_3d(f"{pred}\n\n{SIGNATURE}"))
    except:
        await update.message.reply_text(to_3d(f"{pred}\n\n{SIGNATURE}"))

def _normalize_filename(name):
    try:
        return unicodedata.normalize("NFKC", name or "")
    except Exception:
        return name or ""

DT_KEY_256 = b"$B&E)H@McQfThWmZq4t7w!z%C*F-JaNd"
DT_KEY_192 = b"F)J@NcRfUjXn2r4u7x!A%D*G"
DT_IV = bytes.fromhex("232e39185523184a5723586242200e05")

def _b64decode_loose(value):
    if isinstance(value, str):
        value = value.encode("ascii", "ignore")
    value = b"".join(value.split())
    value = value.replace(b"-", b"+").replace(b"_", b"/")
    value += b"=" * (-len(value) % 4)
    return base64.b64decode(value, validate=False)

def _aes_cfb_decrypt(data, key):
    try:
        from Crypto.Cipher import AES
        return AES.new(key, AES.MODE_CFB, iv=DT_IV, segment_size=128).decrypt(data)
    except ImportError:
        with tempfile.NamedTemporaryFile(delete=False) as fi, tempfile.NamedTemporaryFile(delete=False) as fo:
            fi.write(data)
            in_name, out_name = fi.name, fo.name
        try:
            bits = len(key) * 8
            p = subprocess.run(
                [
                    "openssl", "enc", f"-aes-{bits}-cfb", "-d",
                    "-K", key.hex(), "-iv", DT_IV.hex(),
                    "-in", in_name, "-out", out_name
                ],
                capture_output=True, text=True, timeout=15
            )
            if p.returncode!= 0:
                raise RuntimeError(p.stderr.strip() or "OpenSSL AES-CFB a échoué")
            return Path(out_name).read_bytes()
        finally:
            for f in (in_name, out_name):
                try:
                    os.remove(f)
                except Exception:
                    pass

def _try_json_string(value):
    if not isinstance(value, str):
        return value
    stripped = value.strip()
    if not ((stripped.startswith("{") and stripped.endswith("}")) or
            (stripped.startswith("[") and stripped.endswith("]"))):
        return value
    try:
        fixed = re.sub(r'(:\s*)(\$[A-Za-z0-9_]+)', r'\1"\2"', stripped)
        return _normalize_dark_json(json.loads(fixed))
    except Exception:
        return value

def _normalize_dark_json(value):
    if isinstance(value, dict):
        return {k: _normalize_dark_json(v) for k, v in value.items() if k!= "Password"}
    if isinstance(value, list):
        return [_normalize_dark_json(v) for v in value]
    if isinstance(value, bytes):
        try:
            return _try_json_string(value.decode("utf-8"))
        except Exception:
            return list(value)
    if isinstance(value, str):
        return _try_json_string(value)
    return value

def _decrypt_encrypted_fields(obj, key):
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if isinstance(k, str) and k.startswith("Encrypted") and isinstance(v, (bytes, bytearray)):
                try:
                    result[k] = _aes_cfb_decrypt(bytes(v), key)
                except Exception:
                    result[k] = v
            else:
                result[k] = _decrypt_encrypted_fields(v, key)
        return result
    if isinstance(obj, list):
        return [_decrypt_encrypted_fields(v, key) for v in obj]
    return obj

def _parse_msgpack(data):
    return msgpack.unpackb(data, raw=False, strict_map_key=False)

def decrypt_dark_tunnel_file(path):
    raw = Path(path).read_bytes()
    txt = raw.decode("utf-8-sig", "ignore").strip()
    txt = _normalize_filename(txt)
    if "://" in txt:
        payload = txt.split("://", 1)[1].strip()
    else:
        payload = txt
    if not payload.startswith(("eyJ", "ey")):
        m = re.search(r"(eyJ[A-Za-z0-9_-]+)", payload)
        if m:
            payload = m.group(1)
    outer = json.loads(_b64decode_loose(payload).decode("utf-8"))
    if "encryptedLockedConfig" not in outer:
        raise ValueError("Champ encryptedLockedConfig absent")
    encrypted = _b64decode_loose(outer["encryptedLockedConfig"])
    decrypted_outer = _aes_cfb_decrypt(encrypted, DT_KEY_256)
    unpacked_outer = _parse_msgpack(decrypted_outer)
    if isinstance(unpacked_outer, dict) and isinstance(
        unpacked_outer.get("EncryptedLockedConfig"), (bytes, bytearray)
    ):
        inner = _aes_cfb_decrypt(
            unpacked_outer["EncryptedLockedConfig"], DT_KEY_192
        )
        unpacked_inner = _parse_msgpack(inner)
        unpacked_outer["EncryptedLockedConfig"] = _decrypt_encrypted_fields(
            unpacked_inner, DT_KEY_192
        )
    outer["encryptedLockedConfig"] = unpacked_outer
    return _normalize_dark_json(outer)

def _flatten_config(obj, result=None):
    if result is None:
        result = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = str(k)
            low = key.lower()
            if isinstance(v, (str, int, float, bool)):
                s = str(v)
                if low in ("address", "server", "serveraddress", "server_address"):
                    result.setdefault("address", s)
                elif low in ("port", "serverport", "server_port"):
                    result.setdefault("port", s)
                elif low in ("servername", "server_name", "sni"):
                    result.setdefault("sni", s)
                elif low == "host":
                    result.setdefault("host", s)
                elif low == "path":
                    result.setdefault("path", s)
                elif low in ("network", "transport", "transportnetwork"):
                    result.setdefault("network", s)
                elif low in ("security", "tls"):
                    result.setdefault("security", s)
                elif low in ("protocol", "type"):
                    result.setdefault("protocol", s)
                elif low == "flow":
                    result.setdefault("flow", s)
                elif low == "email":
                    result.setdefault("email", s)
                elif low == "mux":
                    result.setdefault("mux", s)
            elif isinstance(v, (dict, list)):
                _flatten_config(v, result)
    elif isinstance(obj, list):
        for item in obj:
            _flatten_config(item, result)
    return result

def _first_scalar(obj, names):
    wanted = {str(x).lower() for x in names}
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in wanted and isinstance(v, (str, int, float, bool)):
                return v
            found = _first_scalar(v, names)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _first_scalar(item, names)
            if found is not None:
                return found
    return None

def _extract_v2ray_configs(cfg):
    result = []
    seen = set()
    def walk(obj):
        if isinstance(obj, dict):
            if "address" in obj and ("port" in obj or "users" in obj):
                key = (str(obj.get("address")), str(obj.get("port")), str(obj.get("uuid")))
                if key not in seen:
                    seen.add(key)
                    result.append(obj)
            users = obj.get("users")
            if isinstance(users, list):
                for u in users:
                    if isinstance(u, dict):
                        item = dict(u)
                        if "address" not in item and obj.get("address") is not None:
                            item["address"] = obj.get("address")
                        if "port" not in item and obj.get("port") is not None:
                            item["port"] = obj.get("port")
                        result.append(item)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    walk(cfg)
    unique = []
    seen2 = set()
    for x in result:
        key = (
            str(x.get("address")),
            str(x.get("port")),
            str(x.get("id") or x.get("uuid") or x.get("password")),
        )
        if key not in seen2:
            seen2.add(key)
            unique.append(x)
    return unique

def _extract_transport_details(cfg):
    out = {
        "network": _first_scalar(cfg, ["network", "transportNetwork"]),
        "security": _first_scalar(cfg, ["security"]),
        "sni": _first_scalar(cfg, ["serverName", "serverNameIndication", "sni"]),
        "host": _first_scalar(cfg, ["Host", "host"]),
        "path": _first_scalar(cfg, ["path", "wsPath"]),
        "serviceName": _first_scalar(cfg, ["serviceName"]),
        "flow": _first_scalar(cfg, ["flow"]),
        "fingerprint": _first_scalar(cfg, ["fingerprint", "fp"]),
        "publicKey": _first_scalar(cfg, ["publicKey", "pbk"]),
        "shortId": _first_scalar(cfg, ["shortId", "sid"]),
        "allowInsecure": _first_scalar(cfg, ["allowInsecure"]),
        "proxyHost": _first_scalar(cfg, ["proxyHost"]),
        "proxyPort": _first_scalar(cfg, ["proxyPort"]),
        "httpPort": _first_scalar(cfg, ["httpPort"]),
        "socks5Port": _first_scalar(cfg, ["socks5Port"]),
        "allowAccessFromLan": _first_scalar(cfg, ["allowAccessFromLan"]),
    }
    return {k: v for k, v in out.items() if v not in (None, "")}

# === MODULE DECHIFFREMENT HTTP CUSTOM (.hc / .hci) ===
try:
    from Crypto.Cipher import ChaCha20_Poly1305
    CRYPTO_OK = True
except ImportError:
    CRYPTO_OK = False

PKG = b"xyz.easypro.httpcustom"
OUTER_AAD = b"HCX1|xyz.easypro.httpcustom|1"
OUTER_SEED = b"hc-envelope-seal-v1 xyz.easypro.httpcustom"
OUTER_SALT = b"hc-envelope-seal-salt-v1"
OUTER_INFO = b"hc-envelope-seal-info-v1"
OUTER_KEY_V3 = bytes.fromhex("88702df6ae8c089c9478b8cd2bd3f30961b3574a58063d024bdc50f6b779e26f")
N7_HMAC_KEY = bytes.fromhex("9ba7ff3baf33db7aad807a86574b7ca55bef2f048ead51f3a1fe0cff389db3b3")
C0_PREFIX = bytes.fromhex(
    "95dd433d7e4a0be02d55cc62553edcfc8f077fe780be5a7da7f861c2558dc181"
    "38cabb40b2f81a5a30b11a97cbcf0fed755aa8c2b5495e9bc0c1902077a4cd92"
)

class HCError(ValueError):
    pass

def _c0(data: bytes) -> bytes:
    return hashlib.sha256(C0_PREFIX + data).digest()

def _hkdf(ikm: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    out, prev, ctr = b"", b"", 1
    while len(out) < length:
        prev = hmac.new(prk, prev + info + bytes([ctr]), hashlib.sha256).digest()
        out += prev; ctr += 1
    return out[:length]

def _rol(v: int, b: int) -> int:
    return ((v << b) & 0xFFFFFFFF) | (v >> (32 - b))

def _qr(s: List[int], a: int, b: int, c: int, d: int) -> None:
    s[a] = (s[a] + s[b]) & 0xFFFFFFFF; s[d] = _rol(s[d] ^ s[a], 16)
    s[c] = (s[c] + s[d]) & 0xFFFFFFFF; s[b] = _rol(s[b] ^ s[c], 12)
    s[a] = (s[a] + s[b]) & 0xFFFFFFFF; s[d] = _rol(s[d] ^ s[a], 8)
    s[c] = (s[c] + s[d]) & 0xFFFFFFFF; s[b] = _rol(s[b] ^ s[c], 7)

def _rounds(s: List[int]) -> None:
    for _ in range(10):
        _qr(s,0,4,8,12); _qr(s,1,5,9,13); _qr(s,2,6,10,14); _qr(s,3,7,11,15)
        _qr(s,0,5,10,15); _qr(s,1,6,11,12); _qr(s,2,7,8,13); _qr(s,3,4,9,14)

def _hchacha20(key: bytes, nonce16: bytes) -> bytes:
    s = list(struct.unpack("<4I", b"expand 32-byte k") + struct.unpack("<8I", key) + struct.unpack("<4I", nonce16))
    _rounds(s)
    return struct.pack("<8I", s[0],s[1],s[2],s[3],s[12],s[13],s[14],s[15])

def _chacha_block(key: bytes, nonce12: bytes, ctr: int) -> bytes:
    init = list(struct.unpack("<4I", b"expand 32-byte k") + struct.unpack("<8I", key) + (ctr & 0xFFFFFFFF,) + struct.unpack("<3I", nonce12))
    s = init.copy(); _rounds(s)
    return struct.pack("<16I", *((s[i] + init[i]) & 0xFFFFFFFF for i in range(16)))

def _stream_xor(data: bytes, key: bytes, nonce12: bytes, ctr: int = 1) -> bytes:
    out = bytearray(len(data))
    for bn, off in enumerate(range(0, len(data), 64)):
        st = _chacha_block(key, nonce12, ctr + bn)
        for i, v in enumerate(data[off:off+64]): out[off+i] = v ^ st[i]
    return bytes(out)

def _poly1305(msg: bytes, otk: bytes) -> bytes:
    r = int.from_bytes(otk[:16], "little") & 0x0FFFFFFC0FFFFFFC0FFFFFFC0FFFFFFF
    pad = int.from_bytes(otk[16:], "little"); acc = 0; mod = (1 << 130) - 5
    for off in range(0, len(msg), 16):
        acc = ((acc + int.from_bytes(msg[off:off+16] + b"\x01", "little")) * r) % mod
    return ((acc + pad) & ((1 << 128) - 1)).to_bytes(16, "little")

def _pad16(d: bytes) -> bytes:
    return b"" if len(d) % 16 == 0 else b"\x00" * (16 - len(d) % 16)

def _xdec_pure(key: bytes, nonce: bytes, aad: bytes, ct_tag: bytes) -> bytes:
    sub = _hchacha20(key, nonce[:16]); n12 = b"\x00\x00\x00\x00" + nonce[16:]
    ct, tag = ct_tag[:-16], ct_tag[-16:]
    otk = _chacha_block(sub, n12, 0)[:32]
    mac = aad + _pad16(aad) + ct + _pad16(ct) + struct.pack("<Q", len(aad)) + struct.pack("<Q", len(ct))
    if not hmac.compare_digest(_poly1305(mac, otk), tag):
        raise HCError("XChaCha20-Poly1305 auth failed")
    return _stream_xor(ct, sub, n12, 1)

def _xdec(key: bytes, nonce: bytes, aad: bytes, ct_tag: bytes) -> bytes:
    if len(key) != 32 or len(nonce) != 24 or len(ct_tag) < 16:
        raise HCError("bad XChaCha20 input")
    if CRYPTO_OK:
        c = ChaCha20_Poly1305.new(key=key, nonce=nonce); c.update(aad)
        try: return c.decrypt_and_verify(ct_tag[:-16], ct_tag[-16:])
        except ValueError: raise HCError("XChaCha20-Poly1305 auth failed")
    try:
        from nacl.bindings import crypto_aead_xchacha20poly1305_ietf_decrypt
        from nacl.exceptions import CryptoError
        try: return crypto_aead_xchacha20poly1305_ietf_decrypt(ct_tag, aad, nonce, key)
        except CryptoError: raise HCError("XChaCha20-Poly1305 auth failed")
    except ImportError:
        return _xdec_pure(key, nonce, aad, ct_tag)

def _argon2id(pw: bytes, salt: bytes, ops: int, mem: int, length: int = 32) -> bytes:
    if len(salt) != 16: raise HCError("Argon2 salt must be 16 bytes")
    try:
        from nacl.pwhash import argon2id
        return argon2id.kdf(length, pw, salt, opslimit=ops, memlimit=mem)
    except ImportError: pass
    try:
        from argon2.low_level import Type, hash_secret_raw
        return hash_secret_raw(pw, salt, time_cost=ops, memory_cost=mem // 1024, parallelism=1, hash_len=length, type=Type.ID, version=19)
    except ImportError: pass
    try:
        from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
        return Argon2id(salt=salt, length=length, iterations=ops, lanes=1, memory_cost=mem // 1024).derive(pw)
    except (ImportError, AttributeError): pass
    for soname in ["libsodium.so.23", "libsodium.so", "libargon2.so.1", "libargon2.so",
                   "/data/data/com.termux/files/usr/lib/libsodium.so",
                   "/data/data/com.termux/files/usr/lib/libargon2.so"]:
        try:
            lib = ctypes.CDLL(soname)
            if hasattr(lib, "crypto_pwhash"):
                out = (ctypes.c_ubyte * length)()
                if lib.crypto_pwhash(out, ctypes.c_ulonglong(length), pw, ctypes.c_ulonglong(len(pw)), salt,
                                     ctypes.c_ulonglong(ops), ctypes.c_size_t(mem), ctypes.c_int(2)) == 0:
                    return bytes(out)
        except (OSError, AttributeError): continue
    raise RuntimeError("Need pynacl / argon2-cffi / cryptography / libsodium for password-protected files")

def _outer_key() -> bytes:
    return _hkdf(_c0(OUTER_SEED), OUTER_SALT, OUTER_INFO)

def _carriers(data: bytes):
    seen, cur = set(), data
    for _ in range(6):
        if cur in seen: break
        seen.add(cur)
        if len(cur) >= 40: yield cur
        try: text = cur.decode("utf-8")
        except UnicodeDecodeError: break
        if not all(ord(c) <= 0xFF for c in text): break
        nxt = bytes(ord(c) for c in text)
        if nxt == cur: break
        cur = nxt

def _open_outer(data: bytes) -> Dict[str, Any]:
    key = _outer_key(); last_err = None
    for logical in _carriers(data):
        if len(logical) < 40: continue
        try:
            pt = _xdec(key, logical[:24], OUTER_AAD, logical[24:])
            v = json.loads(pt.decode("utf-8"))
            if isinstance(v, dict): return v
        except (HCError, UnicodeDecodeError, json.JSONDecodeError) as e: last_err = e
        try:
            nonce, ct = logical[:24], logical[24:-16]
            sub = _hchacha20(OUTER_KEY_V3, nonce[:16]); n12 = b"\x00\x00\x00\x00" + nonce[16:]
            pt = _stream_xor(ct, sub, n12, 1)
            v = json.loads(pt.decode("utf-8"))
            if isinstance(v, dict) and v.get("a") == "HCCFG": return v
        except (HCError, UnicodeDecodeError, json.JSONDecodeError) as e: last_err = e
    raise HCError("Not a valid HTTP Custom envelope") from last_err

def _validate(env: Dict[str, Any]) -> int:
    if env.get("a") != "HCCFG": raise HCError(f"Bad magic: {env.get('a')!r}")
    schema = int(env.get("b", 0))
    if schema == 1: exp_c, exp_k = "XCHACHA20P1305", "NATIVE-HKDF-SHA256"
    elif schema in (2, 5, 7): exp_c, exp_k = "s1", "h1"
    else: raise HCError(f"Unsupported schema b={schema}")
    if env.get("c") != exp_c: raise HCError(f"Bad cipher: {env.get('c')!r}")
    if env.get("d") != exp_k: raise HCError(f"Bad KDF: {env.get('d')!r}")
    if env.get("e") not in ("n1", "n2", "n7", "n8"): raise HCError(f"Bad schedule: {env.get('e')!r}")
    return schema

def _features(env: Dict[str, Any]) -> bytes:
    f = env.get("f")
    if not isinstance(f, list) or not all(isinstance(x, str) for x in f): raise HCError("Bad features")
    return ",".join(f).encode()

def _n_bytes(env: Dict[str, Any]) -> Optional[bytes]:
    n = env.get("n")
    if n is None or isinstance(n, bool): return None
    ni = int(n)
    if str(ni) != str(n) or ni < 0: raise HCError("Bad n value")
    return str(ni).encode()

def _norm_hwid(hwid: str) -> bytes:
    v = hwid.strip()
    if len(v) != 32: raise HCError("HWID must be 32 chars")
    if any(c not in "0123456789abcdefABCDEFhH" for c in v): raise HCError("Bad HWID chars")
    return v.upper().encode()

def _env_key(env: Dict[str, Any]) -> bytes:
    try: k = bytes.fromhex(env["g"])
    except (KeyError, TypeError, ValueError): raise HCError("Bad inner key")
    if len(k) != 32: raise HCError("Inner key must be 32 bytes")
    return k

def _pw_kdf(env: Dict[str, Any], password: str, ekey: bytes) -> Tuple[bytes, bytes]:
    kdf = env.get("k")
    if kdf not in ("ARGON2ID13", "a1"): raise HCError(f"Bad pw KDF: {kdf!r}")
    try: ops, mem = int(env["l"]), int(env["m"])
    except (KeyError, TypeError, ValueError): raise HCError("Bad Argon2 params")
    pk = _argon2id(password.encode(), ekey[:16], ops, mem)
    return pk, b"|1|ARGON2ID13|" + str(ops).encode() + b"|" + str(mem).encode()

def _h_flag(env: Dict[str, Any]) -> bool:
    h = env.get("h", 0)
    if h not in (0, 1, False, True): raise HCError(f"Bad h flag: {h!r}")
    return bool(h)

def _transcript(env: Dict[str, Any], ekey: bytes, hwid_b: Optional[bytes] = None, n7_mode: bool = False) -> bytes:
    feats = _features(env); nb = _n_bytes(env); vb = b"1"
    t = b"HCCFG\x00" + PKG + b"\x00" + vb + b"\x00" + feats + b"\x00"
    if nb: t += nb + b"\x00"
    if hwid_b is not None: t += b"hwid\x00" + hwid_b + b"\x00"
    t += ekey
    if n7_mode:
        return hmac.new(N7_HMAC_KEY, b"\xd3" + C0_PREFIX[:32] + t, hashlib.sha256).digest()
    return _c0(t)

def _derive(env: Dict[str, Any], password: Optional[str], hwid: Optional[str]) -> Tuple[bytes, bytes]:
    sched = env.get("e"); schema = _validate(env); ekey = _env_key(env)
    feats = _features(env); nb = _n_bytes(env); vb = b"1"
    is_hwid = sched in ("n2", "n8")
    is_n7 = sched in ("n7", "n8")

    if is_hwid and hwid is None:
        raise HCError("HWID_REQUIRED")

    hwid_b = _norm_hwid(hwid) if is_hwid else None
    ikm = _transcript(env, ekey, hwid_b, n7_mode=is_n7)
    protected = _h_flag(env)
    aad_prot = b"|0"

    if protected:
        if password is None:
            raise HCError("PASSWORD_REQUIRED")
        pk, aad_prot = _pw_kdf(env, password, ekey)
        ikm = ikm + pk

    sched_b = sched.encode()
    info = b"app-config|" + sched_b + b"|" + PKG + b"|" + vb + b"|" + feats
    if nb: info += b"|" + nb
    if hwid_b: info += b"|hwid|" + hwid_b
    skey = _hkdf(ikm, ekey, info)

    aad = (b"HCCFG|" + str(schema).encode() + b"|XCHACHA20P1305|NATIVE-HKDF-SHA256|"
           + sched_b + b"|" + PKG + b"|" + vb + b"|" + feats + aad_prot)
    if nb: aad += b"|" + nb

    if is_hwid:
        slots = env.get("o", [])
        if not isinstance(slots, list) or not slots: raise HCError("No HWID key slots")
        for slot in slots:
            if not isinstance(slot, dict): continue
            try:
                nonce = bytes.fromhex(slot["a"]); ct = bytes.fromhex(slot["b"])
                sk = _xdec(skey, nonce, aad + b"\x00w", ct)
                if len(sk) == 32: return sk, aad
            except (HCError, TypeError, ValueError, KeyError): continue
        raise HCError("AUTH_FAILED")

    return skey, aad

class _R:
    def __init__(self, d: bytes): self.d, self.o = d, 0
    def take(self, n: int) -> bytes:
        if self.o + n > len(self.d): raise HCError("Truncated HPC1")
        v = self.d[self.o:self.o+n]; self.o += n; return v
    def u32(self) -> int: return struct.unpack(">I", self.take(4))[0]
    def u64(self) -> int: return struct.unpack(">Q", self.take(8))[0]
    def txt(self) -> str:
        s = self.u32()
        if s > 16*1024*1024: raise HCError("HPC1 string too long")
        return self.take(s).decode("utf-8")

def _parse_hpc1(data: bytes, label: Optional[str]) -> Dict[str, Any]:
    r = _R(data)
    if r.take(4) != b"HPC1": raise HCError("Not HPC1")
    if r.u32() != 11: raise HCError("Bad HPC1 field count")
    name, proto, host = r.txt(), r.txt(), r.txt()
    port = r.u32(); user, pw, payload = r.txt(), r.txt(), r.txt()
    opts_txt = r.txt(); flags = r.u32(); updated = r.u64(); mode = r.txt()
    if r.o != len(data): raise HCError("HPC1 trailing bytes")
    try: opts = json.loads(opts_txt) if opts_txt else {}
    except json.JSONDecodeError: opts = opts_txt
    res: Dict[str, Any] = {"name": name, "protocol": proto, "host": host, "port": port,
                           "username": user, "password": pw, "payload": payload,
                           "options": opts, "flags": flags, "updated_at_ms": updated, "mode": mode}
    if label: res["label"] = label
    return res

def _dec_section(sec: Dict[str, Any], key: bytes, aad_base: bytes) -> bytes:
    try:
        label = sec["a"]; nonce = bytes.fromhex(sec["b"]); ct = bytes.fromhex(sec["c"])
    except (KeyError, TypeError, ValueError): raise HCError("Bad section")
    if not isinstance(label, str) or not label: raise HCError("Bad section label")
    return _xdec(key, nonce, aad_base + b"\x00" + label.encode(), ct)

def _sec_list(v: Any) -> List[Dict[str, Any]]:
    if isinstance(v, list) and all(isinstance(x, dict) for x in v): return v
    if isinstance(v, dict) and all(isinstance(x, dict) for x in v.values()): return list(v.values())
    raise HCError("Bad section collection")

def decrypt_http_custom_file(path, password=None, hwid=None):
    with open(path, "rb") as f:
        data = f.read()
    env = _open_outer(data)
    skey, aad_base = _derive(env, password, hwid)
    main_sec = env.get("i")
    if not isinstance(main_sec, dict): raise HCError("Missing main section")
    main_pt = _dec_section(main_sec, skey, aad_base)
    profiles = []
    for sec in _sec_list(env.get("j", [])):
        pt = _dec_section(sec, skey, aad_base)
        label = sec.get("a")
        if pt.startswith(b"HPC1"):
            prof = _parse_hpc1(pt, label)
            profiles.append(prof)
    
    clean = []
    for p in profiles:
        cp: Dict[str, Any] = {"name": p.get("name",""), "protocol": p.get("protocol",""),
                              "host": p.get("host",""), "port": p.get("port",0),
                              "username": p.get("username",""), "password": p.get("password",""),
                              "mode": p.get("mode","")}
        opts = p.get("options", {})
        if isinstance(opts, dict):
            for k, v in opts.items(): cp[k] = v
        if p.get("payload"): cp["payload"] = p["payload"]
        clean.append(cp)
    return clean

# === FIN MODULE HTTP CUSTOM ===

async def handle_dark_tunnel(update, context):
    save_user(update.effective_user.id)
    document = update.message.document
    if not document:
        return
    original_name = document.file_name or "config"
    normalized_name = _normalize_filename(original_name)
    lower_name = normalized_name.lower()
    
    accepted = lower_name.endswith((".plus", ".ehi", ".hc", ".hci", ".dark"))
    path = os.path.join(
        tempfile.gettempdir(),
        f"dt_{update.effective_user.id}_{os.getpid()}_{os.path.basename(normalized_name)}"
    )
    try:
        await update.message.reply_text("🔐 Analyse de la configuration...")
        tg_file = await document.get_file()
        await tg_file.download_to_drive(path)
        
        # Traitement spécifique pour HTTP Custom (.hc / .hci)
        if lower_name.endswith((".hc", ".hci")):
            try:
                configs = decrypt_http_custom_file(path)
                lines = [
                    "🔐 HTTP CUSTOM (.HC) — CONFIGURATION DÉCHIFFRÉE",
                    f"📄 Fichier : {original_name}",
                    ""
                ]
                if configs:
                    for i, cfg in enumerate(configs, 1):
                        lines.append(f"━━ Profil {i} : {cfg.get('name', 'N/A')} ━━")
                        lines.append(f"Protocole : {cfg.get('protocol', 'N/A')}")
                        lines.append(f"Hôte : {cfg.get('host', 'N/A')}")
                        lines.append(f"Port : {cfg.get('port', 'N/A')}")
                        if cfg.get('username'):
                            lines.append(f"Utilisateur : {cfg.get('username')}")
                        if cfg.get('password'):
                            lines.append(f"Mot de passe : {cfg.get('password')}")
                        if cfg.get('payload'):
                            lines.append(f"Payload :\n{cfg.get('payload')}")
                        lines.append("")
                else:
                    lines.append("ℹ️ Aucun profil trouvé dans le fichier .hc.")
                
                lines.append(SIGNATURE)
                await update.message.reply_text("\n".join(lines)[:4000])
                return
            except Exception as hc_err:
                await update.message.reply_text(f"❌ Erreur de déchiffrement HC (Peut-être protégé par Mot de passe ou HWID) :\n{str(hc_err)[:400]}\n\n{SIGNATURE}")
                return

        # Traitement Dark Tunnel standard pour les autres formats
        if not accepted:
            raw_head = Path(path).read_bytes()[:512]
            try:
                head = unicodedata.normalize("NFKC", raw_head.decode("utf-8", "ignore"))
            except Exception:
                head = ""
            accepted = "://" in head and ("eyJ" in head or "AH" in head)
        if not accepted:
            await update.message.reply_text(
                f"❌ Format non reconnu : {original_name}\n"
                "Formats acceptés : .plus, .dark, .ehi, .hc, .hci"
            )
            return
        loop = asyncio.get_running_loop()
        cfg = await loop.run_in_executor(None, decrypt_dark_tunnel_file, path)
        details = _extract_transport_details(cfg)
        servers = _extract_v2ray_configs(cfg)
        lines = [
            "🔐 DARK TUNNEL — CONFIGURATION DÉCHIFFRÉE",
            f"📄 Fichier : {original_name}",
            ""
        ]
        if servers:
            lines.append(f"🖥️ SERVEURS / COMPTES : {len(servers)}")
            for i, server in enumerate(servers, 1):
                lines.append("")
                lines.append(f"━━ Serveur {i} ━━")
                address = server.get("address") or server.get("server")
                port = server.get("port")
                protocol = server.get("protocol") or details.get("protocol")
                if protocol:
                    lines.append(f"Protocol : {protocol}")
                if address is not None:
                    lines.append(f"Address : {address}")
                if port is not None:
                    lines.append(f"Port : {port}")
                uid = server.get("id") or server.get("uuid")
                if uid:
                    lines.append(f"UUID / ID : {uid}")
        else:
            lines.append("🖥️ Aucun serveur V2Ray/VLESS/VMess trouvé.")
        lines.append("")
        lines.append("🌐 TRANSPORT")
        for key, label in [
            ("network", "Transport"),
            ("security", "Security"),
            ("sni", "SNI"),
            ("host", "WS Host"),
            ("path", "WS Path"),
        ]:
            if key in details:
                lines.append(f"{label} : {details[key]}")
        lines += ["", "✅ Déchiffrement terminé.", SIGNATURE]
        await update.message.reply_text("\n".join(lines)[:4000])
    except Exception as e:
        await update.message.reply_text(
            f"❌ Erreur de déchiffrement : {str(e)[:900]}\n\n{SIGNATURE}"
        )
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

async def handle_download(update,context,audio_only=False):
    save_user(update.effective_user.id)
    raw = update.message.text or ""
    m = re.search(r'https?://\S+', raw)
    url = clean_url(m.group(0) if m else (context.args[0] if context.args else ""))
    if not url:
        return
    await context.bot.send_chat_action(update.effective_chat.id,"upload_video")
    await update.message.reply_text(to_3d("Telechargement..."))
    loop = asyncio.get_event_loop()
    fp,t,_ = await loop.run_in_executor(None,download_video,url,audio_only)
    if fp and os.path.exists(fp):
        try:
            with open(fp,'rb') as f:
                if audio_only:
                    await context.bot.send_audio(update.effective_chat.id,audio=f,caption=to_3d(f"{t}\n\n{SIGNATURE}"))
                else:
                    await context.bot.send_video(update.effective_chat.id,video=f,caption=to_3d(f"{t}\n\n{SIGNATURE}"),supports_streaming=True)
            os.remove(fp)
        except Exception as e:
            await update.message.reply_text(to_3d(f"{e}"))
    else:
        await update.message.reply_text(to_3d(f"{t}"))

async def handle_photo(update,context):
    save_user(update.effective_user.id)
    cap = update.message.caption or "C est quel modele?"
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    try:
        pf = await update.message.photo[-1].get_file()
        fp = "/tmp/analyse.jpg"
        await pf.download_to_drive(fp)
        with open(fp,"rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        if groq_client:
            comp = groq_client.chat.completions.create(model="qwen/qwen3.6-27b",messages=[{"role":"user","content":[{"type":"text","text":cap},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}],temperature=0.0,max_tokens=300)
            rep = comp.choices[0].message.content
            await update.message.reply_text(f"ANALYSE:\n\n{rep}\n\n{SIGNATURE}")
        else:
            await update.message.reply_text("GROQ manquant")
    except Exception as e:
        await update.message.reply_text(f"{str(e)[:500]}\n\n{SIGNATURE}")

async def mp3_cmd(update,context):
    await handle_download(update,context,True)

async def chat_gpt(update,context):
    save_user(update.effective_user.id)
    txt = update.message.text or ""
    low = txt.lower()
    if is_link(txt):
        await handle_download(update,context,False)
        return
    if "pdf" in low or "livre" in low:
        if len(txt.split()) > 1:
            context.args = txt.replace("/pdf","").replace("livre","").split()
            await pdf_cmd(update,context)
            return
    uid = update.effective_user.id
    if uid not in conversations:
        conversations[uid] = []
    conversations[uid].append({"role":"user","content":txt})
    try:
        sys_prompt = f"Tu es {SIGNATURE}. Francais uniquement. Tu peux creer des PDF avec /pdf."
        comp = groq_client.chat.completions.create(model="openai/gpt-oss-20b",messages=[{"role":"system","content":sys_prompt}]+conversations[uid][-10:],temperature=0.7)
        rep = comp.choices[0].message.content
    except:
        rep = f"Bien recu: {txt}. Tape /start"
    conversations[uid].append({"role":"assistant","content":rep})
    await update.message.reply_text(to_3d(f"{rep}\n\n{SIGNATURE}"))

def main():
    print("Building V25.5 DARK TUNNEL...")
    app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("vmess", vmess_cmd))
    app.add_handler(CommandHandler("v2ray", vmess_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("trace", scan_cmd))
    app.add_handler(CommandHandler("scan200", scan200_cmd))
    app.add_handler(CommandHandler("bl", bl_cmd))
    app.add_handler(CommandHandler("blacklist", bl_cmd))
    app.add_handler(CommandHandler("mtr", mtr_cmd))
    app.add_handler(CommandHandler("pdf", pdf_cmd))
    app.add_handler(CommandHandler("mp3", mp3_cmd))
    app.add_handler(CommandHandler("exact", exact_cmd))
    app.add_handler(CommandHandler("today", today_cmd))
    app.add_handler(CommandHandler("tous", today_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_dark_tunnel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
    print("V25.5 GO...")
    app.run_polling()

if __name__ == "__main__":
    main()
