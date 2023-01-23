import os
import datetime
from datetime import datetime
from datetime import date
from datetime import datetime
from discord.ext import commands, tasks
import discord
from discord.commands import Option
from discord.ext.commands import cooldown, BucketType
from discord.ui import Button, View
from datetime import timedelta
import random
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TOKEN')

userCache = []

intents = discord.Intents.all()
bing = commands.Bot(command_prefix='bt!', intents=intents)

PINK_COLOR = 0xC98FFC

class reportModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Aspect"))
        self.add_item(discord.ui.InputText(label="Notes", style=discord.InputTextStyle.long))

    def variables(self, logs, author):
        self.logs = logs
        self.reporter = author

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(title="⚠ Report", description=f"{self.reporter} ● {self.reporter.id}", color=0xFFA6A6)
        embed.add_field(name="Aspect", value=self.children[0].value, inline=False)
        embed.add_field(name="Report Notes", value=self.children[1].value, inline=False)
        embed.timestamp = datetime.now()
        embed.set_thumbnail(url=self.reporter.display_avatar)

        sendEmbed = discord.Embed(title="Thank you for your report", description="You will be contacted shortly", color=PINK_COLOR)
        sendEmbed.timestamp = datetime.now()
        await self.logs.send(embed=embed)

        await interaction.response.send_message(embeds=[sendEmbed])

class verifyModal(discord.ui.Modal):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.add_item(discord.ui.InputText(label="Verification Code"))

    def variables(self, author, channel, cache):
        self.author = author
        self.channel = channel
        self.cache = cache

    async def callback(self, interaction: discord.Interaction):

        if self.cache['code'] == self.children[0].value.upper():
            verified_role = self.author.guild.get_role(1067149416248647742)

            overwrite = discord.PermissionOverwrite()
            overwrite.manage_roles = True

            await self.channel.set_permissions(self.author, overwrite=overwrite)
            await self.author.add_roles(verified_role)

            overwrite.manage_roles = False
            await self.channel.set_permissions(self.author, overwrite=overwrite)

            embed = discord.Embed(title="✅ Successful Verification", color=0x11E104)
            embed.add_field(name="User", value=f"{self.author} ● {self.author.id}", inline=False)
            embed.add_field(name="Code", value=self.children[0].value, inline=False)
            embed.add_field(name="Channel", value=self.channel.mention, inline=False)
            embed.timestamp = datetime.now()
            embed.set_thumbnail(url=self.author.display_avatar)

            await bing.get_channel(1067096413353279529).send(embed=embed)
        
        else:
            embed = discord.Embed(title="❌ Invalid Code", color=0xFFA6A6)
            embed.add_field(name="User", value=f"{self.author} ● {self.author.id}", inline=False)
            embed.add_field(name="Code", value=self.children[0].value, inline=False)
            embed.timestamp = datetime.now()
            embed.set_thumbnail(url=self.author.display_avatar)

            await bing.get_channel(1067096413353279529).send(embed=embed)

        await interaction.response.send_message(embeds=[embed])

@bing.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.CommandOnCooldown):
		await ctx.send(f"On cooldown, {round(error.retry_after, 2)} seconds left")

@bing.event
async def on_ready():
  await bing.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="/report | bing#6313"), status=discord.Status.dnd)

@bing.event
async def on_member_join(member):
    if member.guild.id == 1066518165858832405:
        log = bing.get_channel(1067096413353279529)
        embed = discord.Embed(description=f"{member.mention} {member}", color=0xAFE1AF)
        embed.set_author(icon_url=member.display_avatar, name="Member Joined")
        user = bing.get_user(member.id)
        embed.add_field(name="Account Creation", value=f"<t:{int(user.created_at.timestamp())}:D>")
        embed.set_thumbnail(url=member.display_avatar)
        embed.timestamp = datetime.now()
        embed.set_footer(text=f"ID: {member.id}")
        await log.send(embed=embed)

        welcome_channel = bing.get_channel(1066900094747672710)
        user = bing.get_user(member.id)
        embed = discord.Embed(title="Welcome", description=f"Welcome to **{member.guild}**, {member.mention}!\n\nUsername - {member}\nCreation Date - <t:{int(user.created_at.timestamp())}:D>\nMember #{msg.guild.member_count:,}", color=PINK_COLOR)
        embed.timestamp = datetime.now()
        embed.set_thumbnail(url=member.display_avatar)
        await welcome_channel.send(embed=embed)

        CHANNEL = False
        for i,v in enumerate(member.guild.channels):
            if v.name == f"{member}-verification":
                CHANNEL = True
                sendChannel = v
                break

        overwrite = discord.PermissionOverwrite()
        overwrite.send_messages = True
        overwrite.read_messages = True

        if CHANNEL:
            await sendChannel.set_permissions(member, overwrite=overwrite)
            await sendChannel.send(f"Hello {member.mention}, please run `/verify` and your verification code is: `{userCache['code']}`")
        else:
            verifyCategory = discord.utils.get(member.guild.categories, name='Verification')
            channel = await member.guild.create_text_channel(f"{member}-verification", category=verifyCategory)
            await channel.set_permissions(member, overwrite=overwrite)
            chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"
            code = ""
            for i in range(0,5):
                code += chars[random.randint(0,35)]
            userCache.append({"user": member.id, "code": code})

            await channel.send(f"Hello {member.mention}, please run `/verify` and your verification code is: `{code}`")


@bing.slash_command(name="report", description="Report an issue with BingTools")
async def report(ctx):
    modal = reportModal(title="BingTools Bug Report")
    logs = bing.get_channel(1067096413353279529)
    modal.variables(logs, ctx.author)
    await ctx.send_modal(modal)

@bing.slash_command(name="verify", description="Verification in the Discord")
async def verify(ctx):
    cache = None
    for i, data in enumerate(userCache):
        if data['user'] == ctx.author.id:
            cache = data
    if cache:      
        modal = verifyModal(title="BingTools Verification")
        modal.variables(ctx.author, ctx.channel, cache)
        await ctx.send_modal(modal)
    else:
        await ctx.reply("Invalid user please contact an Admin")

bing.run(token)