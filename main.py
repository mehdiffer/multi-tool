import os
import re
import sys
import time
import shutil
import requests
import threading
import websocket
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

CYAN = '\033[96m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
WHITE = '\033[97m'
RESET = '\033[0m'
BOLD = '\033[1m'
THEME_COLOR = "#6a5acd"

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_width():
    return shutil.get_terminal_size((80, 20)).columns

def remove_codes(text):
    ansi = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi.sub('', text)

def render(text, width=None):
    if width is None:
        width = get_width()
    lines = text.split('\n')
    result = []
    for line in lines:
        clean = remove_codes(line)
        pad = max(0, (width - len(clean)) // 2)
        result.append(' ' * pad + line)
    return '\n'.join(result)

def color(hex_code):
    h = hex_code.lstrip('#')
    r = int(h[0:2], 16)
    g = int(h[2:4], 16)
    b = int(h[4:6], 16)
    return f'\033[38;2;{r};{g};{b}m'

def theme():
    return color(THEME_COLOR)

def token_checker():
    clear()
    header()
    w = get_width()
    
    txt = f"{GREEN}{BOLD}Token Checker started{RESET}"
    print(render(txt, w))
    print()
    
    tokens_path = "secret/tokens.txt"
    
    if not os.path.exists(tokens_path):
        print(render(f"{RED}secret/tokens.txt not found{RESET}", w))
        input(render(f"{YELLOW}Press Enter to continue...{RESET}", w))
        menu()
        return
    
    with open(tokens_path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = [line.strip() for line in f if line.strip()]
    
    if not tokens:
        print(render(f"{YELLOW}No tokens found in file.{RESET}", w))
        input(render(f"{YELLOW}Press Enter to continue...{RESET}", w))
        menu()
        return
    
    print(render(f"{CYAN}Checking {len(tokens)} tokens...{RESET}", w))
    print()
    
    valid = []
    invalid = 0
    error = 0
    
    status_col = 12
    name_col   = 22
    id_col     = 25
    token_col  = 20
    
    def check(t):
        t = t.strip()
        if not t:
            return None
        
        headers = {"Authorization": t}
        token_show = (t[:4] + "......" + t[-4:]) if len(t) > 12 else t
        
        try:
            r = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=8)
            
            if r.status_code == 200:
                d = r.json()
                u = d.get("username", "unknown")
                gid = d.get("global_name") or u
                name_display = (gid or u)[:name_col].ljust(name_col)
                uid = d.get("id", "unknown")
                line = f"{GREEN}[VALID]   {name_display} | ID: {uid:<{id_col-5}} | {token_show:<{token_col}}{RESET}"
                return line, t
            else:
                empty_name = " " * name_col
                empty_id   = " " * (id_col - 5)
                if r.status_code in (401, 403):
                    line = f"{RED}[INVALID] {empty_name} | ID: {empty_id} | {token_show:<{token_col}}{RESET}"
                    return line, None
                else:
                    status_str = f"[{r.status_code}]"[:9].ljust(9)
                    line = f"{YELLOW}{status_str} {empty_name} | ID: {empty_id} | {token_show:<{token_col}}{RESET}"
                    return line, None
        except:
            empty_name = " " * name_col
            empty_id   = " " * (id_col - 5)
            line = f"{YELLOW}[ERR]     {empty_name} | ID: {empty_id} | {token_show:<{token_col}}{RESET}"
            return line, None
    
    for token in tokens:
        result, valid_token = check(token)
        if result:
            clean_result = remove_codes(result)
            pad = max(0, (w - len(clean_result)) // 2 + 3)
            print(" " * pad + result)
            if valid_token:
                valid.append(valid_token)
            elif "[INVALID]" in result:
                invalid += 1
            else:
                error += 1
        time.sleep(0.4)
    
    print()
    
    if valid:
        os.makedirs("secret", exist_ok=True)
        valid_path = "secret/valid.txt"
        with open(valid_path, "w", encoding="utf-8") as f:
            f.write("\n".join(valid))
        print(render(f"{GREEN}{len(valid)} valid tokens → saved to {valid_path}{RESET}", w))
    
    summary = f"Valid: {len(valid):3d} | Invalid: {invalid:3d} | Error: {error:3d}"
    print(render(f"{WHITE}{BOLD}{summary}{RESET}", w))
    print()
    
    input(render(f"{CYAN}Press Enter to return to menu...{RESET}", w))
    menu()

def token_spammer():
    clear()
    header()
    w = get_width()
    
    txt = f"{GREEN}{BOLD}Token Spammer started{RESET}"
    print(render(txt, w))
    print()
    
    channel_id_str = input(render(f"{CYAN}Channel ID: {RESET}", w)).strip()
    try:
        channel_id = int(channel_id_str)
    except:
        print(render(f"{RED}Invalid ID{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    message = input(render(f"{CYAN}Message: {RESET}", w)).strip()
    if not message:
        print(render(f"{RED}Empty message{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    tokens_path = "secret/tokens.txt"
    
    if not os.path.exists(tokens_path):
        print(render(f"{RED}tokens.txt not found{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    with open(tokens_path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = [line.strip() for line in f if line.strip()]
    
    if not tokens:
        print(render(f"{YELLOW}No tokens{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    print(render(f"{CYAN}Ultra fast spamming started... Ctrl+C to stop{RESET}", w))
    print()

    stop_event = threading.Event()
    
    def spam_worker(token):
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        payload = {"content": message}
        
        while not stop_event.is_set():
            try:
                r = requests.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/messages",
                    headers=headers,
                    json=payload,
                    timeout=2
                )
                if r.status_code in (200, 201):
                    print(render(f"{GREEN}[OK] {token[:6]}...{token[-6:]}{RESET}", w))
                else:
                    print(render(f"{RED}[{r.status_code}] {token[:6]}...{token[-6:]}{RESET}", w))
            except:
                print(render(f"{YELLOW}[ERR] {token[:6]}...{token[-6:]}{RESET}", w))
            
            time.sleep(0.15)
    
    threads = []
    for token in tokens:
        t = threading.Thread(target=spam_worker, args=(token,))
        t.daemon = True
        t.start()
        threads.append(t)
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop_event.set()
        print(render(f"{RED}Stopping threads...{RESET}", w))
        time.sleep(1)
        print(render(f"{RED}Stopped{RESET}", w))
        print()
        input(render(f"{CYAN}Enter...{RESET}", w))
        menu()

def token_voice_joiner():
    clear()
    header()
    w = get_width()
    
    txt = f"{GREEN}{BOLD}Token Voice Joiner started{RESET}"
    pad = max(0, (w - len(remove_codes(txt))) // 2)
    print(" " * pad + txt)
    print()
    
    guild_id_str = input(render(f"{CYAN}Guild ID: {RESET}", w)).strip()
    try:
        guild_id = int(guild_id_str)
    except:
        print(render(f"{RED}Invalid guild ID{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    voice_channel_id_str = input(render(f"{CYAN}Channel ID: {RESET}", w)).strip()
    try:
        voice_channel_id = int(voice_channel_id_str)
    except:
        print(render(f"{RED}Invalid channel ID{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    tokens_path = "secret/tokens.txt"
    
    if not os.path.exists(tokens_path):
        print(render(f"{RED}tokens.txt not found{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    with open(tokens_path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = [line.strip() for line in f if line.strip()]
    
    if not tokens:
        print(render(f"{YELLOW}No tokens{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return

    stop_event = threading.Event()
    
    def join_voice(token, guild_id, channel_id):
        ws = None
        try:
            ws = websocket.WebSocket()
            ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
            hello = ws.recv()
            heartbeat_interval = json.loads(hello)['d']['heartbeat_interval']
            
            identify = {
                "op": 2,
                "d": {
                    "token": token,
                    "properties": {
                        "$os": "windows",
                        "$browser": "chrome",
                        "$device": "pc"
                    },
                    "intents": 513
                }
            }
            ws.send(json.dumps(identify))
            
            time.sleep(1.2)
            
            voice_state = {
                "op": 4,
                "d": {
                    "guild_id": str(guild_id),
                    "channel_id": str(channel_id),
                    "self_mute": False,
                    "self_deaf": False,
                    "self_stream": False,
                    "self_video": False
                }
            }
            ws.send(json.dumps(voice_state))
            
            headers = {"Authorization": token}
            r = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=5)
            username = "unknown"
            if r.status_code == 200:
                data = r.json()
                username = data.get("global_name") or data.get("username", "unknown")
            
            token_show = token[:6] + "..." + token[-6:]
            line = f"{GREEN}[JOINED] {username:<20} | {token_show}{RESET}"
            print(render(line, w))
            
            while not stop_event.is_set():
                try:
                    ws.recv()
                    time.sleep(heartbeat_interval / 1000)
                except:
                    break
            
        except Exception as e:
            token_show = token[:6] + "..." + token[-6:]
            line = f"{YELLOW}[ERR]     {token_show}{RESET}"
            print(render(line, w))
        finally:
            if ws:
                try:
                    ws.close()
                except:
                    pass
    
    threads = []
    for token in tokens:
        t = threading.Thread(target=join_voice, args=(token, guild_id, voice_channel_id))
        t.daemon = True
        t.start()
        threads.append(t)
    
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_event.set()
        time.sleep(1.5)
        menu()

def token_info_scraper():
    clear()
    header()
    w = get_width()
    
    txt = f"{GREEN}{BOLD}Token Info Scraper started{RESET}"
    pad = max(0, (w - len(remove_codes(txt))) // 2)
    print(" " * pad + txt)
    print()
    
    webhook_url = input(render(f"{CYAN}Webhook URL (leave empty): {RESET}", w)).strip()
    
    tokens_path = "secret/tokens.txt"
    
    if not os.path.exists(tokens_path):
        print(render(f"{RED}tokens.txt not found{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    with open(tokens_path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = [line.strip() for line in f if line.strip()]
    
    if not tokens:
        print(render(f"{YELLOW}No tokens{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return

    valid_count = 0
    
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        
        token_show = token[:6] + "..." + token[-6:]
        
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        
        try:
            r = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=8)
            
            if r.status_code == 200:
                data = r.json()
                username = data.get("username", "unknown")
                global_name = data.get("global_name") or username
                disc = data.get("discriminator", "0")
                uid = data.get("id", "unknown")
                phone = data.get("phone")
                email = data.get("email") or "no"
                verified = "yes" if data.get("verified") else "no"
                nitro = "yes" if data.get("premium_type", 0) > 0 else "no"
                avatar = data.get("avatar")
                avatar_url = f"https://cdn.discordapp.com/avatars/{uid}/{avatar}.png?size=128" if avatar else "https://i.imgur.com/4M34hi2.png"
                
                snowflake = int(uid)
                created_ts = ((snowflake >> 22) + 1420070400000) / 1000
                created_date = datetime.utcfromtimestamp(created_ts).strftime('%Y-%m-%d')
                
                phone_display = f"||{phone}||" if phone else "no"
                
                embed = {
                    "title": global_name,
                    "color": 3447003,
                    "thumbnail": {
                        "url": avatar_url
                    },
                    "fields": [
                        {"name": "Username", "value": f"{username}#{disc}", "inline": True},
                        {"name": "ID", "value": uid, "inline": True},
                        {"name": "Created", "value": created_date, "inline": True},
                        {"name": "Phone", "value": phone_display, "inline": True},
                        {"name": "Email", "value": email, "inline": True},
                        {"name": "Verified", "value": verified, "inline": True},
                        {"name": "Nitro", "value": nitro, "inline": True}
                    ],
                    "footer": {"text": f"Token • {token_show}"},
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                print(render(f"{GREEN}[VALID] {global_name} | {token_show}{RESET}", w))
                valid_count += 1
                
                if webhook_url:
                    payload = {
                        "embeds": [embed],
                        "username": "Token Scraper",
                        "avatar_url": "https://i.imgur.com/4M34hi2.png"
                    }
                    try:
                        requests.post(webhook_url, json=payload, timeout=5)
                    except:
                        pass
                
            else:
                print(render(f"{RED}[INVALID] {token_show}{RESET}", w))
        
        except:
            print(render(f"{YELLOW}[ERR] {token_show}{RESET}", w))
        
        time.sleep(0.6)
    
    print()
    print(render(f"{WHITE}Finished | Valid: {valid_count}/{len(tokens)}{RESET}", w))
    print()
    input(render(f"{CYAN}Enter...{RESET}", w))
    menu()

def nickname_changer():
    clear()
    header()
    w = get_width()
    
    txt = f"{GREEN}{BOLD}Nickname Changer started{RESET}"
    pad = max(0, (w - len(remove_codes(txt))) // 2)
    print(" " * pad + txt)
    print()
    
    guild_id_str = input(render(f"{CYAN}Guild (Server) ID: {RESET}", w)).strip()
    try:
        guild_id = int(guild_id_str)
    except:
        print(render(f"{RED}Invalid guild ID{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    new_nick = input(render(f"{CYAN}New Nickname: {RESET}", w)).strip()
    if not new_nick:
        print(render(f"{RED}Nickname cannot be empty{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    tokens_path = "secret/tokens.txt"
    
    if not os.path.exists(tokens_path):
        print(render(f"{RED}tokens.txt not found{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    with open(tokens_path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = [line.strip() for line in f if line.strip()]
    
    if not tokens:
        print(render(f"{YELLOW}No tokens{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    print(render(f"{CYAN}Changing nicknames in server...{RESET}", w))
    print()

    stop_event = threading.Event()
    
    def change_nick(token, guild_id, nick):
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        payload = {"nick": nick}
        
        try:
            r = requests.patch(
                f"https://discord.com/api/v9/guilds/{guild_id}/members/@me/nick",
                headers=headers,
                json=payload,
                timeout=6
            )
            token_show = token[:6] + "..." + token[-6:]
            if r.status_code in (200, 204):
                print(render(f"{GREEN}[OK] {token_show}{RESET}", w))
            else:
                print(render(f"{RED}[{r.status_code}] {token_show}{RESET}", w))
        except:
            token_show = token[:6] + "..." + token[-6:]
            print(render(f"{YELLOW}[ERR] {token_show}{RESET}", w))
    
    threads = []
    for token in tokens:
        t = threading.Thread(target=change_nick, args=(token, guild_id, new_nick))
        t.daemon = True
        t.start()
        threads.append(t)
        time.sleep(0.5)
    
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_event.set()
        print(render(f"{RED}Stopped{RESET}", w))
        print()
        input(render(f"{CYAN}Enter...{RESET}", w))
        menu()

def status_changer():
    clear()
    header()
    w = get_width()
    
    txt = f"{GREEN}{BOLD}Status Changer started{RESET}"
    pad = max(0, (w - len(remove_codes(txt))) // 2)
    print(" " * pad + txt)
    print()
    
    custom_status = input(render(f"{CYAN}Custom Status Text: {RESET}", w)).strip()
    if not custom_status:
        print(render(f"{RED}Status cannot be empty{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    status_type = input(render(f"{CYAN}Status Type (online/idle/dnd/invisible): {RESET}", w)).strip().lower()
    if status_type not in ["online", "idle", "dnd", "invisible"]:
        status_type = "online"
    
    tokens_path = "secret/tokens.txt"
    
    if not os.path.exists(tokens_path):
        print(render(f"{RED}tokens.txt not found{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    with open(tokens_path, "r", encoding="utf-8", errors="ignore") as f:
        tokens = [line.strip() for line in f if line.strip()]
    
    if not tokens:
        print(render(f"{YELLOW}No tokens{RESET}", w))
        input(render(f"{YELLOW}Enter...{RESET}", w))
        menu()
        return
    
    print(render(f"{CYAN}Changing statuses...{RESET}", w))
    print()

    stop_event = threading.Event()
    
    def set_status(token, text, status_type):
        token_show = token[:6] + "..." + token[-6:]
        
        headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        
        payload = {
            "status": status_type,
            "custom_status": {
                "text": text,
                "expires_at": None,
                "emoji_id": None,
                "emoji_name": None
            }
        }
        
        try:
            r = requests.patch(
                "https://discord.com/api/v9/users/@me/settings",
                headers=headers,
                json=payload,
                timeout=6
            )
            
            if r.status_code in (200, 204):
                print(render(f"{GREEN}[OK] {token_show}{RESET}", w))
            else:
                print(render(f"{RED}[{r.status_code}] {token_show}{RESET}", w))
        except:
            print(render(f"{YELLOW}[ERR] {token_show}{RESET}", w))
    
    threads = []
    for token in tokens:
        t = threading.Thread(target=set_status, args=(token, custom_status, status_type))
        t.daemon = True
        t.start()
        threads.append(t)
        time.sleep(0.5)
    
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        stop_event.set()
        print(render(f"{RED}Stopped{RESET}", w))
        print()
        input(render(f"{CYAN}Enter...{RESET}", w))
        menu()

def header():
    w = get_width()
    lines = [
        "███╗   ███╗██╗   ██╗██╗  ████████╗██╗    ████████╗ ██████╗  ██████╗ ██╗     ",
        "████╗ ████║██║   ██║██║  ╚══██╔══╝██║    ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ",
        "██╔████╔██║██║   ██║██║     ██║   ██║       ██║   ██║   ██║██║   ██║██║     ",
        "██║╚██╔╝██║██║   ██║██║     ██║   ██║       ██║   ██║   ██║██║   ██║██║     ",
        "██║ ╚═╝ ██║╚██████╔╝███████╗██║   ██║       ██║   ╚██████╔╝╚██████╔╝███████╗",
        "╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝   ╚═╝       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝"
    ]

    print()
    c = theme()
    for line in lines:
        colored = c + line + RESET
        pad = (w - len(line)) // 2
        print(" " * pad + colored)

    print()
    tc = theme()
    print(render(f"{tc}Made by {CYAN}@mehdiffer{RESET}", w))
    print(render(f"{tc}https://github.com/mehdiffer{RESET}", w))
    print()

def menu():
    clear()
    header()
    w = get_width()

    tc = theme()
    s1 = f"{tc}1)  {WHITE}Token Checker{RESET}"
    s2 = f"{tc}2)  {WHITE}Token Spammer{RESET}"
    s3 = f"{tc}3)  {WHITE}Token Voice Joiner{RESET}"
    s4 = f"{tc}4)  {WHITE}Token Info Scraper{RESET}"
    s5 = f"{tc}5)  {WHITE}Nickname Changer{RESET}"
    s6 = f"{tc}6)  {WHITE}Status Changer{RESET}"

    col_width = 30

    pad1 = " " * (col_width - len(remove_codes(s1)))
    line1 = f"{s1}{pad1}{s2}"

    pad2 = " " * (col_width - len(remove_codes(s3)))
    line2 = f"{s3}{pad2}{s4}"

    pad3 = " " * (col_width - len(remove_codes(s5)))
    line3 = f"{s5}{pad3}{s6}"

    clean_line = remove_codes(line1)
    center_pad = max(0, (w - len(clean_line)) // 2)

    print()
    print(" " * center_pad + line1)
    print(" " * center_pad + line2)
    print(" " * center_pad + line3)
    print()
    print(render(f"{theme()}>{RESET} ", w), end="", flush=True)

    choice = input()

    sections = {
        "1": token_checker,
        "2": token_spammer,
        "3": token_voice_joiner,
        "4": token_info_scraper,
        "5": nickname_changer,
        "6": status_changer,
    }

    if choice in sections:
        sections[choice]()
    else:
        menu()

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print(f"\n{RED}Interrupted{RESET}\n")
        sys.exit(0)