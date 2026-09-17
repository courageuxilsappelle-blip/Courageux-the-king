import os, re, requests, threading, datetime, random, base64, socket, time, asyncio, textwrap, json, tempfile, unicodedata
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont
import urllib3
urllib3.disable_warnings()

TOKEN = os.getenv("TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
print("=== V25.3 FULL + PDF ===")

try:
    groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
except:
    groq_client = None

conversations = {}
SIGNATURE = "COURAGEUX THE KING"

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return f"Bot {SIGNATURE} V25.3 FULL LIVE"

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
    await update.message.reply_text(to_3d(f"Je suis {SIGNATURE}\n📸 Photo\n📥 Lien YT/TikTok\n🎯 /exact Team vs Team\n🔥 /today\n🔍 /scan host\n📚 /pdf sujet\n🔐 /vmess /stats"))

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
    """Normalise les extensions Unicode stylisées (ex. 𝒑𝒍𝒖𝒔 -> plus)."""
    try:
        return unicodedata.normalize("NFKC", name)
    except Exception:
        return name

def _try_json_bytes(data):
    try:
        return json.loads(data.decode("utf-8"))
    except Exception:
        return None

def _b64decode_loose(value):
    if isinstance(value, str):
        value = value.encode()
    value = b"".join(value.split())
    value += b"=" * (-len(value) % 4)
    return base64.b64decode(value, validate=False)

def _walk_config(obj, result=None):
    """Extrait les champs réseau visibles sans deviner les valeurs chiffrées."""
    if result is None:
        result = {}

    if isinstance(obj, dict):
        for k, v in obj.items():
            kl = str(k).lower()
            if isinstance(v, (str, int, float, bool)):
                s = str(v)
                if kl in {"uuid", "user_id", "userid"} and "uuid" not in result:
                    result["uuid"] = s
                elif kl in {"sni", "servername", "server_name"} and "sni" not in result:
                    result["sni"] = s
                elif kl in {"host", "ws_host", "wshost"} and "host" not in result:
                    result["host"] = s
                elif kl in {"address", "server", "host_address", "server_address"} and "address" not in result:
                    result["address"] = s
                elif kl in {"port", "server_port", "port_number"} and "port" not in result:
                    result["port"] = s
                elif kl in {"path", "ws_path", "websocket_path"} and "path" not in result:
                    result["path"] = s
                elif kl in {"protocol", "type"} and "protocol" not in result:
                    result["protocol"] = s
                elif kl in {"network", "transport", "transportnetwork"} and "network" not in result:
                    result["network"] = s
                elif kl in {"security", "tls"} and "security" not in result:
                    result["security"] = s
            elif isinstance(v, (dict, list)):
                _walk_config(v, result)
    elif isinstance(obj, list):
        for item in obj:
            _walk_config(item, result)

    return result

def decrypt_dark_tunnel_file(path):
    """
    Parse la couche externe/base64/JSON d'un fichier Dark Tunnel-like.
    Les champs qui restent cryptographiques sont signalés, sans
    brute-force de clé.
    """
    raw = Path(path).read_bytes()
    candidates = [raw]

    try:
        decoded = _b64decode_loose(raw)
        if decoded and decoded != raw:
            candidates.append(decoded)
    except Exception:
        pass

    configs = []
    encrypted = []

    for data in candidates:
        obj = _try_json_bytes(data)
        if obj is not None:
            configs.append(obj)

    # Inspecte récursivement les chaînes Base64 contenant éventuellement
    # une autre couche JSON.
    seen = set()
    changed = True
    while changed:
        changed = False
        snapshot = list(configs)
        for obj in snapshot:
            oid = id(obj)
            if oid in seen:
                continue
            seen.add(oid)

            stack = [obj]
            while stack:
                cur = stack.pop()
                if isinstance(cur, dict):
                    for k, v in cur.items():
                        kl = str(k).lower()
                        if isinstance(v, str):
                            if "encrypt" in kl or "locked" in kl or "cipher" in kl:
                                encrypted.append({"field": str(k), "length": len(v)})
                            if len(v) > 40 and re.fullmatch(r"[A-Za-z0-9+/=_-]+", v):
                                try:
                                    d = _b64decode_loose(v)
                                    nested = _try_json_bytes(d)
                                    if nested is not None:
                                        configs.append(nested)
                                        changed = True
                                except Exception:
                                    pass
                        elif isinstance(v, (dict, list)):
                            stack.append(v)
                elif isinstance(cur, list):
                    stack.extend(x for x in cur if isinstance(x, (dict, list)))

    result = {}
    for cfg in configs:
        _walk_config(cfg, result)

    result["_encrypted_fields"] = encrypted
    result["_decoded_layers"] = len(configs)
    return result

async def handle_dark_tunnel(update, context):
    save_user(update.effective_user.id)
    document = update.message.document
    if not document:
        return

    original_name = document.file_name or "config.plus"
    name = _normalize_filename(original_name)
    lower_name = name.lower()

    # Accepte les extensions normales ET leurs variantes Unicode stylisées.
    if not lower_name.endswith((".plus", ".ehi", ".hc", ".hci", ".dark")):
        await update.message.reply_text(
            f"❌ Format non reconnu : {original_name}\n"
            "Formats acceptés : .plus, .𝒑𝒍𝒖𝒔, .ehi, .hc, .hci, .dark"
        )
        return

    safe_name = os.path.basename(name)
    path = os.path.join(
        tempfile.gettempdir(),
        f"dt_{update.effective_user.id}_{os.getpid()}_{safe_name}"
    )

    try:
        await update.message.reply_text("🔐 Analyse de la configuration...")
        tg_file = await document.get_file()
        await tg_file.download_to_drive(path)

        cfg = await asyncio.get_running_loop().run_in_executor(
            None, decrypt_dark_tunnel_file, path
        )

        labels = [
            ("protocol", "Protocol"),
            ("address", "Address"),
            ("port", "Port"),
            ("uuid", "UUID"),
            ("sni", "SNI"),
            ("host", "WS Host"),
            ("path", "WS Path"),
            ("network", "Transport"),
            ("security", "Security"),
        ]

        lines = [
            "🔐 DARK TUNNEL — ANALYSE",
            f"📄 Fichier : {original_name}",
            ""
        ]
        shown = False

        for key, label in labels:
            if cfg.get(key) not in (None, ""):
                lines.append(f"{label} : {cfg[key]}")
                shown = True

        if not shown:
            lines.append("ℹ️ Aucun paramètre réseau lisible dans la couche décodée.")

        encrypted_fields = cfg.get("_encrypted_fields", [])
        if encrypted_fields:
            lines += [
                "",
                "🔒 Champs encore chiffrés :",
                ", ".join(str(x["field"]) for x in encrypted_fields)
            ]

        lines += [
            "",
            f"Couches JSON décodées : {cfg.get('_decoded_layers', 0)}",
            SIGNATURE
        ]

        await update.message.reply_text("\n".join(lines)[:4000])

    except Exception as e:
        await update.message.reply_text(
            f"❌ Erreur d'analyse : {str(e)[:800]}"
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
    print("Building V25.3 FULL...")
    app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("vmess", vmess_cmd))
    app.add_handler(CommandHandler("v2ray", vmess_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("trace", scan_cmd))
    app.add_handler(CommandHandler("scan200", scan200_cmd))
    app.add_handler(CommandHandler("mtr", mtr_cmd))
    app.add_handler(CommandHandler("pdf", pdf_cmd))
    app.add_handler(CommandHandler("mp3", mp3_cmd))
    app.add_handler(CommandHandler("exact", exact_cmd))
    app.add_handler(CommandHandler("today", today_cmd))
    app.add_handler(CommandHandler("tous", today_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_dark_tunnel))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
    print("V25.3 GO...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
