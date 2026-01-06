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
ghids = [int(gh) for gh in settings["slash_guild_ids"]]
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

KakeraVari = [kakerav.lower() for kakerav in settings["emoji_list"]]
soulLink = [soulkakerav.lower() for soulkakerav in settings["soulemoji_list"]]
eventlist = ["🕯️","😆","🍫","🎀","🧸","🎄"]

#Last min Claims
is_last_enable = True if settings["last_true"].lower().strip() == "true" else False 
last_claim_window = settings["last_claim_min"]
min_kak_last = settings["min_kak_last_min"]

kakera_wall = {}
waifu_wall = {}
dailykakera_wall = {}
resetclaimtimer_wall = {}
daily_roll_reset_wall = 0.0

COOLDOWNS_FILE = pathjoin('user', 'cooldowns.json')

def load_cooldowns():
    """Load cooldown timers from file."""
    global kakera_wall, waifu_wall, dailykakera_wall, resetclaimtimer_wall, daily_roll_reset_wall
    try:
        with open(COOLDOWNS_FILE, 'r', encoding='utf-8') as f:
            cooldowns = json.load(f)
            # Use string keys to match Discord IDs (channel_id, guild_id) used elsewhere
            kakera_wall = {str(k): float(v) for k, v in cooldowns.get('kakera_wall', {}).items()}
            waifu_wall = {str(k): int(v) for k, v in cooldowns.get('waifu_wall', {}).items()}
            dailykakera_wall = {str(k): float(v) for k, v in cooldowns.get('dailykakera_wall', {}).items()}
            resetclaimtimer_wall = {str(k): float(v) for k, v in cooldowns.get('resetclaimtimer_wall', {}).items()}
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
            # must be from relevant channel id, and start with username
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
            # must be from relevant channel id and message sent from mudae
            if r['author']['id'] == str(mudae) and r['channel_id'] == channel_id:
                # return true if relevant claim message
                return (r['content'].startswith('<@' + user['id'] + '>') and "you can claim once per interval" in r['content']) or r['content'].startswith(f"*💖 *{user['username']}")
        return False
    return c

def msg_checking(msgcontent):
    msgtocheck = ["maintenance"] #list to check incase bot is down
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

def daily_roll_reset(slashchannel, slashguild, slash_daily_cmd):
    if not slashchannel or not slashguild:
        logger.error(f"Could not find channel {slashchannel} or guild {slashguild}, will not collect daily roll reset.")
        return
    global daily_roll_reset_wall
    while True:
        # Respect stored cooldown (single global timestamp)
        cooldown_remaining = daily_roll_reset_wall - time.time()
        if cooldown_remaining > 0:
            print(f"Daily roll reset on cooldown, {round(cooldown_remaining)} seconds until next claim.")
            time.sleep(max(cooldown_remaining, 1))
            continue

        bot.triggerSlashCommand(str(mudae), channelID=slashchannel, guildID=slashguild, data=slash_daily_cmd)
        # Default: 30 minutes if timeout or invalid state/format
        cooldown_seconds = 30 * 60
        resp = wait_for(bot, daily_message_check(slashchannel), timeout=5)
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
                    # Neither ✅ nor a recognizable cooldown text
                    print(f"Failed to claim daily roll reset, retrying in {round(cooldown_seconds)} seconds.")
                    print(content)
        # Store cooldown timestamp and loop
        daily_roll_reset_wall = time.time() + cooldown_seconds
        save_cooldowns()
        
def waifu_roll(tide,slashed,slashguild):
    global user
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
                bot.triggerSlashCommand(str(mudae), channelID=tides, guildID=slashguild, data=slashed)
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
        print(f"Finish rolling for waifus in channel {tide}. Next roll in {round(((next_reset(tide)-time.time())+1) + offset_random)} seconds.")
        time.sleep((next_reset(tide)-time.time())+1+offset_random)
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
                    print(f"Attempting to snipe the character again in channel {channelid} after running $rt.")
                    snipe_character(messagechunk, buttonspres, channelid)
            else:
                    print(f"Skipped running $rt in channel {channelid} due to cooldown.")
        else:
            # Successful claim message
            print(f"Successfully claimed character in channel {channelid}.")

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
                        # Claim kakera if it is in emoji list or soul emoji list after validation. If kakeraP is in any of the list, it will be claimed without checking cooldown.
                        if (buttMoji.lower() in KakeraVari and cooldown <= 0) or (buttMoji.lower() in soulLink and cooldown <= 0 and user['username'] in kakera_message.get('footer')['text'] and "<:chaoskey:690110264166842421>" in kakera_message['description']) or (buttMoji.lower() == "kakerap" and ("kakerap" in KakeraVari or "kakerap" in soulLink)):
                            time.sleep(0.3)
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
                                    time.sleep(0.3)
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
                        else:
                            print(f"Skipped {buttMoji} in channel {guildid}.")
                return
                
            if(not sniping and roller != user['id']):
                # Sniping disabled by user
                return
            
            if roller == user['id']:
                # confirmed user roll
                c_settings['rolls'] += 1
            
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
                    print(f"Successfully detected claimed character in channel {rchannelid}.")
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
        for sli in range(len(s.commands.get("options"))):
            option = s.commands.get("options")[sli]
            name = option.get("name")
            if name == slash_prefix:
                slashget = option
                if settings['slash_rolling'].lower().strip() == "true" and slashget != None:
                    for xchg in range(len(shids)):
                        slashchannel = shids[xchg]
                        slashguild = ghids[xchg]
                        slashfus = threading.Timer(10.0,waifu_roll,args=[slashchannel,slashget,slashguild])
                        slashfus.start()
            elif name == "daily":
                slash_daily_cmd = option
            
    global ready
 
    if resp.event.ready_supplemental and not ready:
        ready = bot.gateway.READY
        try:
            user = bot.gateway.session.user
            print(f"Logged in.")
        except KeyError:
            print(f"Unable to retrieve user information with Discum. Please ensure you are using a updated version of Discum.")
            raise
        bot.gateway.request.searchSlashCommands(str(ghids[0]), limit=100, query=slash_prefix)
        
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
            d = threading.Thread(target=daily_roll_reset,args=[shids[0], ghids[0], slash_daily_cmd])
            d.start()
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