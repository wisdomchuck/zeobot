import xml.etree.ElementTree as etree

from discord.ext import commands
from steam import WebAPI
from steam import SteamID
from steam.enums import EPersonaState
from utils.config import Config
from utils.tools import *
from utils import checks
from datetime import datetime
config = Config()

steamAPI = WebAPI(config._steamAPIKey)

class Steam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @checks.is_dev()
    async def steamdebug(self, ctx, *, shit: str):
        """This is the part where I make 20,000 typos before I get it right"""
        # "what the fuck is with your variable naming" - EJH2
        # seth seriously what the fuck - Robin
        import asyncio
        import os
        import random
        import re
        from datetime import datetime, timedelta
        try:
            rebug = eval(shit)
            if asyncio.iscoroutine(rebug):
                rebug = await rebug
            await ctx.send(py.format(rebug))
        except Exception as damnit:
            await ctx.send(py.format("{}: {}".format(type(damnit).__name__, damnit)))

    @commands.command()
    async def steamuser(self, ctx, communityid:str):
        """Gets steam profile information on a user with the specified community ID"""
        await ctx.channel.trigger_typing()
        steamID = SteamID.from_url("http://steamcommunity.com/id/{}".format(communityid))
        if steamID is None:
            steamID = communityid
        try:
            steamUser = steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steamID)["response"]["players"][0]
        except IndexError:
            await ctx.send("User not found! Make sure you are using steam community IDs!")
            return
        bans = steamAPI.ISteamUser.GetPlayerBans_v1(steamids=steamID)["players"][0]
        vacBanned = bans["VACBanned"]
        communityBanned = bans["CommunityBanned"]
        ban_info = {"VAC Banned":vacBanned, "Community Banned":communityBanned}
        if vacBanned:
            ban_info["VAC Bans"] = bans["NumberOfVACBans"]
            ban_info["Days Since Last VAC Ban"] = bans["DaysSinceLastBan"]
        if steamUser["communityvisibilitystate"] != 3:
            embed = make_list_embed(ban_info)
            embed.description = "This profile is private."
            embed.title = steamUser["personaname"]
            embed.color = 0xFF0000
            embed.url = steamUser["profileurl"]
            embed.set_thumbnail(url=steamUser["avatarfull"])
            await ctx.send(embed=embed)
            return
        groupCount = len(steamAPI.ISteamUser.GetUserGroupList_v1(steamid=steamID)["response"]["groups"])
        games = requests.get("http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={}&steamid={}&include_played_free_games=1%format=json".format(config._steamAPIKey, steamID)).json()["response"]
        gamesPlayed = games["game_count"]
        state = EPersonaState(steamUser["personastate"]).name
        gameName = None
        if "gameid" in steamUser.keys():
            state = "In-game"
            gameID = steamUser["gameid"]
            gameName = requests.get("http://store.steampowered.com/api/appdetails?appids={}".format(gameID)).json()[gameID]["data"]["name"]
        lastOnline = format_time(datetime.fromtimestamp(steamUser["lastlogoff"]))
        creationDate = format_time(datetime.fromtimestamp(steamUser["timecreated"]))
        fields = {"Status":state, "Created on":creationDate, "Group Count":groupCount, "Games Owned":gamesPlayed}
        if state == EPersonaState.Offline.name:
            fields["Last Online"] = lastOnline
        if gameName:
            fields["Currently Playing"] = gameName
        if "primaryclanid" in steamUser.keys():
            fields["Primary Group Name"] = etree.fromstring(requests.get("http://steamcommunity.com/gid/{}/memberslistxml".format(steamUser["primaryclanid"])).text).find("groupDetails/groupName").text
        fields.update(ban_info)
        embed = make_list_embed(fields)
        embed.title = steamUser["personaname"]
        embed.color = 0xFF0000
        embed.url = steamUser["profileurl"]
        embed.set_thumbnail(url=steamUser["avatarfull"])
        await ctx.send(embed=embed)

    @commands.command()
    async def steamid(self, ctx, communityid:str):
        """Gets a steam id in all formats"""
        await ctx.channel.trigger_typing()
        steamID = SteamID.from_url("http://steamcommunity.com/id/{}".format(communityid))
        if steamID is None:
            steamID = SteamID(communityid)
        try:
            name = steamAPI.ISteamUser.GetPlayerSummaries_v2(steamids=steamID)["response"]["players"][0]["personaname"]
        except IndexError:
            await ctx.send("User not found! Make sure you are using steam community IDs!")
            return
        await ctx.send(xl.format("Steam ID formats for {}:\nSteamID2: {}\nSteamID2Zero: {}\nSteamID3: {}\nSteamID32: {}\nSteamID64: {}").format(name, steamID.as_steam2, steamID.as_steam2_zero, steamID.as_steam3, steamID.as_32, steamID.as_64))


def setup(bot):
    bot.add_cog(Steam(bot))
