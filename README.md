# MudaeAutoBot
MudaeAutoBot is a python bot that auto rolls and attempts to snipe Kakeras and Claims in Mudae

# Features
+ Snipes and claims Kakera in any Discord servers you're in that has Mudae#0807
+ Kakera value sniping as long as kakera value can be determined (e.g. Like Rank, Claim Rank, ## Kakera)
+ Maximizes rolls by tracking roll timers
+ Waifu/Husbando rolling
+ Pokeslot rolling
+ Selective Kakera Reaction Snipes Features (Includes: Soulmate Kak sniping Feature)
+ Mudae emoji reaction event sniping support

## How it works
All this bot needs to work is your Discord token, channel IDs and server IDs that you want to roll in.

This is intended to be completely automated; it doesn't need to take any input other than initial settings configuration.
You'll be able to leave the window running in the background, and not need to think about it.

## Requirements
+ Python 3.7+
+ Git https://git-scm.com/downloads (Required for installing Discum from github)
+ Discum from this fork `pip install git+https://github.com/Nixeld/Discord-S.C.U.M.git`

## Running the bot
To run the bot, run `AutoReconnect.py` in a terminal with this command. `python .\AutoReconnect.py`<br />
If you do not want it to auto reconnect whenever MudaeAutoBot disconnects, you can run `MudaeAutoBot.py` instead.

# Configuration
To configure the bot, you'll edit the variables in the `Settings_Mudae.json` file for your botting needs.<br />

Discum may fail to retrieve user and server information for some people, when that happens you will need to: <br />
+ Set your guild and channel ids in `guild.txt` found in the user folder.
+ Set your username and user id in the `user.txt` found in the user folder.

## Bot settings
All settings are set within the Settings_Mudae.json file.
Some settings may be superseded by your Mudae server settings.

+ `token` - The user token for the account you want to bot on. If you need extra assistance on how to obtain it, let me know.
+ `channelids` - Which channels to **Prefix Roll** and **monitor**  e.g. 807##########948 (Channel ID)
+ `slash_ids` - Which channels to **Slash roll** e.g. 807##########948 (Channel ID)
+ `slash_guild_ids` - Which Guild to **Slash roll** e.g. 807##########948 (Server ID)
+ `claim_delay` - _Affects servers w/o $setting instance_ Time in **seconds** to wait before attempting to Claim Characters e.g. 5
+ `kak_delay` - _Affects servers w/o $setting instance_ Time in **seconds** to wait before attempting to snipe Kakeraloot e.g. 8
+ `use_emoji` - This setting only works if you change the Mudaebot.py code by uncommenting out the line (Custom emojis only) e.g.  "<:emoji_name:795############214>"
+ `roll_this` - (m|ma|mg|w|wg|wa|h|ha|hg) If `rolling` is enabled it will roll this specific command e.g. '$wg'
+ `slash_this` - (wa|wx|wg|hg|ha|mg|ma|mx) If `slash_rolling` is enabled it will roll this specific command e.g. '/wg'
+ `rolling` - (True|False) **Case-sensitive**, uses `channelid` to **Prefix Roll**
+ `slash_rolling` - (True|False) **Case-sensitive**, uses `slash_ids` to **Slash roll**
+ `random_rolling` - (True|False) **Case-sensitive**, Random roll time between the each reset.
+ `daily_kakera` - (True|False) **Case-sensitive**, Enables the bot to automatically run the $dk (daily kakera) command when kakera reaction cooldown is detected. Set to "True" to enable.
+ `reset_claim_timer` - (True|False) **Case-sensitive**, If enabled, the bot will attempt to run the $rt command when it is needs to claim a character but it is still on cooldown. Set to "True" to enable.
+ `reset_claim_timer_cooldown` - (integer, in hours) Set this value to your cooldown time for the $rt command. You can find your cooldown time by running $bonus.
+ `daily_claiming` - (True|False) **Case-sensitive**, Trigger $daily command everyday
+ `poke_rolling` - (True|False) **Case-sensitive**, Pokeslot rolling enabled, uses `channelid`
+ `series_list` - **Case-sensitive** Name of series of characters you want to claim  e.g. \[ "Honkai Impact 3rd" , "Senran Kagura" \]
+ `name_list` - **Must be exact match** List of specific character names to claim  e.g. \["Raiden Mei", "gOkU" \]
+ `emoji_list` - This is the kakera that will be snipes \[ "KakeraY" , "KakeraO" \] << This example means only snipe Yellow and orange Kakera
+ `min_kak` - A minimum kakera value to snipe a claimable character _regardless of whether it's in the series/name lists_
+ `last_true` -  (True|False) Enable last minute claim window
+ `last_claim_min` - (1-180) the time the window is open for e.g. 10 means last 10 minutes
+ `min_kak_last_min` - same as min kak but only within the last minute claim window

# Optimize the snipes
Typing $settings in your server with mudae should give you the snipe and kaksnipping timers.
Using these values you usually snipes faster than a "Human" user can react 

Please when settings delays avoid setting 0 as your delay as it might be to fast for mudae
a minimum of 1 second to let mudae register that a character was rolled as is reacted to.

# Regarding Issue Creation
Before creating an issue, search through all the issues (including closed issues) on the repository to see if any of them solves your problem.<br /><br />
Verify that you have the latest version of Discum from this fork https://github.com/Nixeld/Discord-S.C.U.M.git.<br />
Latest version is `1.4.3`, you can check your Discum version with `pip show discum`.<br /><br />
If that does not solve your problem, please provide as much detail as possible when you create your issue so we can quickly identify the problem. (eg. settings file without your user token, screenshots of error)

# Regarding Forking
I have seen many users fork this repo. I do not mind forks but I really would like to state that github is a public space and that any user who forks this repo is ultimatly can be found by all the various users that frequent this repo. 

!!!!!!! IF YOU FORK THIS REPO PLEASE DO NOT PUSH A COMMIT WITH YOUR DISCORD USER TOKEN !!!!!!

I personally have tried to email users that I have found that posted their token
 >>> If you have posted your token, please delete said fork and just refork this repo github has a history of commits and I can find your token if its posted so again I would like to state

!!!!!!! IF YOU FORK THIS REPO PLEASE DO NOT PUSH A COMMIT WITH YOUR DISCORD USER TOKEN !!!!!!

# Use at your own Risk
This is a Discord **selfbot**. I am not responsible if you get banned using this bot. 

# Closing Notes
This is forked from https://github.com/vivinano/MudaeAutoBot and we will try to maintain this repo.

Thanks to:
https://github.com/vivinano for MudaeAutoBot 
and
https://github.com/FatPain
for assisting vivinano with Discum.

