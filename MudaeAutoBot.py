# -*- coding: utf-8 -*-
import discum
import re
import asyncio
import json
import random
import time
import logging
import threading
from os.path import join as pathjoin
from discum.utils.slash import SlashCommander
from discum.utils.button import Buttoner
from collections import OrderedDict
from functools import lru_cache
from itertools import combinations
from math import comb

class CacheDict(OrderedDict):
    def __init__(self, *args, **kwds):
        self.max = kwds.pop("max", None)
        OrderedDict.__init__(self, *args, **kwds)
        self._check_size_limit()

    def __setitem__(self, key, value):
        OrderedDict.__setitem__(self, key, value)
        self._check_size_limit()

    def _check_size_limit(self):
        if self.max is not None:
            while len(self) > self.max:
                self.popitem(last=False)

msg_buf = CacheDict(max=50)

jsonf = open("Settings_Mudae.json", encoding="utf-8")
settings = json.load(jsonf)
jsonf.close()

bot = discum.Client(token=settings["token"],log={"console":False, "file":False})
mudae = 432610292342587392

with open("cmds.txt","r") as f:
    mudae_cmds = [line.rstrip() for line in f]
mhids = [int(mh) for mh in settings["channel_ids"]]
shids = [int(sh) for sh in settings["slash_ids"]]
channel_settings = dict()

series_list = settings["series_list"]
chars = [charsv.lower() for charsv in settings["name_list"]]
kak_min = settings["min_kak"]
roll_prefix = settings["roll_this"]
slash_prefix = settings["slash_this"]
random_rolling = True if settings["random_rolling"].lower().strip() == "true" else False
daily_kakera = settings["daily_kakera"]
reset_claim_timer = True if settings["reset_claim_timer"].lower().strip() == "true" else False 
reset_claim_timer_cooldown = settings["reset_claim_timer_cooldown"]
sniping = settings.get("sniping_enabled",True)
auto_accept_gifts = True if settings.get("auto_accept_gifts", "True").lower().strip() == "true" else False
claim_free = True if settings.get("claim_free", "True").lower().strip() == "true" else False
mudae_event = True if settings.get("mudae_event", "True").lower().strip() == "true" else False
ourochest_enabled = True if settings.get("ourochest", "True").lower().strip() == "true" else False

ready = bot.gateway.READY

mention_finder = re.compile(r'\<@(?:!)?(\d+)\>')
pagination_finder = re.compile(r'\d+ / \d+')

kak_finder = re.compile(r'\*\*??([0-9]+)\*\*<:kakera:469835869059153940>')
like_finder = re.compile(r'Likes\: \#??([0-9]+)')
claim_finder = re.compile(r'Claims\: \#??([0-9]+)')
poke_finder = re.compile(r'\*\*(?:([0-9+])h )?([0-9]+)\*\* min')
wait_finder = re.compile(r'\*\*(?:([0-9+])h )?([0-9]+)\*\* min \w')
waitdaily_finder = re.compile(r'\*\*(?:(\d+)h )?(\d+)\*\* min\.?')
waitk_finder = re.compile(r'\*\*(?:([0-9+])h )?([0-9]+)\*\* min')
ser_finder = re.compile(r'.*.')

raw_kakera_list = settings.get("kakera_list")
if not raw_kakera_list:
    raise KeyError("Missing required setting: kakera_list")
kakera_list = {
    int(str(cost)): [k.lower() for k in emojis]
    for cost, emojis in raw_kakera_list.items()
}
eventlist = ["🕯️","😆","🍫","🎀","🧸","🎄","🍭","👻","🍬"]
ouroSpheres = ["spB2", "spT2", "spG2", "spY2", "spO2", "spR2", "spL2", "spD2", "spM"]

#Last min Claims
is_last_enable = True if settings["last_true"].lower().strip() == "true" else False 
last_claim_window = settings["last_claim_min"]
min_kak_last = settings["min_kak_last_min"]

kakera_wall = {}
waifu_wall = {}
dailykakera_wall = {}
resetclaimtimer_wall = {}
ourochest_wall = {}
ourochest_busy = set()
daily_roll_reset_wall = 0.0
slash_sphere_cmd = None

COOLDOWNS_FILE = pathjoin('user', 'cooldowns.json')

def load_cooldowns():
    """Load cooldown timers from file."""
    global kakera_wall, waifu_wall, dailykakera_wall, resetclaimtimer_wall, ourochest_wall, daily_roll_reset_wall
    try:
        with open(COOLDOWNS_FILE, 'r', encoding='utf-8') as f:
            cooldowns = json.load(f)
            # Use string keys to match Discord IDs (channel_id, guild_id) used elsewhere
            kakera_wall = {str(k): float(v) for k, v in cooldowns.get('kakera_wall', {}).items()}
            waifu_wall = {str(k): int(v) for k, v in cooldowns.get('waifu_wall', {}).items()}
            dailykakera_wall = {str(k): float(v) for k, v in cooldowns.get('dailykakera_wall', {}).items()}
            resetclaimtimer_wall = {str(k): float(v) for k, v in cooldowns.get('resetclaimtimer_wall', {}).items()}
            # The $ourochest wall holds the UTC day an attempt was spent on, not a timer.
            ourochest_wall = {str(k): str(v) for k, v in cooldowns.get('ourochest_wall', {}).items()}
            daily_roll_reset_wall = float(cooldowns.get('daily_roll_reset_wall', 0.0))
            print(f"Loaded cooldown timers from {COOLDOWNS_FILE}")
    except FileNotFoundError:
        print(f"Cooldowns file not found, starting with empty cooldowns.")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error loading cooldowns: {e}. Starting with empty cooldowns.")

def save_cooldowns():
    """Save cooldown timers to file."""
    try:
        cooldowns = {
            'kakera_wall': {str(k): v for k, v in kakera_wall.items()},
            'waifu_wall': {str(k): v for k, v in waifu_wall.items()},
            'dailykakera_wall': {str(k): v for k, v in dailykakera_wall.items()},
            'resetclaimtimer_wall': {str(k): v for k, v in resetclaimtimer_wall.items()},
            'ourochest_wall': {str(k): v for k, v in ourochest_wall.items()},
            'daily_roll_reset_wall': daily_roll_reset_wall,
        }
        with open(COOLDOWNS_FILE, 'w', encoding='utf-8') as f:
            json.dump(cooldowns, f, indent=2)
    except Exception as e:
        print(f"Error saving cooldowns: {e}")

# Load cooldowns from file at startup
load_cooldowns()

#logging settings
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

def get_kak(text):
    k_value = kak_finder.findall(text)
    like_value = like_finder.findall(text)
    claim_value=claim_finder.findall(text)
    if len(k_value):
        return k_value[0]
    elif len(like_value) or len(claim_value):
        LR = 0
        CR = 0 
        CA= 1
        if(len(like_value)):
            LR = like_value[0]
        if(len(claim_value)):
            CR = claim_value[0]
        pkak = (int(LR) + int(CR)) /2
        multi = 1 + (CA/5500)
        return((25000 *(pkak+70)**-.75+20)*multi+.5)     
    return 0
    
def get_wait(text):
    waits = wait_finder.findall(text)
    if len(waits):
        hours = int(waits[0][0]) if waits[0][0] != '' else 0
        return (hours*60+int(waits[0][1]))*60
    return 0

def get_dailywait(text):
    waits = waitdaily_finder.findall(text)
    if len(waits):
        hours = int(waits[0][0]) if waits[0][0] != '' else 0
        return (hours*60+int(waits[0][1]))*60
    return 0
    
def get_pwait(text):
    waits = poke_finder.findall(text)
    if len(waits):
        hours = int(waits[0][0]) if waits[0][0] != '' else 0
        return (hours*60+int(waits[0][1]))*60
    return 0

def get_serial(text):
    serk = ser_finder.findall(text)
    return serk[0]

def get_kakera_cost(kakera_message):
    # Return the effective kakera cost as a percentage integer.
    cost = 100
    description = kakera_message.get('description', '') or ''
    footer = kakera_message.get('footer') or {}
    footer_text = footer.get('text', '') or ''

    if "💎 ➗" in description:
        cost = cost * 50 // 100
    if user['username'] in footer_text and "<:chaoskey:690110264166842421>" in description:
        cost = cost * 50 // 100
    return cost

_resp = dict()
def wait_for(bot, predicate, timeout=None):
    ev = threading.Event()
    ident = threading.get_ident()
    def evt_check(resp):
        if predicate(resp):
            _resp[ident] = resp.parsed.auto()
            ev.set()
    bot.gateway._after_message_hooks.insert(0,evt_check)
    ev.wait(timeout)
    bot.gateway.removeCommand(evt_check)
    obj = _resp.pop(ident,None)
    
    return obj

def mudae_warning(tide,StartwithUser=True):
    def c(r):
        if r.event.message:
            r = r.parsed.auto()
            # must be sent from mudae, relevant channel id and start with our username
            if StartwithUser == True:
                return r['author']['id'] == str(mudae) and r['channel_id'] == tide and r['content'].startswith(f"**{user['username']}")
            elif StartwithUser == False:
                return r['author']['id'] == str(mudae) and r['channel_id'] == tide
        return False
    return c

def claim_check(channel_id):
    def c(r):
        if r.event.message:
            r = r.parsed.auto()
            # must be sent from mudae and relevant channel id,
            if r['author']['id'] == str(mudae) and r['channel_id'] == channel_id:
                # return true if relevant claim message
                return (r['content'].startswith('<@' + user['id'] + '>') and "you can claim once per interval" in r['content']) or r['content'].startswith(f"*💖 *{user['username']}")
        return False
    return c

def msg_checking(msgcontent):
    msgtocheck = ["maintenance", "reboot"] #list to check incase bot is down
    msgcontent = str(msgcontent)
    t = False
    if msgcontent.startswith(f"**{user['username']}"):
        t = True
    for i in msgtocheck:
        if i in msgcontent:
            t = True
    return t
    
def get_server_settings(guild_id,channel_id):
    try:
        #with open(f"channeldata\\{channel_id}.txt","r", encoding="utf-8") as textsettings:
        with open(pathjoin('channeldata',f'{channel_id}.txt'),'r') as textsettings:
            print(f"Reading channel settings from file for channel {channel_id}.")
            return textsettings.read()
    except IOError:
        print(f"File not found, using different method.")
        
    
    msgs = bot.searchMessages(guild_id,authorID=[mudae],textSearch="($togglehentai)",limit = 5)
    Rmsgs = bot.filterSearchResults(msgs)
    for group in Rmsgs:
        if group['content'].startswith("🛠️"):
            print(f"Using $settings found during search for channel {channel_id}")
            abcdef = group['content'].replace("🛠️","_").replace("⭐","_")
            #pres_data = open(f"channeldata\\{channel_id}.txt","w+")
            pres_data = open(pathjoin('channeldata',f'{channel_id}.txt'),'w+', encoding="utf-8")
            pres_data.write(abcdef)
            pres_data.close()
            return group['content']
    # msgs = bot.searchMessages(guild_id,userID=[mudae],textSearch="($togglehentai)").json()['messages']
    # for group in msgs:
        # for result in group:
            # if 'hit' in result:
                # if result['content'].startswith("🛠️"):
                    # print(result)
                    # return result['content']
    
    # no setting found
    # so send settings request, and hope they have default prefix.
    FsMsgs = bot.searchMessages(guild_id,channelID=[channel_id],authorID=[user['id']],textSearch=roll_prefix,includeNsfw=True,limit=2)
    FsResults = bot.filterSearchResults(FsMsgs)
    for group in FsResults:
        if group['content'].endswith(roll_prefix):
            settings_hope_prefix = group['content'].split(roll_prefix)[0]
             
    print(f"Default $settings used for channel {channel_id}.")
    default_settings_if_no_settings = f"""🛠️ __**Server Settings**__ 🛠️
                 (Server not premium)

                · Prefix: **{settings_hope_prefix}** ($prefix)
                · Lang: **en** ($lang)
                · Claim reset: every **180** min. ($setclaim)
                · Exact minute of the reset: xx:**56** ($setinterval)
                · Reset shifted: by +**0** min. ($shifthour)
                · Rolls per hour: **10** ($setrolls)
                · Time before the claim reaction expires: **30** sec. ($settimer)
                · Spawn rarity multiplicator for already claimed characters: **2** ($setrare)
                · Server game mode: **1** ($gamemode)
                · This channel instance: **1** ($channelinstance)
                · Slash commands: enabled ($toggleslash)

                · Ranking: enabled ($toggleclaimrank/$togglelikerank)
                · Ranks displayed during rolls: claims and likes ($togglerolls)
                · Hentai series: enabled ($togglehentai)
                · Disturbing imagery series: enabled ($toggledisturbing)
                · Rolls sniping: **2** ($togglesnipe) => **{settings['claim_delay']}** sec.
                · Kakera sniping: **1** ($togglekakerasnipe) => **{settings['kak_delay']}** sec.
                · Limit of characters per harem: **8100** ($haremlimit)
                · Custom reactions: yes ($claimreact list)

                · Kakera trading: **disabled** ($togglekakeratrade)
                · Kakera calculation: claims and likes ranks (and number of claimed characters) ($togglekakeraclaim/$togglekakeralike)
                · Kakera value displayed during rolls: enabled ($togglekakerarolls)
                · $kakeraloot wishprotect: enabled ($togglewishprotect)"""            
    return default_settings_if_no_settings

def parse_settings_message(message):
    if message == None:
        return None
    val_parse = re.compile(r'\*\*(\S+)\*\*').findall
    num_parse = re.compile(r'(\d+)').findall
    num_parsedec = re.compile(r'(\d*[.,]?\d+)').findall

    settings_p = re.findall(r'\w+: (.*)',message)
    settings = dict()

    settings['prefix'] = val_parse(settings_p[0])[0]
    settings['prefix_len'] = len(settings['prefix'])
    settings['claim_reset'] = int(num_parse(settings_p[2])[0]) # in minutes
    settings['reset_min'] = int(num_parse(settings_p[3])[0])
    settings['shift'] = int(num_parse(settings_p[4])[0])
    settings['max_rolls'] = int(num_parse(settings_p[5])[0])
    settings['expiry'] = float(num_parse(settings_p[6])[0])
    settings['claim_snipe'] = [float(v) for v in num_parsedec(settings_p[17])]
    settings['kak_snipe'] = [float(v) for v in num_parsedec(settings_p[18])]
    

    settings['claim_snipe'][0] = int(settings['claim_snipe'][0])
    # pad out claim/kak snipe for default '0 second cooldown'
    if len(settings['claim_snipe']) < 2:
        settings['claim_snipe'] += [0.0]
    if len(settings['kak_snipe']) < 2:
        settings['kak_snipe'] += [0.0]
    settings['claim_snipe'][0] = int(settings['claim_snipe'][0])
    settings['kak_snipe'][0] = int(settings['kak_snipe'][0])

    settings['pending'] = None
    settings['rolls'] = 0
 
    return settings

def get_snipe_time(channel,rolled,message):
    # Returns delay for when you are able to snipe a given roll
    r,d = channel_settings[channel]['claim_snipe']
    if r == 0:
        # Anarchy FTW!
        return 0.0
    
    global user
    is_roller = (rolled == user['id'])
    if (r < 4 or r == 5) and is_roller:
        # Roller can insta-snipe
        return 0.0
    if r == 2 and not is_roller:
        # Not the roller.
        return d
    
    wished_for = mention_finder.findall(message)
    
    # Wish-based rules
    if not len(wished_for):
        # Not a WISHED character
        if r > 4:
            # Combined restriction, roller still gets first dibs
            return 0.0 if is_roller else d
        return 0.0

    if r > 2 and user['id'] in wished_for:
        # Wishers can insta-snipe
        return 0.0
    
    if r == 1 and rolled not in wished_for:
        # Roller (who is not us) did not wish for char, so can insta-snipe
        return 0.0
    
    return d

def next_claim(channel):
    channel = int(channel)
    offset = (channel_settings[channel]['shift']+channel_settings[channel]['reset_min'] + (30 - channel_settings[channel]['reset_min'])*2 )*60
    reset_period = channel_settings[channel]['claim_reset']*60
    t = time.time()+offset
    last_reset = (t%86400)%reset_period
    reset_at = reset_period-last_reset+time.time()
    return (int(t/reset_period),reset_at) # claim window id, timestamp of reset

def next_reset(channel):
    # Returns timestamp of next reset
    channel = int(channel)
    offset = channel_settings[channel]['reset_min']*60
    t = time.time()
    return t+(3600-((t-offset)%3600))

def next_retry_after_down(channel, downtime):
    # Retry at least 5 minutes after the downtime check, at a random minute inside
    # whichever roll window (reset_min .. reset_min-1 of the next hour) that time lands in.
    start = downtime + 5*60
    offset = channel_settings[int(channel)]['reset_min']*60
    # boundary = start rounded up to the next :reset_min; window_end is the minute before it
    boundary = ((start - offset) // 3600 + 1) * 3600 + offset
    window_end = boundary - 60
    return start + random.randint(0, int((window_end - start) // 60))*60

def poke_roll(tide):
    tides = str(tide)
    if tide not in channel_settings:
        logger.error(f"Could not find channel {tide}, will not catch Pokemon.")
        return
    c_settings = channel_settings[tide]
    pwait = 0
    while True:
        while pwait == 0:
            time.sleep(2)
            bot.sendMessage(tides,c_settings['prefix']+"p")
            if wait_for(bot,mudae_warning(tides,False),timeout=5) is None:
                now = time.time()
                pwait = next_retry_after_down(tide, now) - now
                print(f"Mudae appears down in channel {tide}. Next poke claim in {round(pwait)} seconds.")
            else:
                pwait = 2*60*60 # sleep for 2 hours
        print(f"Catching Pokemon in channel {tide}. Next claim in {pwait} seconds.")
        time.sleep(pwait) 
        pwait = 0
        
def daily_message_check(slashchannel):
    slashchannel = str(slashchannel)
    def c(r):
        if r.event.message:
            m = r.parsed.auto()
            # 1) Channel id must match slashchannel
            if m.get('channel_id') != slashchannel:
                return False
            # 2) Author must be Mudae
            if m.get('author', {}).get('id') != str(mudae):
                return False
            # 3) Interaction username must equal our username
            inter = m.get('interaction')
            inter_user = inter.get('user', {})
            if inter_user.get('username') != user['username']:
                return False
            # 4) Interaction command name must be 'daily'
            if inter.get('name') != 'daily':
                return False
            return True
        return False
    return c

def guild_id_from_channel(channel_id):
    # 1) try cached READY data
    guilds = bot.gateway.session.settings_ready.get("guilds", {})
    ch = str(channel_id)
    for gid, g in guilds.items():
        if ch in g.get("channels", {}):
            return int(gid)
    # 2) fallback to API channel lookup
    try:
        channel = bot.getChannel(str(channel_id)).json()
        gid = channel.get("guild_id")
        return int(gid) if gid else None
    except Exception:
        return None

def daily_roll_reset(channelID, slash_daily_cmd):
    guildID = guild_id_from_channel(channelID)
    if not channelID or not guildID:
        logger.error(f"Could not find channel {channelID} or guild {guildID}, will not collect daily roll reset.")
        return
    global daily_roll_reset_wall
    while True:
        # Respect stored cooldown (single global timestamp)
        cooldown_remaining = daily_roll_reset_wall - time.time()
        if cooldown_remaining > 0:
            print(f"Daily roll reset on cooldown, {round(cooldown_remaining)} seconds until next claim.")
            time.sleep(max(cooldown_remaining, 1))

        bot.triggerSlashCommand(str(mudae), channelID, guildID, data=slash_daily_cmd)
        # Default: 30 minutes if timeout or invalid state/format
        cooldown_seconds = 30 * 60
        resp = wait_for(bot, daily_message_check(channelID), timeout=5)
        if resp is None:
            print(f"Failed to claim daily roll reset, retrying in {round(cooldown_seconds)} seconds.")
        else:
            content = resp.get('content', '')
            # Successful daily uses ✅ – assume 20 hours cooldown
            if '✅' in content:
                cooldown_seconds = 20 * 60 * 60
                print(f"Daily roll reset successfully claimed, {round(cooldown_seconds)} seconds until next claim.")
            else:
                # Parse cooldown text (e.g. "Next $daily reset in **8h 01** min.")
                parsed_wait = get_dailywait(content)
                if parsed_wait > 0:
                    cooldown_seconds = parsed_wait
                else:
                    # Neither ✅ nor a recognisable cooldown text
                    print(f"Failed to claim daily roll reset, retrying in {round(cooldown_seconds)} seconds.")
                    print(content)
        # Store cooldown timestamp
        daily_roll_reset_wall = time.time() + cooldown_seconds
        save_cooldowns()
        # Sleep until cooldown expires before next loop iteration to avoid immediate re-check
        cooldown_remaining = daily_roll_reset_wall - time.time()
        if cooldown_remaining > 0:
            time.sleep(cooldown_remaining)

# $ourochest ($oc): a 5x5 grid of spheres hiding one red sphere, 5 clicks.
# Mudae's colour rules are all conditions on the red sphere's position, so every click
# narrows it down: orange sits next to red, yellow on a diagonal of red, green in red's
# row or column, teal in red's row/column/diagonal, blue in none of them, and red is
# never the centre cell.
oc_value = {"B": 10, "T": 20, "G": 35, "Y": 55, "O": 90, "R": 150}
oc_sphere = {"spB2": "B", "spT2": "T", "spG2": "G", "spY2": "Y", "spO2": "O", "spR2": "R"}
oc_clicks_finder = re.compile(r'You can click \*\*([0-9]+)\*\* times')
oc_cells = list(range(25))
oc_center = 12
oc_coord = {i: (i // 5, i % 5) for i in oc_cells}
oc_reds = [c for c in oc_cells if c != oc_center]
oc_order = ("B", "T", "G", "Y", "O", "R")
oc_index = {c: i for i, c in enumerate(oc_order)}
oc_colour_value = [oc_value[c] for c in oc_order]
oc_boards = None
oc_beam = 8

def oc_rowcol(a, b):
    return oc_coord[a][0] == oc_coord[b][0] or oc_coord[a][1] == oc_coord[b][1]

def oc_diag(a, b):
    return abs(oc_coord[a][0]-oc_coord[b][0]) == abs(oc_coord[a][1]-oc_coord[b][1]) != 0

def oc_adjacent(a, b):
    return abs(oc_coord[a][0]-oc_coord[b][0]) + abs(oc_coord[a][1]-oc_coord[b][1]) == 1

def oc_lines(a, b):
    return oc_rowcol(a, b) or oc_diag(a, b)

oc_adj = {x: [c for c in oc_cells if oc_adjacent(x, c)] for x in oc_cells}
oc_diag_cells = {x: [c for c in oc_cells if oc_diag(x, c)] for x in oc_cells}
oc_rowcol_cells = {x: [c for c in oc_cells if oc_rowcol(x, c) and c != x] for x in oc_cells}
oc_cons = {
    "O": {x: frozenset(oc_adj[x]) for x in oc_cells},
    "Y": {x: frozenset(oc_diag_cells[x]) for x in oc_cells},
    "G": {x: frozenset(oc_rowcol_cells[x]) for x in oc_cells},
    "T": {x: frozenset(c for c in oc_cells if oc_lines(x, c) and c != x) for x in oc_cells},
    "B": {x: frozenset(c for c in oc_cells if not oc_lines(x, c) and c != x) for x in oc_cells},
}

def oc_refine(cands, x, colour):
    # Red positions still possible after seeing `colour` on cell x.
    return frozenset((cands & oc_cons[colour][x]) - {x})

def oc_branches(cands, x):
    return [c for c in ("O", "Y", "G", "T", "B") if oc_refine(cands, x, c)]

@lru_cache(maxsize=None)
def oc_guaranteed(cands, clicked, k):
    # Can the red sphere still be hit within k clicks, whatever the board is?
    if not cands:
        return True
    if k <= 0 or len(cands) == 1:
        return k > 0
    for x in [c for c in oc_cells if c not in clicked]:
        bs = oc_branches(cands, x)
        if not bs:
            return True
        if all(oc_guaranteed(oc_refine(cands, x, c), frozenset(clicked | {x}), k - 1) for c in bs):
            return True
    return False

def oc_all_boards():
    # Built once, on the first puzzle: every board Mudae can deal.
    global oc_boards
    if oc_boards is None:
        oc_boards = oc_build_boards()
    return oc_boards

def oc_build_boards():
    # Red anywhere but the centre, 2 orange drawn from the cells next to it, 3 yellow from
    # its diagonals, 4 green from the rest of its row and column. Holding the whole set is
    # what makes a cell's value exact instead of independent: once both oranges have been
    # revealed, no other cell can still be one, so the yellows become the better click.
    boards = []
    unknown = oc_index["B"]
    for red in oc_reds:
        adj, diag = oc_adj[red], oc_diag_cells[red]
        if len(adj) < 2 or len(diag) < 3:
            continue
        for orange in combinations(adj, 2):
            for yellow in combinations(diag, 3):
                pool = [c for c in oc_rowcol_cells[red] if c not in orange and c not in yellow]
                if len(pool) < 4:
                    continue
                for green in combinations(pool, 4):
                    layout = bytearray([unknown] * 25)
                    layout[red] = oc_index["R"]
                    for c in orange:
                        layout[c] = oc_index["O"]
                    for c in yellow:
                        layout[c] = oc_index["Y"]
                    for c in green:
                        layout[c] = oc_index["G"]
                    lines = oc_cons["T"][red]
                    for c in oc_cells:
                        if layout[c] == unknown and c in lines:
                            layout[c] = oc_index["T"]
                    p = (1.0 / len(oc_reds)) / comb(len(adj), 2) / comb(len(diag), 3) / comb(len(pool), 4)
                    boards.append((p, bytes(layout), red))
    return boards

def oc_survive(alive, x, colour):
    left = [b for b in alive if b[1][x] == oc_index[colour]]
    # A board outside this model would leave nothing; keep the previous set and carry on.
    return left if left else alive

def oc_values(alive, free):
    # Expected spheres from each still-clickable cell, over the boards still possible.
    ev = {x: 0.0 for x in free}
    total = 0.0
    for w, layout, _ in alive:
        total += w
        for x in free:
            ev[x] += w * oc_colour_value[layout[x]]
    total = total or 1.0
    return {x: v / total for x, v in ev.items()}

def oc_next_click(observed, remaining, alive):
    # Click the best-paying cell that still leaves the red sphere reachable inside the
    # budget, judging the pay by looking one click ahead as well as at the cell itself.
    # The board set is what makes both parts exact: the guarantee comes from which red
    # positions are still possible, the pay from which spheres are still unaccounted for
    # - a cell that could only have been orange is worth nothing once both oranges are up.
    clicked = frozenset(observed)
    cands = frozenset(b[2] for b in alive)
    free = [x for x in oc_cells if x not in clicked]
    ev = oc_values(alive, free)
    if len(cands) <= 1:
        # Red is pinned down, so its cell is worth the full 150 and simply wins this.
        return max(free, key=lambda x: ev[x])
    order = sorted(free, key=lambda x: -ev[x])
    keepable = [x for x in order
                if not oc_branches(cands, x)
                or all(oc_guaranteed(oc_refine(cands, x, c), frozenset(clicked | {x}), remaining - 1)
                       for c in oc_branches(cands, x))]
    shortlist = (keepable or order)[:oc_beam]
    if remaining <= 1 or len(shortlist) == 1:
        return shortlist[0]
    total = sum(b[0] for b in alive) or 1.0
    best, best_score = shortlist[0], None
    for x in shortlist:
        buckets = {}
        for b in alive:
            buckets.setdefault(b[1][x], []).append(b)
        score = ev[x]
        for sub in buckets.values():
            after = oc_values(sub, [c for c in free if c != x])
            score += (sum(b[0] for b in sub) / total) * max(after.values())
        if best_score is None or score > best_score:
            best, best_score = x, score
    return best

def ourochest_board(message):
    # Grid cell -> button for an ourochest chest puzzle, otherwise None. The other
    # sphere minigames share these buttons, so the wording picks the chest out.
    if "red sphere" not in message.get('content', ''):
        return None
    rows = message.get('components') or []
    cells = {}
    for r, row in enumerate(rows):
        buttons = row.get('components') or []
        if r > 4 or len(buttons) != 5:
            return None
        for c, butt in enumerate(buttons):
            cells[r * 5 + c] = butt
    if len(cells) != 25:
        return None
    return cells

def ourochest_is_ours(message):
    # Slash-triggered puzzles carry the triggering user; prefix-triggered ones carry no
    # interaction at all and only appear when we type the command ourselves.
    inter = message.get('interaction') or {}
    uid = (inter.get('user') or {}).get('id')
    return uid is None or uid == user['id']

def ourochest_read(channelid, messageid):
    # Current cell -> revealed colour; "U" is a sphere not clicked yet.
    try:
        msg = bot.getMessage(channelid, messageid).json()[0]
        cells = ourochest_board(msg)
        if cells is None:
            return {}
        return {c: oc_sphere.get((b.get('emoji') or {}).get('name'), "U") for c, b in cells.items()}
    except Exception:
        return {}

def ourochest_solve(message):
    channelid = message['channel_id']
    messageid = message['id']
    cells = ourochest_board(message)
    try:
        if cells is None:
            return
        ourochest_wall[channelid] = ourochest_today()
        save_cooldowns()
        butts = Buttoner(message['components'])
        found = oc_clicks_finder.findall(message.get('content', ''))
        budget = int(found[0]) if found else 5
        print(f"Playing $ourochest in channel {channelid}, {budget} clicks available.")
        observed, alive = {}, oc_all_boards()
        for step in range(budget):
            x = oc_next_click(observed, budget - step, alive)
            bot.click(
                str(mudae),
                channelID=channelid,
                guildID=message.get('guild_id'),
                messageID=messageid,
                messageFlags=message['flags'],
                data=butts.getButton(customID=cells[x]['custom_id']),
            )
            colour = None
            deadline = time.time() + 10
            while time.time() < deadline:
                revealed = ourochest_read(channelid, messageid)
                if revealed.get(x, "U") != "U":
                    colour = revealed[x]
                    break
                time.sleep(0.4)
            if colour is None:
                print(f"$ourochest: cell {x} never revealed in channel {channelid}, stopping.")
                return
            observed[x] = colour
            alive = oc_survive(alive, x, colour)
            print(f"$ourochest revealed {colour} ({oc_value[colour]} spheres) on cell {x} in channel {channelid}.")
        total = sum(oc_value[c] for c in observed.values())
        print(f"$ourochest finished in channel {channelid} with {total} spheres from {len(observed)} clicks.")
    finally:
        ourochest_busy.discard(messageid)

def ourochest_next_reset():
    # Attempts unlock at 08:00 GMT+8, which is 00:00 UTC. Epoch seconds are already
    # aligned to UTC, so this does not care what timezone the bot runs in.
    return (int(time.time()) // 86400 + 1) * 86400

def ourochest_today():
    # The attempt day rolls at 00:00 UTC, so the UTC date names the day the currently
    # available attempt belongs to, whatever timezone the bot runs in.
    return time.strftime("%Y-%m-%d", time.gmtime())

def ourochest_puzzle_check(channel_id):
    target = str(channel_id)
    def c(r):
        if r.event.message:
            m = r.parsed.auto()
            return (m['author']['id'] == str(mudae) and m['channel_id'] == target
                    and ourochest_board(m) is not None and ourochest_is_ours(m))
        return False
    return c

def ourochest_daily(channelID):
    ch = str(channelID)
    guildID = guild_id_from_channel(channelID)
    if not guildID:
        logger.error(f"Could not find guild for channel {ch}, will not play $ourochest there.")
        return
    while True:
        today = ourochest_today()
        last = ourochest_wall.get(ch)
        if last == today:
            # Today's attempt is spent, so wait for the rollover instead of re-checking.
            time.sleep(max(ourochest_next_reset() - time.time(), 1))
            continue
        if last is None:
            print(f"$ourochest has no recorded attempt for channel {ch}, playing now.")
        else:
            print(f"$ourochest was last played in channel {ch} on {last} and today is {today}, playing now.")
        if slash_sphere_cmd is None:
            print("Waiting for the /sphere slash command before playing $ourochest.")
            time.sleep(5)
            continue
        # Record the attempt as taken before firing, so a slow answer cannot make us fire twice.
        ourochest_wall[ch] = today
        save_cooldowns()
        started = False
        for attempt in range(5):
            bot.triggerSlashCommand(str(mudae), channelID, guildID, data=slash_sphere_cmd)
            if wait_for(bot, ourochest_puzzle_check(channelID), timeout=20) is not None:
                started = True
                break
            if attempt < 4:
                print(f"$ourochest did not start in channel {ch}, retrying in 30 seconds.")
                time.sleep(30)
        if not started:
            print(f"$ourochest never started in channel {ch}, waiting for the next reset.")

def waifu_roll(tide,slashed):
    global user
    guildID = guild_id_from_channel(tide)
    if slashed == None:
        print(f"Rolling for waifus in channel {tide}.")
    else:
        print(f"Slash rolling for waifus in channel {tide}.")
    
    tides = str(tide)
    waifuwait = 0
    
    if tide not in channel_settings:
        print(f"Could not find channel {tide}, skipping waifu rolling on this channel.")
        return
    
    c_settings = channel_settings[tide]
    roll_cmd = c_settings['prefix'] + roll_prefix
    
    warned_overroll = False
    # TODO Add persistent cooldown tracking for waifu rolls
    while True:
        wait_for_quiet = wait_for(bot,mudae_warning(tides,False),timeout=10)
        if wait_for_quiet != None:
            # don't do stuff
            continue
    
        c_settings['rolls'] = 0
        rolls_left = -1
        checkmudaedown = 0
        while waifuwait == False:
            if slashed != None:
                bot.triggerSlashCommand(str(mudae), channelID=tides, guildID=guildID, data=slashed)
            else:
                bot.sendMessage(tides,roll_cmd)
            varwait = wait_for(bot,mudae_warning(tides,False),timeout=5)
            time.sleep(.5)
            
            if varwait != None:
                # Check if it's our roll if a message is received
                our_roll = msg_buf.get(varwait['id'],{}).get('rolled',None)
                if our_roll:
                    # minus rolls_left after 2 rolls left warning
                    rolls_left = rolls_left-1

            if varwait != None and msg_checking(varwait['content']) and "$ku" not in varwait['content']:
                # We over-rolled.
                checkmudaedown = 0
                waifuwait = True
                if c_settings['rolls'] > 2 and not warned_overroll:
                    # We overrolled when we shouldn't have. Warn the user they can prevent this
                    warned_overroll = True
                    logger.warning("Please enable $rollsleft 0 feature to prevent overrolling.")
                break
            elif varwait != None and rolls_left < 0:
                # Check if our roll featured a warning
                checkmudaedown = 0
                total_text = varwait.get('content','') # $rollsleft 2
                if len(varwait['embeds']):
                    total_text += varwait['embeds'][0].get('footer',{}).get('text','') # $rollsleft 0 (default)
                    total_text += varwait['embeds'][0].get('description','') # $rollsleft 1
                
                p = c_settings['pending']
                if our_roll == None and p:
                    # on_message may have not seen our roll, so we should manually check if it was our roll
                    our_roll = p == user['id']
                    
                if our_roll and "\u26a0\ufe0f 2 ROLLS " in total_text:
                    # Has warning for us
                    rolls_left = 2
                    
            if rolls_left == 0 or checkmudaedown > 3:
                # Ran out of rolls or mudae down
                waifuwait = True
                
            if varwait == None:
                checkmudaedown += 1
        offset_random = 0
        if random_rolling:
            offset_random = random.randint(0,58)*60
        if checkmudaedown > 3:
            now = time.time()
            wait_until = next_retry_after_down(tide, now)
            print(f"Mudae is down in channel {tide}. Next roll in {round(wait_until-now)} seconds.")
        else:
            wait_until = (next_reset(tide)+1+offset_random)
            print(f"Finish rolling for waifus in channel {tide}. Next roll in {round(wait_until-time.time())} seconds.")
        time.sleep(wait_until-time.time())
        waifuwait = False

def snipe_character_delay(recv_time, snipe_delay):
    if snipe_delay != 0.0:
        try:
            time.sleep((recv_time+snipe_delay)-time.time())
        except ValueError:
            # sleep was negative, so we're overdue!
            return
    time.sleep(.3)
    
def snipe_character(messagechunk, buttonspres, channelid):
    if buttonspres.components != []:
        buttMojis = buttonspres.components[0]["components"][0]["emoji"]["name"]
        bot.click(
            messagechunk['author']['id'],
            channelID=messagechunk["channel_id"],
            guildID=messagechunk.get("guild_id"),
            messageID=messagechunk["id"],
            messageFlags=messagechunk["flags"],
            data=buttonspres.getButton(emojiName=buttMojis),
        )
    else:
        bot.addReaction(messagechunk['channel_id'], messagechunk['id'], "❤")
    
    # newmessagechunk = wait_for(bot, lambda m: mudae_warning(channelid, True) and 'content' in m.parsed.auto() and 'claim' in m.parsed.auto()['content'], timeout=5)
    newmessagechunk = wait_for(bot, claim_check(channelid), timeout=5)
    if newmessagechunk is None:
        # Character might be claimed by someone else
        waifu_wall.pop(channelid, None)
        save_cooldowns()
    else:
        # Check if it is claim timer
        if "you can claim once per interval" in newmessagechunk['content']:
            # Get claim time
            if get_pwait(newmessagechunk['content']):
                waifu_wall[channelid] = next_claim(channelid)[1]
                save_cooldowns()
                print(f"{round(next_claim(channelid)[1] - time.time())} second(s) waifu claiming cooldown was set for channel {channelid}.")
        
            # Check if we should run the $rt command
            if reset_claim_timer:
                reset_claim_timer_cooldown_time = resetclaimtimer_wall.get(channelid, 0) - time.time()
                if reset_claim_timer_cooldown_time <= 0:
                    bot.removeReaction(messagechunk['channel_id'], messagechunk['id'], "❤")
                    bot.sendMessage(channelid, channel_settings[int(channelid)]['prefix'] + "rt")
                    resetclaimtimer_wall[channelid] = time.time() + reset_claim_timer_cooldown * 60 * 60  # Cooldown in hours
                    print(f"Ran reset claim timer command in channel {channelid}.")
                    # Attempt to snipe the character again
                    waifu_wall[channelid] = next_claim(channelid)[1]
                    save_cooldowns()
                    print(f"Attempting to snipe the character again in channel {channelid} after running $rt.")
                    snipe_character(messagechunk, buttonspres, channelid)
                else:
                    print(f"Skipped running $rt in channel {channelid} due to cooldown.")

def is_rolled_char(m):
    embeds = m.get('embeds',[])
    if len(embeds) != 1 or "image" not in embeds[0] or "author" not in embeds[0] or list(embeds[0]["author"].keys()) != ['name']:
        # not a marry roll.
        return False
    elif 'footer' in embeds[0] and 'text' in embeds[0]['footer'] and pagination_finder.findall(embeds[0]['footer']['text']):
        # Has pagination e.g. "1 / 29", which does not occur when rolling
        return False
    return True

@bot.gateway.command
def on_message(resp):
    global user

    recv = time.time()
    if resp.event.message:
        m = resp.parsed.auto()
        aId = m['author']['id']
        content = m['content']
        embeds = m['embeds']
        messageid = m['id']
        channelid = m['channel_id']
        
        guildid = m['guild_id'] if 'guild_id' in m else None
        butts = Buttoner(m["components"])
        
        # if "@" in content:
            # print("There was a possible wish detected")
            
        if int(channelid) not in mhids:
            # Not a channel we work in.
            return

        if int(channelid) not in channel_settings:
            mhids.remove(int(channelid))
            logger.error(f"Could not find settings for {channelid}, please trigger the '$settings' command in the server and run the bot again.")
            return
        c_settings = channel_settings[int(channelid)]
        
        snipe_delay = channel_settings[int(channelid)]['kak_snipe'][1]

        if c_settings['pending'] == None and int(aId) != mudae and content[0:c_settings['prefix_len']] == c_settings['prefix'] and content.split(' ')[0][c_settings['prefix_len']:] in mudae_cmds:
            # Note rolls as they happen so we know who rolled what
            c_settings['pending'] = aId
            return
        elif int(aId) == mudae:
            if ourochest_enabled and messageid not in ourochest_busy and ourochest_board(m) is not None and ourochest_is_ours(m):
                # Our own puzzle, whether we scheduled it or someone typed $oc by hand.
                ourochest_busy.add(messageid)
                ocs = threading.Thread(target=ourochest_solve,args=[m])
                ocs.start()
                return
            if "interaction" in m:
                # Mudae triggered via slash command
                roller = m['interaction']['user']['id']
            else:
                roller = c_settings['pending']
            c_settings['pending'] = None

            # Validate this is a rolled character.
            if not is_rolled_char(m):
                content_starts_with_mention = (m['content'].startswith('<@' + user['id'] + '>') or m['content'].startswith('<@!' + user['id'] + '>'))
                if content_starts_with_mention:
                    # get claim time
                    if get_pwait(m['content']):
                        waifu_wall[channelid] = next_claim(channelid)[1]
                        save_cooldowns()
                        # print(f"{round(next_claim(channelid)[1] - time.time())} second(s) waifu claiming cooldown was set for channel {channelid}.")
                        
                    # Check for gift messages
                    if auto_accept_gifts:
                        if "Enhanced multitrade: this gift is free" in m['content']:
                            print(f"Gift detected in channel {channelid}, auto-accepting...")
                            bot.sendMessage(channelid, "y")
                return
                
            msg_buf[messageid] = {'claimed':int(embeds[0].get('color',0)) not in (16751916,1360437),'rolled':roller == user['id']}
            print(f"Our user rolled in {channelid}." if roller == user['id'] else f"Someone else rolled in {channelid}.")

            # Claiming kakera
            if msg_buf[messageid]['claimed']:
                kakera_message = bot.getMessage(channelid, messageid).json()[0]['embeds'][0]
                if butts.components != []:
                    cooldown = kakera_wall.get(guildid, 0) - time.time()
                    if roller != user['id']:
                        time.sleep(snipe_delay)
                    for butt in butts.components[0]["components"]:
                        buttMoji = butt["emoji"]["name"]
                        buttMoji_lower = buttMoji.lower()
                        # Check if free_kakera is enabled and whether the button is a free kakera button
                        if claim_free:
                            free = buttMoji_lower == "kakerap" or butt["style"] == 3 or buttMoji in ouroSpheres
                        else:
                            free = False

                        cost = get_kakera_cost(kakera_message)
                        allowed_emojis_for_cost = kakera_list.get(cost, [])
                        allowed_by_cost = buttMoji_lower in allowed_emojis_for_cost

                        # Only claim kakera that match the configured cost or free kakera or emoji part of a reaction event
                        if (allowed_by_cost and cooldown <= 0) or free or (mudae_event and buttMoji in eventlist):
                            customid = butt["custom_id"]
                            bot.click(
                                aId,
                                channelID=m["channel_id"],
                                guildID=m.get("guild_id"),
                                messageID=m["id"],
                                messageFlags=m["flags"],
                                data=butts.getButton(customID=customid),
                            )
                            print(f"Claiming {buttMoji} in channel {guildid}.")
                            
                            # Check for kakera wall after claiming
                            warn_check = mudae_warning(channelid)
                            kakerawallwait = wait_for(bot, lambda m: warn_check(m) and '$ku' in m.parsed.auto()['content'], timeout=5)
                            if kakerawallwait is not None:
                                time_to_wait = waitk_finder.findall(kakerawallwait['content'])
                            else:
                                time_to_wait = []

                            if len(time_to_wait):
                                timegetter = (int(time_to_wait[0][0] or "0") * 60 + int(time_to_wait[0][1] or "0")) * 60
                                print(f"{timegetter} second(s) kakera reaction cooldown was set for channel {guildid}.")
                                kakera_wall[guildid] = timegetter + time.time()
                                save_cooldowns()
                                
                                # Check if daily kakera command can be run
                                daily_kakera_cooldown = dailykakera_wall.get(channelid, 0) - time.time()
                                if daily_kakera_cooldown <= 0:
                                    bot.sendMessage(channelid, channel_settings[int(channelid)]['prefix'] + "dk")
                                    dailykakera_wall[channelid] = time.time() + 20 * 60 * 60  # 20 hours cooldown
                                    kakera_wall[guildid] = 0
                                    save_cooldowns()
                                    print(f"Ran daily kakera command in channel {channelid}.")
                                    time.sleep(1)
                                    # Attempt to claim the kakera again
                                    bot.click(
                                        aId,
                                        channelID=m["channel_id"],
                                        guildID=m.get("guild_id"),
                                        messageID=m["id"],
                                        messageFlags=m["flags"],
                                        data=butts.getButton(customID=customid),
                                    )
                                    print(f"Attempting to claim {buttMoji} again in channel {guildid} after running $dk.")

                                    # Check for kakera wall again
                                    kakerawallwait = wait_for(bot, lambda m: warn_check(m) and 'kakera for' in m.parsed.auto()['content'], timeout=5)
                                    if kakerawallwait is not None:
                                        time_to_wait = waitk_finder.findall(kakerawallwait['content'])
                                    else:
                                        time_to_wait = []
                                    if len(time_to_wait):
                                        timegetter = (int(time_to_wait[0][0] or "0") * 60 + int(time_to_wait[0][1] or "0")) * 60
                                        print(f"{timegetter} second(s) kakera reaction cooldown was set for channel {guildid}")
                                        kakera_wall[guildid] = timegetter + time.time()
                                        save_cooldowns()
                                else:
                                    print(f"Skipped {buttMoji} in channel {guildid} due to kakera reaction and $dk cooldown.")
                            time.sleep(0.3)
                        else:
                            print(f"Skipped {buttMoji} in channel {guildid}.")
                return
                
            if(not sniping and roller != user['id']):
                # Sniping disabled by user
                return
            
            if roller == user['id']:
                # confirmed user roll
                c_settings['rolls'] += 1
            
            # Mudae event
            if mudae_event:
                raw_description = embeds[0]["description"]
                # Normalize newlines to spaces for checking
                normalized_description = raw_description.replace("\n", " ")
                if "Click on me, it's free!" in normalized_description:
                    if butts.components != []:
                        custom_id = butts.components[0]["components"][0]["custom_id"]
                        if custom_id:
                            print(f"Event character from {raw_description} detected in channel {channelid}, reacting to it.")
                            bot.click(
                                aId,
                                channelID=m["channel_id"],
                                guildID=m.get("guild_id"),
                                messageID=m["id"],
                                messageFlags=m["flags"],
                                data=butts.getButton(customID=custom_id),
                            )
                            return

            # Waifu claiming
            claiming_cooldown = waifu_wall.get(channelid, 0) - time.time()
            if claiming_cooldown <= 0:
                snipe_delay = get_snipe_time(int(channelid),roller,content)
                charpop = m['embeds'][0]
                charname = charpop["author"]["name"]
                chardes = charpop["description"]
                charcolor = int(charpop['color'])

                if str(user['id']) in content:
                    if msg_buf[messageid]['claimed']:
                        return
                    print(f"Wished character named {charname} from {get_serial(chardes)} with {get_kak(chardes)} value in channel {guildid} has spawned!")
                    waifu_wall[channelid] = next_claim(channelid)[1]
                    save_cooldowns()
                    snipe_character_delay(recv, snipe_delay)
                    snipe_character(m, butts, channelid)
                    # if "reactions" in m_reacts:
                        # if m_reacts["reactions"][0]["emoji"]['id'] == None:
                            # bot.addReaction(channelid, messageid, m_reacts["reactions"][0]["emoji"]["name"])
                        # elif m_reacts["reactions"][0]["emoji"]['id'] != None and "kakera" not in m_reacts["reactions"][0]["emoji"]["name"]:
                            # cust_emoji_sen = m_reacts["reactions"][0]["emoji"]["name"] + ":" + m_reacts["reactions"][0]["emoji"]['id']
                            # bot.addReaction(channelid, messageid, cust_emoji_sen)
                    # elif butts.components != [] :
                        # buttMoji = butts.components[0]["components"][0]["emoji"]["name"]
                        # if "kakera" not in buttMoji:
                            # bot.click(
                                        # aId,
                                        # channelID=m["channel_id"],
                                        # guildID=m.get("guild_id"),
                                        # messageID=m["id"],
                                        # messageFlags=m["flags"],
                                        # data=butts.getButton(emojiName=buttMoji),
                                        # )  
                    # else:
                        # bot.addReaction(channelid, messageid, "❤")
                
                if charname.lower() in chars:
                    print(f"Attempting to snipe {charname} which is in your character name list in channel {guildid}.")
                    waifu_wall[channelid] = next_claim(channelid)[1]
                    save_cooldowns()
                    snipe_character_delay(recv, snipe_delay)
                    if msg_buf[messageid]['claimed']:
                        return
                    snipe_character(m, butts, channelid)
                
                for ser in series_list:
                    if ser in chardes and charcolor == 16751916:
                        print(f"Attempting to snipe {charname} from {ser} which is in your series list in channel {guildid}.")
                        waifu_wall[channelid] = next_claim(channelid)[1]
                        save_cooldowns()
                        snipe_character_delay(recv, snipe_delay)
                        if msg_buf[messageid]['claimed']:
                            return
                        snipe_character(m, butts, channelid)


                if "<:kakera:469835869059153940>" in chardes or "Claims:" in chardes or "Likes:" in chardes:
                    kak_value = get_kak(chardes)
                    if int(kak_value) >= kak_min and charcolor == 16751916:
                        print(f"{charname} with {kak_value} kakera value appeared in channel {guildid}.")
                        waifu_wall[channelid] = next_claim(channelid)[1]
                        save_cooldowns()
                        snipe_character_delay(recv, snipe_delay)
                        if msg_buf[messageid]['claimed']:
                            return
                        snipe_character(m, butts, channelid)
       
                if is_last_enable and next_claim(channelid)[1] - time.time() < (60 * last_claim_window):
                    if "<:kakera:469835869059153940>" in chardes or "Claims:" in chardes or "Likes:" in chardes:
                        kak_value = get_kak(chardes)
                        if int(kak_value) >= min_kak_last and charcolor == 16751916:
                            print(f"{charname} with {kak_value} kakera value appeared in channel {guildid}.")
                            print(f"Attempting last minute claim.")
                            waifu_wall[channelid] = next_claim(channelid)[1]
                            save_cooldowns()
                            snipe_character_delay(recv, snipe_delay)
                            if msg_buf[messageid]['claimed']:
                                return
                            snipe_character(m, butts, channelid)
                
                if str(user['id']) not in content and charname.lower() not in chars and get_serial(chardes) not in series_list and int(get_kak(chardes)) < kak_min:
                    logger.debug(f"Ignoring {charname} from {get_serial(chardes)} with {get_kak(chardes)} Kakera Value in Server id:{guildid}")

                
    if resp.event.message_updated:
        # Handle claims
        r = resp.parsed.auto()
        rchannelid = r["channel_id"]
        rmessageid = r["id"]
        #embeds = r['embeds']
        embeds = r.get('embeds',[])

        if int(rchannelid) not in mhids:
            return
        try:
            if r['author']['id'] == str(mudae):
                if not is_rolled_char(r):
                    return
                embed = embeds[0]
                f = embed.get('footer')
                if f and user['username'] in f['text']:
                    # Successful claim, mark waifu claim window as used
                    print(f"Successfully claimed character in channel {rchannelid}.")
                    waifu_wall[rchannelid] = next_claim(rchannelid)[1]
                    save_cooldowns()
                elif int(embed['color']) == 6753288:
                    # Someone else has just claimed this, mark as such
                    msg_buf[rmessageid]['claimed'] = True
                    waifu_wall.pop(rchannelid, None)
                    save_cooldowns()
        except KeyError:
            pass

    if resp.event.reaction_added:
        r = resp.parsed.auto()
        reactionid = int(r['user_id'])
        rchannelid = r["channel_id"]
        rmessageid = r["message_id"]
        rguildid = r["guild_id"]
        emoji = r["emoji"]["name"]
        emojiid = r["emoji"]['id']

        if int(rchannelid) not in mhids:
            # Not a channel we work in.
            return
        
        if int(rchannelid) not in channel_settings:
            mhids.remove(int(rchannelid))
            logger.error(f"Could not find settings for channel {rchannelid}, please trigger the '$settings' command in that channel and run the bot again.")
            return
        
        if reactionid == int(user['id']) and int(rchannelid) in mhids:
            print(f"Sniping time waited, reaction was added.")

        # snipe_delay = channel_settings[int(rchannelid)]['kak_snipe'][1]
        
        # if reactionid == mudae and int(rchannelid) in mhids:
            
            # if emojiid != None and emoji == "kakeraP" and (snipe_delay == 0 or msg_buf[rmessageid]['rolled']):
            #     sendEmoji = emoji + ":" +emojiid
            #     react_m = bot.getMessage(rchannelid, rmessageid).json()[0]['embeds'][0]
            #     time.sleep(1)
            #     bot.addReaction(rchannelid,rmessageid,sendEmoji)
                
            # if emojiid != None and emoji.lower() in KakeraVari:
            #     sendEmoji = emoji + ":" +emojiid
            #     react_m = bot.getMessage(rchannelid, rmessageid).json()[0]['embeds'][0]
                
            #     cooldown = kakera_wall.get(rguildid,0) - time.time()
            #     if cooldown <= 1:
            #         print(f"{emoji} was detected on {react_m['author']['name']}:{get_serial(react_m['description'])} in Server: {rguildid}")
            #         time.sleep(snipe_delay)
            #         bot.addReaction(rchannelid,rmessageid,sendEmoji)
            #     else:
            #         print(f"Skipped {emoji} found on {react_m['author']['name']}:{get_serial(react_m['description'])} in Server: {rguildid}")
            #         return 

            #     warn_check = mudae_warning(rchannelid)
            #     kakerawallwait = wait_for(bot,lambda r: warn_check(r) and 'kakera' in r.parsed.auto()['content'],timeout=5)

            #     if kakerawallwait != None:
            #         time_to_wait = waitk_finder.findall(kakerawallwait['content'])
            #     else:
            #         time_to_wait = []
                
            #     if len(time_to_wait):
            #         timegetter = (int(time_to_wait[0][0] or "0")*60+int(time_to_wait[0][1] or "0"))*60
            #         print(f"{timegetter} second(s) kakera reaction cooldown was set for channel : {rguildid}")
            #         kakera_wall[rguildid] = timegetter + time.time()
                    
            # if emojiid != None and emoji.lower() in soulLink:
            #     react_m = bot.getMessage(rchannelid, rmessageid).json()[0]['embeds'][0]
            #     fake = react_m.get('footer')

            #     if fake and user['username'] in fake['text'] and "<:chaoskey:690110264166842421>" in react_m['description']:
            #         sendEmoji = emoji + ":" +emojiid
            #         cooldown = kakera_wall.get(rguildid,0) - time.time()
            #         if cooldown <= 1:
            #             print(f"{emoji} was detected on {react_m['author']['name']}:{get_serial(react_m['description'])} in Server: {rguildid}")
            #             time.sleep(snipe_delay)
            #             bot.addReaction(rchannelid,rmessageid,sendEmoji)
            #         else:
            #             print(f"Skipped {emoji} found on {react_m['author']['name']}:{get_serial(react_m['description'])} in Server: {rguildid}")
            #             return 

            #         warn_check = mudae_warning(rchannelid)
            #         kakerawallwait = wait_for(bot,lambda r: warn_check(r) and 'kakera' in r.parsed.auto()['content'],timeout=5)

            #         if kakerawallwait != None:
            #             time_to_wait = waitk_finder.findall(kakerawallwait['content'])
            #         else:
            #             time_to_wait = []
                    
            #         if len(time_to_wait):
            #             timegetter = (int(time_to_wait[0][0] or "0")*60+int(time_to_wait[0][1] or "0"))*60
            #             print(f"{timegetter} for kakera_wall was set for Server : {rguildid}")
            #             kakera_wall[rguildid] = timegetter + time.time()
                    
            # if emojiid == None:
            #     if emoji in eventlist:
            #         print(f"{emoji} was detected in Server: {rguildid}")
            #         time.sleep(snipe_delay)
            #         bot.addReaction(rchannelid,rmessageid,emoji)
          
    if resp.event.guild_application_commands_updated:
        guild_id = resp.parsed.auto()['guild_id']
        slashCmds = bot.getGuildSlashCommands(guild_id).json()["application_commands"]
        s = SlashCommander(slashCmds, application_id=str(mudae))
        # Find both rolling slash and daily slash
        global slash_daily_cmd
        global slash_sphere_cmd
        for sli in range(len(s.commands.get("options"))):
            option = s.commands.get("options")[sli]
            name = option.get("name")
            if name == slash_prefix:
                slashget = option
                if settings['slash_rolling'].lower().strip() == "true" and slashget != None:
                    for xchg in range(len(shids)):
                        slashchannel = shids[xchg]
                        slashfus = threading.Timer(10.0,waifu_roll,args=[slashchannel,slashget])
                        slashfus.start()
            elif name == "daily":
                slash_daily_cmd = option
            elif name == "sphere":
                for sub in option.get("options") or []:
                    if sub.get("name") == "chest":
                        # /sphere chest, shaped like the data Discord itself sends.
                        slash_sphere_cmd = {
                            "name": option["name"],
                            "type": option["type"],
                            "id": option["id"],
                            "version": option["version"],
                            "options": [{"name": sub["name"], "type": sub["type"], "options": []}],
                        }
                        print(f"Found the /sphere chest slash command in guild {guild_id}.")
            
    global ready
 
    if resp.event.ready_supplemental and not ready:
        ready = bot.gateway.READY
        try:
            user = bot.gateway.session.user
            print(f"Logged in.")
        except KeyError:
            print(f"Unable to retrieve user information with Discum. Please ensure you are using a updated version of Discum.")
            raise

        guildID = guild_id_from_channel(mhids[0])
        # Rate limit of 1 request every 5 seconds
        bot.gateway.request.searchSlashCommands(str(guildID), limit=100, query=slash_prefix)
        
        try:
            guilds = bot.gateway.session.settings_ready['guilds']
        except KeyError:
            print("Unable to retrieve guild information with Discum. Please ensure you are using a updated version of Discum.")
            raise
                
        chs = set(str(mhid) for mhid in mhids)
        for gid, guild in guilds.items():
            for matched_channel in (set(guild['channels'].keys()) & chs):
                # Find associated guild ID to a monitored channel, then get settings
                msg = get_server_settings(gid,matched_channel)
                c_settings = parse_settings_message(msg)
                channel_settings[int(matched_channel)] = c_settings
        
        if settings['daily_claiming'].lower().strip() == "true":
            time.sleep(3)
            d = threading.Thread(target=daily_roll_reset,args=[mhids[0], slash_daily_cmd])
            d.start()
        if ourochest_enabled:
            # One scheduler per monitored channel, since the attempt is per channel.
            for chid in mhids:
                ocs = threading.Thread(target=ourochest_daily,args=[chid])
                ocs.start()
        if settings['poke_rolling'].lower().strip() == "true":
            time.sleep(3)
            p = threading.Thread(target=poke_roll,args=[mhids[0]])
            p.start()
        if settings['rolling'].lower().strip() == "true":
            for chid in mhids:
                waifus = threading.Timer(10.0,waifu_roll,args=[chid,None,None])
                waifus.start()
                

def empty(*args,**kwargs):
    return

#bot.sendMessage = empty

bot.gateway.run(auto_reconnect=False)