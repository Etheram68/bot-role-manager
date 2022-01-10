import discord
import asyncio
from discord.ext import commands
from discord.ext.commands import MissingPermissions
from discord.utils import get
from random import randrange
from src.dao.daoFactory import DaoFactory, ValueExistError


class RoleManage(commands.Cog):

    def __init__(self, bot, db):
        self.bot = bot
        self.db = db
        self.role_list = list()
        self.emoji_list = list()
        self.__private_colors = [0xff0000, 0xa8009a, 0x001eff, 0x00d5ff, 0x00ff2a,
								 0xffdd00, 0xff4000, 0xffffff, 0x7756d2]
        self.__private_colors_nb = len(self.__private_colors)

    async def __send_advert_exit__(self, ctx, message):
        await ctx.author.send(message)
        await ctx.message.delete()
        if len(self.role_list) > 0:
            [await r.delete() for r in self.role_list]
        return

    async def __create_view_embed__(self):
        i = 0
        message = list()
        embed = discord.Embed(title=f'**Manager Roles: **', description=f"", \
								color=self.__private_colors[randrange(self.__private_colors_nb)])
        for i in range(len(self.role_list)):
            message.append(f'**{self.emoji_list[i]} : {self.role_list[i].name}**\n')
        embed.add_field(name=f'***Notification roles for event ***', value=''.join(message), inline=False)
        embed.set_footer(text="*Choose your role to get the notifications that concern you*")
        return embed

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id is None:
            return

        self.role_list = list()
        self.emoji_list = list()
        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)

        if user.id != self.bot.user.id:
            lst_roles_db = self.db.get_role_table(guild.id)
            for e in lst_roles_db:
                self.role_list.append(get(guild.roles, id=e[1]))
            lst_emoji = self.db.get_emoji_table(guild.id)
            for e in lst_emoji:
                self.emoji_list.append(e[1])
                for i,e in enumerate(self.emoji_list):
                    if str(payload.emoji) == e:
                        await user.add_roles(self.role_list[i])
        return

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id is None:
            return

        self.role_list = list()
        self.emoji_list = list()
        guild = self.bot.get_guild(payload.guild_id)
        user = guild.get_member(payload.user_id)

        if user.id != self.bot.user.id:
            lst_roles_db = self.db.get_role_table(guild.id)
            for e in lst_roles_db:
                self.role_list.append(get(guild.roles, id=e[1]))
            lst_emoji = self.db.get_emoji_table(guild.id)
            for e in lst_emoji:
                self.emoji_list.append(e[1])
                for i,e in enumerate(self.emoji_list):
                    if str(payload.emoji) == e:
                        await user.remove_roles(self.role_list[i])
        return

    @commands.command(name="help")
    async def help_manager(self, ctx):
        embed = discord.Embed(title="Help", description="", color=0x7289da)
        # embed.set_author(name=f"{ctx.guild.me.display_name}", icon_url=f"{ctx.guild.me.avatar_url}")
        embed.add_field(name=f'**Commands**', value=f'**Create Role Manager:**\n\n`>add-manager`\n\n------------\n\n'
                                f'**Remove old request group:**\n\n`>remove-manager`\n\n------------\n\n'
                                f'**Print man help:**\n\n`>help`\n\n', inline='false')
        await ctx.channel.send(embed=embed)
        await ctx.message.delete()
        return

    @commands.command(name="remove-manager")
    @commands.has_permissions(manage_roles=True)
    async def remove_manage_role(self, ctx):
        self.role_list = list()
        guild = ctx.guild
        guildID = ctx.guild.id

        channel_id = self.db.get_id_channel(guildID)
        id_mess = self.db.get_id_mess(guildID)
        chanel = self.bot.get_channel(int(channel_id[0]))
        msg = await chanel.fetch_message(id_mess[0]) if chanel else None

        lst_roles_db = self.db.get_role_table(guildID)
        for e in lst_roles_db:
            role = get(guild.roles, id=e[1])
            self.role_list.append(role) if role else None

        [await r.delete() for r in self.role_list] if len(self.role_list) > 0 else None

        self.db.remove_all_elem(guildID)

        await msg.delete() if msg else None
        await ctx.author.send("***Role Manager and roles successfully deleted***")
        await ctx.message.delete()
        return

    @remove_manage_role.error
    async def remove_manage_role_error(self, error, ctx):
        if isinstance(error, MissingPermissions):
            await ctx.author.send(f'***Error: You are missing Administrator permission(s) to run this command***')
            await ctx.message.delete()


    @commands.command(name="add-manager")
    @commands.has_permissions(manage_roles=True)
    async def create_manage_role(self, ctx):
        guildID = ctx.guild.id
        ownerID = ctx.author.id
        channelID = ctx.message.channel.id
        finish = False
        self.role_list = list()
        self.emoji_list = list()

        try:
            self.db.check_guild_table(guildID)
        except ValueExistError:
            await ctx.author.send('***Error: You can only have one role manager***\n' \
                                    '*Please use command `>remove-manager` for remove role manager*')
            await ctx.message.delete()
            return

        def check(m):
            return m.author == ctx.author and isinstance(m.channel, discord.channel.DMChannel)

        await ctx.author.send(f'**You have 60 second to answer each Questions! **\n'
                                '**Check if you have start command on channel where you print Embed **\n'
                                f"*Send `exit` if you have finish*\n"
                                '**\nPhase 1: Enter name of Role: (e.g  `God`) **')

        while 1 and not finish:
            try:
                r = await self.bot.wait_for('message',check=check, timeout=60.0)
                r = r.content.capitalize()
                if r == 'Exit':
                    finish = True
                    continue
                r = await ctx.guild.create_role(name=r, mentionable=True, colour=0xf1c40f)
                await ctx.author.send(f"**Role `{r.name}` created**\n" \
                                        f"*Send `exit` for stop*\n")
                self.role_list.append(r)
            except asyncio.TimeoutError:
                await self.__send_advert_exit__(ctx, '*Took too long to answer!*')
                return
            except discord.Forbidden as message:
                await self.__send_advert_exit__(ctx, message)
                return

        await ctx.author.send(f"**Phase 2: Choose emojii **\n" \
                                    f"*Send `exit` for stop*\n")

        for r in self.role_list:
            await ctx.author.send(f'**Send Emoji used for choose role `{r.name}`: (e.g  `❌`) **')
            try:
                r = await self.bot.wait_for('message',check=check, timeout=60.0)
                if r.content.capitalize() == 'Exit':
                    await self.__send_advert_exit__(ctx, '*You send exit, Bye!*')
                    return
                self.emoji_list.append(r.content)
            except asyncio.TimeoutError:
                await self.__send_advert_exit__(ctx, '*Took too long to answer!*')
                return
        await ctx.author.send(f'*Please wait i create your embed ...*')
        [self.db.set_role_table(guildID, r.id, r.name) for r in self.role_list]
        [self.db.set_emoji_table(guildID, e) for e in self.emoji_list]
        embed = await self.__create_view_embed__()
        mess = await ctx.message.channel.send(embed=embed)
        for emoji in self.emoji_list:
            await mess.add_reaction(emoji)
        self.db.set_guild_table(guildID, ownerID, mess.id, channelID)
        await ctx.author.send(f'***Embed for choose role on channel {ctx.message.channel.name} successfully Creating***')
        await ctx.message.delete()
        return

    @create_manage_role.error
    async def create_manage_role_error(self, ctx, error):
        if isinstance(error, MissingPermissions):
            await ctx.author.send(f'***Error: You are missing manage_roles permission(s) to run this command***')
            await ctx.message.delete()

def setup(bot):
    db = DaoFactory()
    bot.add_cog(RoleManage(bot, db))
