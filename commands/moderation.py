"""
Moderation Commands for Discord Bot
Contains ban, kick, mute, timeout, warn, and other moderation utilities
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta
from utils import has_permissions, get_emoji, create_embed, parse_time

class ModerationConfirmView(discord.ui.View):
    def __init__(self, action_type, target_user, moderator, reason, timeout=30):
        super().__init__(timeout=timeout)
        self.action_type = action_type
        self.target_user = target_user
        self.moderator = moderator
        self.reason = reason
        self.message = None

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.moderator:
            await interaction.response.send_message("❌ Only the moderator can confirm this action!", ephemeral=True)
            return

        try:
            if self.action_type == "ban":
                await self.target_user.ban(reason=f"{self.reason} - By {self.moderator}")
                embed = create_embed(f"{get_emoji('tick')} User Banned", f"**{self.target_user}** has been banned\n**Reason:** {self.reason}")
            elif self.action_type == "kick":
                await self.target_user.kick(reason=f"{self.reason} - By {self.moderator}")
                embed = create_embed(f"{get_emoji('tick')} User Kicked", f"**{self.target_user}** has been kicked\n**Reason:** {self.reason}")
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self)
            
        except discord.Forbidden:
            embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to perform this action!")
            await interaction.response.edit_message(embed=embed, view=self)
        except Exception as e:
            embed = create_embed(f"{get_emoji('cross')} Error", f"An error occurred: {str(e)}")
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.moderator:
            await interaction.response.send_message("❌ Only the moderator can cancel this action!", ephemeral=True)
            return

        embed = create_embed(
            f"{get_emoji('cross')} Action Cancelled",
            f"The {self.action_type} action has been cancelled."
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        embed = create_embed(
            f"{get_emoji('cross')} Action Timed Out",
            f"The {self.action_type} confirmation has timed out."
        )
        
        # Disable all buttons
        for item in self.children:
            item.disabled = True
        
        # Try to edit the message
        try:
            await self.message.edit(embed=embed, view=self)
        except:
            pass

# Moderation Commands
@commands.hybrid_command(name='ban', description='Ban a user from the server')
@app_commands.describe(user='User to ban', reason='Reason for ban')
async def ban(ctx, user: discord.Member, *, reason: str = "No reason provided"):
    if not await has_permissions(ctx, ban_members=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Ban Members** permission!")
        return await ctx.send(embed=embed)
    
    # Create confirmation embed
    embed = create_embed(
        "⚠️ Confirm Ban Action",
        f"Are you sure you want to **ban** {user.mention}?\n\n"
        f"**User:** {user} (ID: {user.id})\n"
        f"**Reason:** {reason}\n\n"
        f"⏰ You have 30 seconds to confirm this action."
    )
    
    # Create confirmation view
    view = ModerationConfirmView("ban", user, ctx.author, reason)
    message = await ctx.send(embed=embed, view=view)
    view.message = message

@commands.hybrid_command(name='kick', description='Kick a user from the server')
@app_commands.describe(user='User to kick', reason='Reason for kick')
async def kick(ctx, user: discord.Member, *, reason: str = "No reason provided"):
    if not await has_permissions(ctx, kick_members=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Kick Members** permission!")
        return await ctx.send(embed=embed)
    
    # Create confirmation embed
    embed = create_embed(
        "⚠️ Confirm Kick Action",
        f"Are you sure you want to **kick** {user.mention}?\n\n"
        f"**User:** {user} (ID: {user.id})\n"
        f"**Reason:** {reason}\n\n"
        f"⏰ You have 30 seconds to confirm this action."
    )
    
    # Create confirmation view
    view = ModerationConfirmView("kick", user, ctx.author, reason)
    message = await ctx.send(embed=embed, view=view)
    view.message = message

@commands.hybrid_command(name='mute', description='Timeout a user')
@app_commands.describe(user='User to mute', duration='Duration (e.g., 10m, 1h)', reason='Reason for mute')
async def mute(ctx, user: discord.Member, duration: str = "10m", *, reason: str = "No reason provided"):
    if not await has_permissions(ctx, moderate_members=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Timeout Members** permission!")
        return await ctx.send(embed=embed)
    
    duration_seconds = parse_time(duration)
    if not duration_seconds:
        embed = create_embed(f"{get_emoji('cross')} Invalid Duration", "Use format like: 10m, 1h, 2d")
        return await ctx.send(embed=embed)
    
    try:
        until = discord.utils.utcnow() + timedelta(seconds=duration_seconds)
        await user.timeout(until, reason=f"{reason} - By {ctx.author}")
        
        embed = create_embed(
            f"{get_emoji('tick')} User Muted",
            f"**{user}** has been muted for **{duration}**\n**Reason:** {reason}"
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to timeout this user!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='unmute', description='Remove timeout from a user')
@app_commands.describe(user='User to unmute')
async def unmute(ctx, user: discord.Member):
    if not await has_permissions(ctx, moderate_members=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Timeout Members** permission!")
        return await ctx.send(embed=embed)
    
    try:
        await user.timeout(None, reason=f"Unmuted by {ctx.author}")
        embed = create_embed(f"{get_emoji('tick')} User Unmuted", f"**{user}** has been unmuted")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to remove timeout from this user!")  
        await ctx.send(embed=embed)

@commands.hybrid_command(name='unban', description='Unban a user from the server')
@app_commands.describe(user_id='User ID to unban', reason='Reason for unban')
async def unban(ctx, user_id: str, *, reason: str = "No reason provided"):
    if not await has_permissions(ctx, ban_members=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Ban Members** permission!")
        return await ctx.send(embed=embed)
    
    try:
        user_id = int(user_id)
        user = await ctx.bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=f"{reason} - By {ctx.author}")
        
        embed = create_embed(
            f"{get_emoji('tick')} User Unbanned",
            f"**{user}** has been unbanned\n**Reason:** {reason}"
        )
        await ctx.send(embed=embed)
    except ValueError:
        embed = create_embed(f"{get_emoji('cross')} Invalid ID", "Please provide a valid user ID!")
        await ctx.send(embed=embed)
    except discord.NotFound:
        embed = create_embed(f"{get_emoji('cross')} User Not Found", "User is not banned or doesn't exist!")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to unban users!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='warn', description='Warn a user')
@app_commands.describe(user='User to warn', reason='Reason for warning')
async def warn(ctx, user: discord.Member, *, reason: str = "No reason provided"):
    if not await has_permissions(ctx, kick_members=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Kick Members** permission!")
        return await ctx.send(embed=embed)
    
    guild_id = str(ctx.guild.id)
    user_id = str(user.id)
    
    # Initialize warning system
    if guild_id not in ctx.bot.user_warnings:
        ctx.bot.user_warnings[guild_id] = {}
    if user_id not in ctx.bot.user_warnings[guild_id]:
        ctx.bot.user_warnings[guild_id][user_id] = []
    
    # Add warning
    warning = {
        'reason': reason,
        'moderator': str(ctx.author),
        'timestamp': discord.utils.utcnow().isoformat()
    }
    ctx.bot.user_warnings[guild_id][user_id].append(warning)
    
    warning_count = len(ctx.bot.user_warnings[guild_id][user_id])
    
    embed = create_embed(
        f"{get_emoji('warning')} User Warned",
        f"**{user}** has been warned\n**Reason:** {reason}\n**Total Warnings:** {warning_count}"
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name='warnings', description='Check user warnings')
@app_commands.describe(user='User to check warnings for')
async def warnings(ctx, user: discord.Member = None):
    if not user:
        user = ctx.author
    
    guild_id = str(ctx.guild.id)
    user_id = str(user.id)
    
    if guild_id not in ctx.bot.user_warnings or user_id not in ctx.bot.user_warnings[guild_id]:
        embed = create_embed(f"{get_emoji('tick')} No Warnings", f"**{user}** has no warnings!")
        return await ctx.send(embed=embed)
    
    warnings = ctx.bot.user_warnings[guild_id][user_id]
    warning_list = []
    
    for i, warning in enumerate(warnings[-10:], 1):  # Show last 10 warnings
        warning_list.append(f"**{i}.** {warning['reason']} - *by {warning['moderator']}*")
    
    embed = create_embed(
        f"{get_emoji('warning')} User Warnings",
        f"**{user}** has **{len(warnings)}** warning(s)\n\n" + "\n".join(warning_list)
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name='clearwarns', description='Clear all warnings for a user')
@app_commands.describe(user='User to clear warnings for')
async def clearwarns(ctx, user: discord.Member):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)
    
    guild_id = str(ctx.guild.id)
    user_id = str(user.id)
    
    if guild_id in ctx.bot.user_warnings and user_id in ctx.bot.user_warnings[guild_id]:
        del ctx.bot.user_warnings[guild_id][user_id]
        embed = create_embed(f"{get_emoji('tick')} Warnings Cleared", f"All warnings for **{user}** have been cleared")
    else:
        embed = create_embed(f"{get_emoji('info')} No Warnings", f"**{user}** has no warnings to clear")
    
    await ctx.send(embed=embed)

async def setup(bot):
    """Add moderation commands to bot"""
    bot.add_command(ban)
    bot.add_command(kick)
    bot.add_command(mute)
    bot.add_command(unmute)
    bot.add_command(unban)
    bot.add_command(warn)
    bot.add_command(warnings)
    bot.add_command(clearwarns)