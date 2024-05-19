This script might have to be rewritten using `discord.py-self` due to `Discord-S.C.U.M` being unmaintained.
https://github.com/dolfies/discord.py-self

# Regarding Forking
I have seen many users fork this repo. I do not mind forks but I really would like to state that github is a public space and that any user who forks this repo is ultimatly can be found by all the various users that frequent this repo. 

!!!!!!! IF YOU FORK THIS REPO PLEASE DO NOT PUSH A COMMIT WITH YOUR DISCORD USER TOKEN !!!!!!

I personally have tried to email users that I have found that posted their token
 >>> If you have posted your token Please delete said fork and just refork this repo github has a histroy of commits and I can find your token if its posted so again I would like to state

!!!!!!! IF YOU FORK THIS REPO PLEASE DO NOT PUSH A COMMIT WITH YOUR DISCORD USER TOKEN !!!!!!


# Regarding Issue Creation
Lately I have been getting alot of **Issues** that is not based on problems with the bot but they regard `Python Enviroment Errors` I.E `discum module not found`/`discum not installed properly` I have attempted to help many users that have had this problem but it is very time consuming. Python Enviroment issues are not a problem with the **BOT** but how one has installed python this varies from user to user.There are archived issues where a user has had a enviroment issue and they have resolved it you can use that as a reference.
If these resources do not help there are plently of resources online to help you resolve your `Python Enviroment` Issue


`FAQS`
+ CMD closes instantly - Open with IDLE and run it and it should give you the reason that it closed
+ JSON load error - https://jsonformatter.curiousconcept.com/# copy and paste your json file into the textbox and click validate
+ Does it have `gateway` log data ? - Your using older version of Dis.c.u.m refer to their github: https://github.com/Merubokkusu/Discord-S.C.U.M
+ How is bot suppose to look like in normal state - 
![image](https://user-images.githubusercontent.com/33008397/123542012-47927e00-d715-11eb-9bf9-26c78a9721d7.png)

+ Claims / Bot didn't claim X character - Please make sure you have checked if the `bot has not claimed already within the claim window` , or that `someone else did not already claim X character before the snipe protection has expired`

**Future Issues opened that do NOT deal with a Error with the BOT will be labeled accordingly and closed**

# MudaeAutoBot
MudaeAutoBot is a python bot that auto rolls and attempts to snipe Kakeras and Claims in Mudae

# Features
+ Snipes and claims Kakera in any Discord servers you're in that has Mudae#0807
+ Kakera value sniping as long as kakera value can be determined (e.g. Like Rank, Claim Rank, ## Kakera)
+ Maximizes rolls by tracking roll timers
+ Waifu/Husbando rolling
+ Pokeslot rolling
+ Selective Kakera Reaction Snipes Features(Includes: Soulmate Kak sniping Feature)
+ Mudae emoji reaction event sniping support

## How it works
All this bot needs to work is your Discord token, username, user ID, the channel IDs and server IDs that you want it to roll in.

This is intended to be completely automated; it doesn't need to take any input other than initial settings configuration.
You'll be able to leave the window running in the background, and not need to think about it.

## Requirements

+ Python 3.7+
+ Git https://git-scm.com/downloads
+ Discum from this fork `pip install git+https://github.com/Nixeld/Discord-S.C.U.M.git`
  >uninstall first if you have the one from the original repo

# Configuration
To configure the bot, you'll edit the variables in the `Settings_Mudae.json` file for your botting needs.
Change the guild and channel ids in `guild.txt` as well as username and user id in the `user.txt` under the user folder.

## Bot settings
All settings are set within the Settings_Mudae.json file.
Some settings may be superseded by your Mudae server settings.

+ `token` - The user token for the account you want to bot on. If you need extra assistance on how to obtain it, let me know.
+ `channelids` - Which channels to **Roll** and **monitor**  e.g. 807##########948 (Channel ID)
+ `slash_ids` - Which channels to **Slash roll** e.g. 807##########948 (Channel ID)
+ `slash_guild_ids` - Which Guild to **Slash roll** e.g. 807##########948 (Server ID)
+ `claim_delay` - _Affects servers w/o $setting instance_ Time in **seconds** to wait before attempting to Claim Characters e.g. 5
+ `kak_delay` - _Affects servers w/o $setting instance_ Time in **seconds** to wait before attempting to snipe Kakeraloot e.g. 8
+ `use_emoji` - This setting only works if you change the Mudaebot.py code by uncommenting out the line (Custom emojis only) e.g.  "<:emoji_name:795############214>"
+ `roll_this` - (m|ma|mg|w|wg|wa|h|ha|hg) If `rolling` is enabled it will roll this specific command e.g. '$wg'
+ `slash_this` - (wa|wx|wg|hg|ha|mg|ma|mx) If `slash_rolling` is enabled it will roll this specific command e.g. '/wg'
+ `rolling` - (True|False) **Case-sensitive**, uses `channelid`
+ `slash_rolling` - (True|False) **Case-sensitive**, uses `Slash_ids`
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

# Use at your own Risk
This is a Discord **selfbot**. I am not responsible if you get banned using this program. 

# Closing Notes
This is forked from https://github.com/vivinano/MudaeAutoBot and I will try to see if we can support this repo.

Thanks to:
https://github.com/vivinano for this MudaeAutoBot 
and
https://github.com/FatPain
for assisting vivinano with Discum

