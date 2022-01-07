import discord
import asyncio
from discord.ext import commands
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

    async def __create_view_embed__(self):
        i = 0
        embed = discord.Embed(title=f'**Event Role: **', description=f"**Notification roles for event **", \
								color=self.__private_colors[randrange(self.__private_colors_nb)])

        for i in range(len(self.role_list)):
            embed.add_field(name=f'{self.emoji_list[i]} : {self.role_list[i].name}', value='\u200b', inline=False)
        embed.set_footer(text="Choose your role to get the notifications that concern you")
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


    @commands.command(name="remove-manager")
    @commands.has_permissions(administrator=True)
    async def remove_manage_role(self, ctx):
        self.role_list = list()
        guild = ctx.guild
        guildID = ctx.guild.id

        channel_id = self.db.get_id_channel(guildID)
        id_mess = self.db.get_id_mess(guildID)
        chanel = self.bot.get_channel(int(channel_id[0]))
        msg = await chanel.fetch_message(id_mess[0])

        lst_roles_db = self.db.get_role_table(guildID)
        for e in lst_roles_db:
            self.role_list.append(get(guild.roles, id=e[1]))

        [await r.delete() for r in self.role_list]

        self.db.remove_all_elem(guildID)

        await msg.delete()
        await ctx.author.send("** Request successfully deleted **")
        await ctx.message.delete()

    @commands.command(name="add-manager")
    @commands.has_permissions(administrator=True)
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
            await ctx.author.send('**Error: You can only have one role manager**\n' \
                                    '**Please use command `>remove-manager` for remove role manager**')
            return False

        def check(m):
            return m.author == ctx.author and isinstance(m.channel, discord.channel.DMChannel)

        await ctx.author.send(f'** You have 60 second to answer each Questions! **\n'
                                '** Check if you have start command on channel where you print Embed **\n'
                                f"** send 'exit' if you have finish **\n"
                                '** Enter name of Role: (e.g  `God`) **')

        while 1 and not finish:
            try:
                r = await self.bot.wait_for('message',check=check, timeout=60.0)
                r = r.content.capitalize()
                if r == 'Exit':
                    finish = True
                    continue
                r = await ctx.guild.create_role(name=r, mentionable=True, colour=0xf1c40f)
                await ctx.author.send(f"** Role `{r.name}` created **\n")
                self.role_list.append(r)
            except asyncio.TimeoutError:
                await ctx.author.send('Took too long to answer!')
                await ctx.message.delete()
                return False
            except discord.Forbidden as message:
                await ctx.author.send(message)
                await ctx.message.delete()
                return False

        await ctx.author.send(f"** Phase 2: Choose emojii **\n" \
                                    f"** Send 'exit' for stop **\n")

        for r in self.role_list:
            await ctx.author.send(f'** Send Emoji used for choose role {r.name}: (e.g  `❌`) **')
            try:
                r = await self.bot.wait_for('message',check=check, timeout=60.0)
                if r == 'Exit':
                    await ctx.message.delete()
                    await ctx.author.send(f'** You send exit, Bye **')
                    return
                self.emoji_list.append(r.content)

            except asyncio.TimeoutError:
                await ctx.author.send('Took too long to answer!')
                await ctx.message.delete()
        [self.db.set_role_table(guildID, r.id, r.name) for r in self.role_list]
        [self.db.set_emoji_table(guildID, e) for e in self.emoji_list]
        embed = await self.__create_view_embed__()
        mess = await ctx.message.channel.send(embed=embed)
        for emoji in self.emoji_list:
            await mess.add_reaction(emoji)
        self.db.set_guild_table(guildID, ownerID, mess.id, channelID)
        await ctx.author.send(f'** Creating embed for choose role on channel {ctx.message.channel.name} **')
        await ctx.message.delete()


def setup(bot):
    db = DaoFactory()
    bot.add_cog(RoleManage(bot, db))
