import os, re, requests, threading, datetime, random, base64, socket, time, asyncio
from flask import Flask
from groq import Groq
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from PIL import Image
import urllib3
urllib3.disable_warnings()

print("=== COURAGEUX THE KING V18 MTR TRACE REAL ===")
TOKEN = os.getenv("TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None
conversations = {}
SIGNATURE = "COURAGEUX THE KING"

flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return f"Bot {SIGNATURE} V18 LIVE"

def run_flask():
    port = int(os.getenv("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, use_reloader=False)

threading.Thread(target=run_flask, daemon=True).start()
time.sleep(2)

USERS_FILE = "users.txt"
def save_user(uid):
    try:
        if not os.path.exists(USERS_FILE): open(USERS_FILE,"w").close()
        with open(USERS_FILE,"r") as f: data=f.read()
        if str(uid) not in data:
            with open(USERS_FILE,"a") as f: f.write(f"{uid}\n")
    except: pass

def get_total_users():
    try:
        if not os.path.exists(USERS_FILE): return 0
        with open(USERS_FILE,"r") as f: return len([l for l in f if l.strip()])
    except: return 0

def to_3d(t):
    try:
        normal="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
        bold3d="𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇𝟬𝟭𝟮𝟯𝟰𝟱𝟲𝟳𝟴𝟵"
        return "".join([bold3d[normal.index(c)] if c in normal else c for c in t])
    except: return t

def clean_url(u): return u.strip().split('?is=')[0]
def get_yt_id(u):
    m=re.search(r'(?:v=|be/|shorts/|embed/)([A-Za-z0-9_-]{11})',u)
    return m.group(1) if m else None
def is_link(t): return any(x in t.lower() for x in ["http://","https://","tiktok.com","youtu","instagram.com","fb.watch","facebook.com"])

# === VRAI MTR TRACE VIA CHECK-HOST.NET ===
def get_mtr_real(host):
    try:
        session = requests.Session()
        session.headers.update({"Accept":"application/json", "User-Agent":"Mozilla/5.0"})
        # 1. Lancer le check MTR
        print(f"MTR request for {host}")
        r = session.get(f"https://check-host.net/check-mtr?host={host}&max_nodes=1", timeout=15)
        if r.status_code!= 200:
            return {"error": f"Check-host erreur {r.status_code}"}
        data = r.json()
        request_id = data.get("request_id")
        nodes = data.get("nodes", {})
        if not request_id:
            return {"error": "Pas de request_id"}

        print(f"MTR request_id: {request_id} nodes: {list(nodes.keys())[:2]}")
        # 2. Attendre et récupérer les résultats
        result_url = f"https://check-host.net/check-result/{request_id}"
        final_data = None
        for i in range(12): # 12 tentatives = 12 sec
            time.sleep(1.5)
            rr = session.get(result_url, timeout=15)
            if rr.status_code!= 200:
                continue
            j = rr.json()
            # j est dict node -> result
            # Vérifie si au moins un node a fini
            has_data = False
            for node, val in j.items():
                if val and isinstance(val, list) and len(val)>0 and val[0] and val[0][0]!=None:
                    has_data = True
                    break
            if has_data:
                final_data = j
                break

        if not final_data:
            return {"error": "Timeout MTR - réessaie"}

        # 3. Parser le premier node qui a des données (comme ton image Albanie/Tirana)
        for node_key, hops in final_data.items():
            if not hops or not hops[0]: continue
            mtr_list = hops[0] # liste des hops
            # mtr_list format: [{"address":"1.2.3.4", "host":"..."}...] mais check-host renvoie dict complexe
            # En réalité check-host renvoie: [ [ {ip, host, asn...},... ],... ]
            # On essaie de parser 2 formats possibles
            parsed_hops = []
            try:
                # Format check-host.cc: list of hops, each hop is dict
                if isinstance(mtr_list, dict) and "result" in mtr_list:
                    mtr_list = mtr_list["result"]
                if isinstance(mtr_list, list):
                    for idx, hop in enumerate(mtr_list, 1):
                        if not hop: continue
                        # hop peut être dict avec 'address' etc ou list
                        if isinstance(hop, dict):
                            ip = hop.get("address") or hop.get("ip") or "?"
                            hostname = hop.get("host") or hop.get("hostname") or ""
                            asn = hop.get("asn") or hop.get("AS") or ""
                            parsed_hops.append({"n":idx, "ip":ip, "host":hostname, "asn":asn})
                        elif isinstance(hop, list) and len(hop)>0:
                            # format: [{"address":...}]
                            for sub in hop:
                                if isinstance(sub, dict):
                                    ip = sub.get("address") or "?"
                                    hostname = sub.get("host") or ""
                                    parsed_hops.append({"n":idx, "ip":ip, "host":hostname, "asn":""})
                                    break
            except Exception as e:
                print(f"Parse error {e}")
                parsed_hops = []

            if parsed_hops:
                return {"node": node_key, "hops": parsed_hops, "request_id": request_id, "nodes_info": nodes}

        return {"error": "Aucun HOTE trouvé, réessaie dans 10s"}
    except Exception as e:
        import traceback; traceback.print_exc()
        return {"error": str(e)}

def get_host_info(host):
    info={}
    try:
        ip=socket.gethostbyname(host)
        info["ip"]=ip
        try: info["reverse"]=socket.gethostbyaddr(ip)[0]
        except: info["reverse"]="Pas de PTR"
        try:
            r=requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,city,isp,org,as", timeout=5).json()
            if r.get("status")=="success":
                info.update({"country":f"{r.get('country')} - {r.get('city')}", "isp":r.get("isp"), "org":r.get("org"), "as":r.get("as")})
        except: pass
    except Exception as e: info["error"]=str(e)
    return info

def check_port_200(host, ip, port):
    result={"port":port,"open":False,"status":"FERMÉ","is_200":False,"code":0}
    try:
        s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        if s.connect_ex((ip, int(port)))!=0:
            s.close(); return result
        s.close(); result["open"]=True
    except: return result
    try:
        urls=[f"http://{host}:{port}", f"https://{host}:{port}"] if port!=443 else [f"https://{host}:{port}"]
        for u in urls:
            try:
                r=requests.get(u, timeout=4, verify=False, headers={"User-Agent":"Mozilla/5.0"})
                result["code"]=r.status_code
                if r.status_code==200: result["status"]="✅ 200 OK"; result["is_200"]=True
                elif r.status_code in [301,302,403,401]: result["status"]=f"🔀 {r.status_code} - VIVANT"; result["is_200"]=True
                else: result["status"]=f"📄 {r.status_code}"; result["is_200"]=r.status_code<500
                break
            except: continue
        if result["code"]==0 and result["open"]: result["status"]="🟢 OUVERT TCP"
    except: result["status"]="🟢 OUVERT"
    return result

async def mtrace_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text(
            "🌍 VRAI MTR TRACE - comme check-host.net\n\n"
            "Usage:\n"
            "/mtrace ncmrsb-ai-in-f14.1e100.net\n"
            "/mtrace 8.8.8.8\n\n"
            "Le bot va tracer depuis le monde entier comme sur ton image Albanie/Tirana + Australia/Sydney\n\n"
            f"{SIGNATURE}"
        )
        return
    host = context.args[0].replace("http://","").replace("https://","").split("/")[0].split(":")[0]
    await context.bot.send_chat_action(update.effective_chat.id, "typing")
    await update.message.reply_text(f"🌍 MTR TRACE en cours pour {host}...\n⏳ 10-15s comme sur check-host.net")

    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, get_mtr_real, host)

    if "error" in data:
        await update.message.reply_text(f"❌ MTR Erreur: {data['error']}\n\nRéessaie: /mtrace {host}\n\n{SIGNATURE}")
        return

    hops = data.get("hops", [])
    node = data.get("node", "unknown")
    nodes_info = data.get("nodes_info", {})

    # Info du node (ex: Albania, Tirana)
    node_name = "Monde"
    try:
        if node in nodes_info:
            # nodes_info[node] = [country, city, ip, asn,...]
            info = nodes_info[node]
            if isinstance(info, list) and len(info)>=2:
                node_name = f"{info[1]}, {info[0]}"
    except: pass

    text = f"🌍 MTR TRACE: {host}\n"
    text += f"📍 Node: {node_name} ({node})\n"
    text += f"🔗 https://check-host.net/check-mtr?host={host}&node={node}\n"
    text += f"━━━━━━━━━━━━━━\n"
    text += f"# HÔTE ASN\n"

    for h in hops[:15]:
        ip = h.get("ip","?")[:18]
        asn = h.get("asn","-")
        # Récupère ASN via ip-api si manquant
        if not asn or asn=="-":
            try:
                r = requests.get(f"http://ip-api.com/json/{ip}?fields=as", timeout=2).json()
                asn = r.get("as","")[:12]
            except: asn = "-"
        host_short = h.get("host","")[:25] if h.get("host") else ""
        line = f"{h['n']}. {ip} {asn}\n"
        if host_short:
            line = f"{h['n']}. {ip} {host_short} {asn}\n"
        text += line

    text += f"━━━━━━━━━━━━━━\n"
    text += f"💡 /mtr {' '.join([h['ip'] for h in hops if h['ip']!='?' and not h['ip'].startswith('172.')][:5])} = scan 200 OK\n"
    text += f"\n{SIGNATURE}"
    if len(text)>4000: text=text[:4000]
    await update.message.reply_text(text)

async def mtr_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("📡 SCAN MTR 200 OK\n/mtr 163.227.128.102 103.216.222.72\n\nColle les IP de ton image MTR\n\nCOURAGEUX THE KING")
        return
    raw=" ".join(context.args)
    ips=re.findall(r'\b\d+\.\d+\.\d+\.\d+\b', raw)
    ips=list(dict.fromkeys(ips))
    if not ips: await update.message.reply_text("❌ Aucune IP"); return
    loop=asyncio.get_event_loop()
    await update.message.reply_text(f"🔍 Scan {len(ips)} HOSTS MTR...")
    txt=f"🌍 SCAN MTR {len(ips)} HOSTS\n"
    found=[]
    for ip in ips[:15]:
        r80=await loop.run_in_executor(None, check_port_200, ip, ip, 80)
        r443=await loop.run_in_executor(None, check_port_200, ip, ip, 443)
        if r80["is_200"] or r443["is_200"]:
            found.append(ip)
            txt+=f"✅ {ip}: 200 OK VIVANT!\n"
        elif r80["open"] or r443["open"]:
            txt+=f"🟡 {ip}: Ouvert\n"
        else:
            txt+=f"❌ {ip}: Fermé\n"
    if found:
        txt+=f"\n🎯 {len(found)} AVEC 200 OK: {' '.join(found)}\n"
    txt+=f"\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def scan_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args: await update.message.reply_text("🔍 /scan host"); return
    host=context.args[0].split("/")[0].split(":")[0]
    await update.message.reply_text(f"🔍 Scan {host}...")
    loop=asyncio.get_event_loop()
    host_info=await loop.run_in_executor(None, get_host_info, host)
    ip=host_info.get("ip",host)
    txt=f"🌍 {host} IP:{ip}\n"
    for p in [80,443,8080,1080]:
        r=await loop.run_in_executor(None, check_port_200, host, ip, p)
        txt+=f"{'✅' if r['is_200'] else '❌' if not r['open'] else '🟡'} {p}: {r['status']} code {r['code']}\n"
    txt+=f"\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def scan200_cmd(update, context):
    save_user(update.effective_user.id)
    if not context.args: await update.message.reply_text("Usage: /scan200 host"); return
    host=context.args[0].split("/")[0].split(":")[0]
    loop=asyncio.get_event_loop()
    host_info=await loop.run_in_executor(None, get_host_info, host)
    ip=host_info.get("ip",host)
    await update.message.reply_text(f"🎯 Scan 200 OK {host}...")
    found=[]
    for p in [80,443,8080,1080]:
        r=await loop.run_in_executor(None, check_port_200, host, ip, p)
        if r["is_200"]: found.append(r)
    txt=f"🎯 200 OK: {host} ({ip})\n" + "\n".join([f"✅ {r['port']}: code {r['code']}" for r in found]) if found else f"❌ Aucun 200 OK sur {host}"
    txt+=f"\n\n{SIGNATURE}"
    await update.message.reply_text(txt)

async def start(update, context):
    save_user(update.effective_user.id)
    msg = (
        f"Je suis {SIGNATURE} 👑\n"
        "📸 Photo + question\n"
        "📥 Lien YouTube\n"
        "🌍 /mtrace host = VRAI MTR TRACE comme check-host.net (ton image)\n"
        "🔍 /scan host = scan 200 OK simple\n"
        "🎯 /scan200 host = que 200 OK\n"
        "📡 /mtr ip1 ip2 = scan IP de ton MTR\n"
        "🔐 /vmess /stats"
    )
    await update.message.reply_text(to_3d(msg))

async def stats_cmd(update, context):
    save_user(update.effective_user.id)
    await update.message.reply_text(f"📊 Total: {get_total_users()}\n\n{SIGNATURE}")

async def vmess_cmd(update, context): await update.message.reply_text("🔐 VMESS en cours")
async def exact_cmd(update, context): await update.message.reply_text("🎯 /exact")
async def today_cmd(update, context): await update.message.reply_text("🔥 /today")
async def handle_photo(update, context):
    save_user(update.effective_user.id)
    await update.message.reply_text("📸 Photo reçue")
    try:
        photo_file=await update.message.photo[-1].get_file()
        file_path="/tmp/analyse.jpg"
        await photo_file.download_to_drive(file_path)
        with open(file_path, "rb") as f: b64=base64.b64encode(f.read()).decode('utf-8')
        if groq_client:
            comp=groq_client.chat.completions.create(model="qwen/qwen3.6-27b", messages=[{"role":"user","content":[{"type":"text","text":"Quel modèle? Réponds français /no_think"},{"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}]}], temperature=0.0, max_tokens=300)
            rep=comp.choices[0].message.content
            await update.message.reply_text(f"🔍 {rep}\n\n{SIGNATURE}")
    except Exception as e: await update.message.reply_text(f"❌ {e}")
async def chat_gpt(update, context): await update.message.reply_text(to_3d(f"Tape /start\n\n{SIGNATURE}"))

def main():
    print("Building App...")
    app = ApplicationBuilder().token(os.getenv("TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("mtrace", mtrace_cmd))
    app.add_handler(CommandHandler("mtr", mtr_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("trace", scan_cmd))
    app.add_handler(CommandHandler("scan200", scan200_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("vmess", vmess_cmd))
    app.add_handler(CommandHandler("exact", exact_cmd))
    app.add_handler(CommandHandler("today", today_cmd))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_gpt))
    print("✅ Polling...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    try: main()
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback; traceback.print_exc()
        time.sleep(5)
