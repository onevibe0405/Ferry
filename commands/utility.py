"""
Utility Commands for Discord Bot
Contains userinfo, serverinfo, avatar, ping, uptime, and other utility commands
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from utils import get_emoji, create_embed
from discord.ui import View, Button, button

@commands.hybrid_command(name="userinfo", description="Show detailed information about a user")
@app_commands.describe(member="The user you want information about")
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author

    # Fetch full profile to get banner
    user = await ctx.bot.fetch_user(member.id)

    roles = [role.mention for role in member.roles[1:]]  # Exclude @everyone
    roles_display = ", ".join(roles) if roles else "No roles"

    # Key permissions only
    important_perms = [
        "administrator", "manage_guild", "manage_roles", "manage_channels",
        "ban_members", "kick_members", "manage_messages", "mention_everyone",
        "mute_members", "deafen_members", "move_members", "manage_webhooks",
        "manage_emojis", "view_audit_log", "manage_threads"
    ]
    perms_list = [
        perm.replace("_", " ").title()
        for perm, value in member.guild_permissions
        if value and perm in important_perms
    ]
    perms_display = ", ".join(perms_list) if perms_list else "No key permissions"

    created = f"{member.created_at:%d %b %Y} (<t:{int(member.created_at.timestamp())}:R>)"
    joined = f"{member.joined_at:%d %b %Y} (<t:{int(member.joined_at.timestamp())}:R>)"

    embed = create_embed(
        title=f"User Information — {member}",
        description=None
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(
        name="**General Info**",
        value=(
            f"**ID:** {member.id}\n"
            f"**Display Name:** {member.display_name}\n"
            f"**Created On:** {created}\n"
            f"**Joined Server:** {joined}"
        ),
        inline=False
    )
    embed.add_field(
        name="**Roles**",
        value=roles_display,
        inline=False
    )
    embed.add_field(
        name="**Key Permissions**",
        value=perms_display,
        inline=False
    )

    # Show banner if exists
    if user.banner:
        embed.set_image(url=user.banner.url)

    await ctx.send(embed=embed)

@commands.hybrid_command(name="serverinfo", description="Show detailed information about the server")
async def serverinfo(ctx):
    guild = ctx.guild

    total_members = guild.member_count
    humans = len([m for m in guild.members if not m.bot])
    bots = total_members - humans
    banned_count = len([ban async for ban in guild.bans()])
    created = f"{guild.created_at:%d %b %Y} (<t:{int(guild.created_at.timestamp())}:R>)"

    # Channel counts
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)

    # Emoji counts
    regular_emojis = len([e for e in guild.emojis if not e.animated])
    animated_emojis = len([e for e in guild.emojis if e.animated])
    total_emojis = len(guild.emojis)

    # Create embed
    embed = create_embed(
        title=f"{guild.name}",
        description=None
    )

    embed.set_thumbnail(url=guild.icon.url if guild.icon else None)

    embed.add_field(
        name="**About**",
        value=(
            f"**Name:** {guild.name}\n"
            f"**ID:** {guild.id}\n"
            f"**Owner:** {guild.owner.mention if guild.owner else 'Unknown'}\n"
            f"**Server Created:** {created}\n"
            f"**Members:** {total_members} (Humans: {humans} | Bots: {bots})\n"
            f"**Banned:** {banned_count}"
        ),
        inline=False
    )

    embed.add_field(
        name="**Extra**",
        value=(
            f"**Verification Level:** {str(guild.verification_level).title()}\n"
            f"**Upload Limit:** {round(guild.filesize_limit / 1024 / 1024)} MB\n"
            f"**Inactive Timeout:** {guild.afk_timeout // 60} minutes\n"
            f"**System Welcome Messages:** {'Yes' if guild.system_channel else 'No'}\n"
            f"**Default Notifications:** {str(guild.default_notifications).replace('_', ' ').title()}\n"
            f"**Explicit Media Content Filter:** {str(guild.explicit_content_filter).replace('_', ' ').title()}\n"
            f"**2FA Requirements:** {'Yes' if guild.mfa_level else 'No'}"
        ),
        inline=False
    )

    embed.add_field(
        name="**Channels**",
        value=f"**Total:** {text_channels + voice_channels}\n"
              f"**Voice:** {voice_channels} | **Text:** {text_channels}",
        inline=False
    )

    embed.add_field(
        name="**Emoji Info**",
        value=f"**Regular:** {regular_emojis}/50\n"
              f"**Animated:** {animated_emojis}/50\n"
              f"**Total:** {total_emojis}/100",
        inline=False
    )

    # Show banner if exists
    if guild.banner:
        embed.set_image(url=guild.banner.url)

    # Roles Button
    class RolesButton(View):
        def __init__(self, roles):
            super().__init__(timeout=None)
            self.roles = roles

        @discord.ui.button(label="View Roles", style=discord.ButtonStyle.blurple)
        async def view_roles(self, interaction: discord.Interaction, button: Button):
            roles_list = [role.mention for role in self.roles if role.name != "@everyone"]
            roles_text = ", ".join(roles_list) if roles_list else "No roles in this server."
            await interaction.response.send_message(
                f"**Roles in {guild.name}:**\n{roles_text}",
                ephemeral=True
            )

    view = RolesButton(guild.roles)
    await ctx.send(embed=embed, view=view)

@commands.hybrid_command(name="roleinfo", description="Show detailed information about a role")
@app_commands.describe(role="The role you want information about")
async def roleinfo(ctx, role: discord.Role):
    # Key permissions filter
    important_perms = [
        "administrator", "manage_guild", "manage_roles", "manage_channels",
        "manage_messages", "manage_webhooks", "manage_nicknames",
        "kick_members", "ban_members", "mention_everyone", "moderate_members",
        "view_audit_log", "priority_speaker", "mute_members", "deafen_members"
    ]
    perms = [name.replace("_", " ").title() for name, value in role.permissions if value and name in important_perms]
    perms_display = ", ".join(perms) if perms else "No key permissions"

    # Embed
    embed = create_embed(
        title=f"Role Information — {role.name}",
        description=None
    )
    embed.add_field(
        name="**General Info**",
        value=(
            f"**ID:** {role.id}\n"
            f"**Name:** {role.name}\n"
            f"**Color:** {role.color if role.color.value != 0 else 'Default'}\n"
            f"**Position:** {role.position}\n"
            f"**Mentionable:** {'Yes' if role.mentionable else 'No'}\n"
            f"**Created On:** {discord.utils.format_dt(role.created_at, 'D')} ({discord.utils.format_dt(role.created_at, 'R')})"
        ),
        inline=False
    )
    embed.add_field(
        name="**Statistics**",
        value=(
            f"**Members with this role:** {len(role.members)}\n"
            f"**Hoisted:** {'Yes' if role.hoist else 'No'}\n"
            f"**Managed by Integration:** {'Yes' if role.managed else 'No'}"
        ),
        inline=False
    )
    embed.add_field(
        name="**Key Permissions**",
        value=perms_display,
        inline=False
    )

    # View Members Button
    class ViewMembers(discord.ui.View):
        def __init__(self, members):
            super().__init__(timeout=None)
            self.members = members

        @discord.ui.button(label="View Members", style=discord.ButtonStyle.blurple)
        async def view_members_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            members_list = "\n".join([member.mention for member in self.members]) or "No members have this role."
            await interaction.response.send_message(
                f"**Members with {role.name}:**\n{members_list}",
                ephemeral=True
            )

    await ctx.send(embed=embed, view=ViewMembers(role.members))

@commands.hybrid_command(name='avatar', description='Get user avatar')
@app_commands.describe(user='User to get avatar from')
async def avatar(ctx, user: discord.Member = None):
    if not user:
        user = ctx.author
    
    embed = create_embed(f"🖼️ Avatar", f"**{user.display_name}'s** avatar")
    embed.set_image(url=user.display_avatar.url)
    embed.add_field(name="Download", value=f"[Click here]({user.display_avatar.url})", inline=False)
    await ctx.send(embed=embed)

@commands.hybrid_command(name='ping', description='Check bot latency')
async def ping(ctx):
    latency = round(ctx.bot.latency * 1000)
    embed = create_embed("🏓 Pong!", f"Bot latency: **{latency}ms**")
    await ctx.send(embed=embed)

@commands.hybrid_command(name='uptime', description='Check bot uptime')
async def uptime(ctx):
    uptime_duration = datetime.now() - ctx.bot.start_time
    hours, remainder = divmod(int(uptime_duration.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    
    embed = create_embed("⏰ Bot Uptime", f"**{days}d {hours}h {minutes}m {seconds}s**")
    await ctx.send(embed=embed)

@commands.hybrid_command(name="mc", description="Show detailed member count of the server")
async def mc(ctx):
    guild = ctx.guild
    total_members = guild.member_count
    bots = sum(1 for member in guild.members if member.bot)
    humans = total_members - bots
    online = sum(1 for member in guild.members if member.status != discord.Status.offline)
    
    embed = create_embed(
        "📊 Member Count",
        f"**Total Members:** {total_members}\n"
        f"**Humans:** {humans}\n"
        f"**Bots:** {bots}\n"
        f"**Online:** {online}"
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name='snipe', description='Show last deleted message')
async def snipe(ctx):
    if not ctx.bot.deleted_messages:
        embed = create_embed(f"{get_emoji('cross')} No Messages", "No recently deleted messages found!")
        return await ctx.send(embed=embed)
    
    # Get the most recent deleted message
    deleted_msg = ctx.bot.deleted_messages[-1]
    
    embed = create_embed(
        "🎯 Message Sniped",
        f"**Author:** {deleted_msg['author']}\n"
        f"**Content:** {deleted_msg['content'][:1000]}{'...' if len(deleted_msg['content']) > 1000 else ''}\n"
        f"**Deleted:** <t:{int(deleted_msg['timestamp'].timestamp())}:R>"
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name='afk', description='Set AFK status')
@app_commands.describe(reason='Reason for being AFK')
async def afk(ctx, *, reason: str = "AFK"):
    ctx.bot.afk_users[ctx.author.id] = {
        'reason': reason,
        'timestamp': datetime.now()
    }
    
    embed = create_embed(
        f"{get_emoji('sleepy')} AFK Set",
        f"**{ctx.author.display_name}** is now AFK: *{reason}*"
    )
    await ctx.send(embed=embed, delete_after=10)

@commands.hybrid_command(name="invite", description="Get bot invite link")
async def invite(ctx):
    embed = create_embed(
        "📩 Bot Invite",
        f"**[Invite me to your server!](https://discord.com/api/oauth2/authorize?client_id={ctx.bot.user.id}&permissions=8&scope=bot%20applications.commands)**\n\n"
        f"**Features:**\n"
        f"🔨 Advanced Moderation\n"
        f"🎵 Music System\n"
        f"🎯 Custom Commands\n"
        f"📊 Server Management\n"
        f"🌐 Web Dashboard"
    )
    await ctx.send(embed=embed)

async def setup(bot):
    """Add utility commands to bot"""
    bot.add_command(userinfo)
    bot.add_command(serverinfo)
    bot.add_command(roleinfo)
    bot.add_command(avatar)
    bot.add_command(ping)
    bot.add_command(uptime)
    bot.add_command(mc)
    bot.add_command(snipe)
    bot.add_command(afk)
    bot.add_command(invite)
