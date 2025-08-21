"""
Administration Commands for Discord Bot
Contains server management, channel operations, prefix settings, and bot administration
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import zipfile
import io
from utils import has_permissions, get_emoji, create_embed, save_data

@commands.hybrid_command(name='purge', description='Delete multiple messages')
@app_commands.describe(amount='Number of messages to delete (1-100)')
async def purge(ctx, amount: int):
    if not await has_permissions(ctx, manage_messages=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Messages** permission!")
        return await ctx.send(embed=embed)

    if amount < 1 or amount > 100:
        embed = create_embed(f"{get_emoji('cross')} Invalid Amount", "Amount must be between 1 and 100!")
        return await ctx.send(embed=embed)

    deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include command message

    embed = create_embed(f"{get_emoji('tick')} Messages Purged", f"Deleted **{len(deleted)-1}** messages")
    message = await ctx.send(embed=embed)
    await asyncio.sleep(3)
    await message.delete()

@commands.hybrid_command(name='cbot', description='Delete bot messages from the channel')
@app_commands.describe(amount='Number of messages to check (default: 50)')
async def cbot(ctx, amount: int = 50):
    if not await has_permissions(ctx, manage_messages=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Messages** permission!")
        return await ctx.send(embed=embed)

    deleted = 0
    async for message in ctx.channel.history(limit=amount):
        if message.author.bot:
            try:
                await message.delete()
                deleted += 1
            except:
                continue

    embed = create_embed(f"{get_emoji('tick')} Bot Messages Cleared", f"Deleted **{deleted}** bot messages")
    message = await ctx.send(embed=embed)
    await asyncio.sleep(3)
    await message.delete()

@commands.hybrid_command(name='lock', description='Lock a channel')
@app_commands.describe(channel='Channel to lock (optional)')
async def lock(ctx, channel: discord.TextChannel = None):
    if not await has_permissions(ctx, manage_channels=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Channels** permission!")
        return await ctx.send(embed=embed)

    channel = channel or ctx.channel

    try:
        await channel.set_permissions(ctx.guild.default_role, send_messages=False)
        embed = create_embed(f"{get_emoji('lock')} Channel Locked", f"**{channel.name}** has been locked")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to manage this channel!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='unlock', description='Unlock a channel')
@app_commands.describe(channel='Channel to unlock (optional)')
async def unlock(ctx, channel: discord.TextChannel = None):
    if not await has_permissions(ctx, manage_channels=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Channels** permission!")
        return await ctx.send(embed=embed)

    channel = channel or ctx.channel

    try:
        await channel.set_permissions(ctx.guild.default_role, send_messages=None)
        embed = create_embed(f"{get_emoji('unlock')} Channel Unlocked", f"**{channel.name}** has been unlocked")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to manage this channel!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='slowmode', description='Set channel slowmode')
@app_commands.describe(seconds='Slowmode duration in seconds (0-21600)', channel='Channel to set slowmode for')
async def slowmode(ctx, seconds: int, channel: discord.TextChannel = None):
    if not await has_permissions(ctx, manage_channels=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Channels** permission!")
        return await ctx.send(embed=embed)

    if seconds < 0 or seconds > 21600:
        embed = create_embed(f"{get_emoji('cross')} Invalid Duration", "Slowmode must be between 0 and 21600 seconds (6 hours)!")
        return await ctx.send(embed=embed)

    channel = channel or ctx.channel

    try:
        await channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            embed = create_embed(f"{get_emoji('tick')} Slowmode Disabled", f"Slowmode disabled in **{channel.name}**")
        else:
            embed = create_embed(f"{get_emoji('tick')} Slowmode Set", f"Slowmode set to **{seconds}** seconds in **{channel.name}**")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to manage this channel!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='nuke', description='Delete and recreate channel')
async def nuke(ctx):
    if not await has_permissions(ctx, manage_channels=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Channels** permission!")
        return await ctx.send(embed=embed)

    channel = ctx.channel
    position = channel.position

    try:
        new_channel = await channel.clone()
        await new_channel.edit(position=position)
        await channel.delete()

        embed = create_embed("💥 Channel Nuked", "Channel has been successfully nuked!")
        await new_channel.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to manage channels!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='vcpull', description='Pull a user to your voice channel')
@app_commands.describe(user='User to pull to your voice channel')
async def vcpull(ctx, user: discord.Member):
    if not await has_permissions(ctx, move_members=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Move Members** permission!")
        return await ctx.send(embed=embed)

    if not ctx.author.voice:
        embed = create_embed(f"{get_emoji('cross')} Not in Voice", "You need to be in a voice channel!")
        return await ctx.send(embed=embed)

    if not user.voice:
        embed = create_embed(f"{get_emoji('cross')} User Not in Voice", f"{user.mention} is not in a voice channel!")
        return await ctx.send(embed=embed)

    try:
        await user.move_to(ctx.author.voice.channel)
        embed = create_embed(f"{get_emoji('tick')} User Moved", f"Moved {user.mention} to **{ctx.author.voice.channel.name}**")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to move members!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='setprefix', description='Change server prefix')
@app_commands.describe(prefix='New prefix for the server')
async def setprefix(ctx, prefix: str):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    if len(prefix) > 5:
        embed = create_embed(f"{get_emoji('cross')} Prefix Too Long", "Prefix must be 5 characters or less!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    # Update global guild_prefixes
    global guild_prefixes
    guild_prefixes[guild_id] = prefix

    # Update bot data
    ctx.bot.data['guild_prefixes'] = guild_prefixes
    save_data(ctx.bot.data)

    embed = create_embed(f"{get_emoji('tick')} Prefix Changed", f"Server prefix changed to: **{prefix}**")
    await ctx.send(embed=embed)

@commands.hybrid_command(name='noprefix', description='Toggle no-prefix access for a user')
@app_commands.describe(user='User to toggle no-prefix access for')
async def noprefix(ctx, user: discord.Member):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    user_id = user.id

    if user_id in ctx.bot.no_prefix_users:
        ctx.bot.no_prefix_users.remove(user_id)
        embed = create_embed(f"{get_emoji('tick')} No-Prefix Disabled", f"**{user}** can no longer use commands without prefix")
    else:
        ctx.bot.no_prefix_users.add(user_id)
        embed = create_embed(f"{get_emoji('tick')} No-Prefix Enabled", f"**{user}** can now use commands without prefix")

    # Save data
    ctx.bot.data['no_prefix_users'] = list(ctx.bot.no_prefix_users)
    save_data(ctx.bot.data)
    await ctx.send(embed=embed)

@commands.hybrid_command(name='npusers', description='Show users with no-prefix permissions')
async def npusers(ctx):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    if not ctx.bot.no_prefix_users:
        embed = create_embed(f"{get_emoji('info')} No No-Prefix Users", "No users have no-prefix permissions!")
        return await ctx.send(embed=embed)

    embed = create_embed("👑 No-Prefix Users", f"Users with no-prefix permissions: **{len(ctx.bot.no_prefix_users)}**")

    user_list = []
    for user_id in ctx.bot.no_prefix_users:
        try:
            user = await ctx.bot.fetch_user(user_id)
            user_list.append(f"• **{user}** (ID: {user_id})")
        except discord.NotFound:
            user_list.append(f"• **Unknown User** (ID: {user_id})")
        except Exception:
            user_list.append(f"• **Error fetching user** (ID: {user_id})")

    if user_list:
        # Split into chunks if too many users
        chunks = [user_list[i:i+10] for i in range(0, len(user_list), 10)]
        for chunk in chunks:
            embed.description += "\n\n" + "\n".join(chunk)

    await ctx.send(embed=embed)

@commands.hybrid_command(name='massban', description='Ban multiple users')
@app_commands.describe(user_ids='User IDs to ban separated by spaces', reason='Reason for ban')
async def massban(ctx, user_ids: str, *, reason: str = "Mass ban"):
    if not await has_permissions(ctx, ban_members=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Ban Members** permission!")
        return await ctx.send(embed=embed)

    ids = user_ids.split()
    success_count = 0
    failed_count = 0

    for user_id in ids:
        try:
            user_id = int(user_id)
            user = await ctx.bot.fetch_user(user_id)
            await ctx.guild.ban(user, reason=f"{reason} - By {ctx.author}")
            success_count += 1
        except ValueError:
            print(f"Invalid user ID: {user_id}")
            failed_count += 1
            continue
        except discord.NotFound:
            print(f"User not found: {user_id}")
            failed_count += 1
            continue
        except discord.Forbidden:
            print(f"No permission to ban user: {user_id}")
            failed_count += 1
            continue
        except Exception as e:
            print(f"Error banning user {user_id}: {e}")
            failed_count += 1
            continue

    embed = create_embed(
        f"{get_emoji('tick')} Mass Ban Complete",
        f"**Banned:** {success_count}\n**Failed:** {failed_count}\n**Reason:** {reason}"
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name='leaveguild', description='Make the bot leave a server by guild ID (owner only)')
@commands.is_owner()
@app_commands.describe(guild_id='Guild ID to leave')
async def leaveguild(ctx, guild_id: str):
    try:
        guild_id = int(guild_id)
        guild = ctx.bot.get_guild(guild_id)

        if not guild:
            embed = create_embed(f"{get_emoji('cross')} Guild Not Found", f"I'm not in a guild with ID: {guild_id}")
            return await ctx.send(embed=embed)

        guild_name = guild.name
        await guild.leave()

        embed = create_embed(f"{get_emoji('tick')} Left Guild", f"Successfully left **{guild_name}** (ID: {guild_id})")
        await ctx.send(embed=embed)

    except ValueError:
        embed = create_embed(f"{get_emoji('cross')} Invalid ID", "Please provide a valid guild ID!")
        await ctx.send(embed=embed)
    except Exception as e:
        embed = create_embed(f"{get_emoji('cross')} Error", f"Failed to leave guild: {str(e)}")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='say', description='Make the bot say something (Owner only)')
@commands.is_owner()
@app_commands.describe(message='Message to say')
async def say(ctx, *, message: str):
    try:
        await ctx.message.delete()  # Delete command message
    except:
        pass

    # If the command is used in reply to a message
    if ctx.message.reference:
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        await replied_message.reply(message)
    else:
        await ctx.send(message)

@commands.hybrid_command(name='dm', description='Send a direct message to a user')
@app_commands.describe(user='User to send DM to', message='Message to send')
async def dm_user(ctx, user: discord.Member, *, message: str):
    if not await has_permissions(ctx, manage_messages=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Messages** permission!")
        return await ctx.send(embed=embed)

    try:
        # Send DM to the user
        await user.send(message)

        # Send confirmation (ephemeral for slash commands)
        embed = create_embed(f"{get_emoji('tick')} DM Sent", f"Successfully sent DM to **{user}**")

        if ctx.interaction:
            await ctx.send(embed=embed, ephemeral=True)
        else:
            # For prefix commands, send confirmation and delete after 3 seconds
            confirmation_msg = await ctx.send(embed=embed)
            # Delete both command message and confirmation message
            try:
                await asyncio.sleep(3)
                await confirmation_msg.delete()
                await ctx.message.delete()
            except (discord.NotFound, discord.Forbidden):
                pass

    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} DM Failed", f"Could not send DM to **{user}** - they may have DMs disabled")

        if ctx.interaction:
            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)
    except Exception as e:
        embed = create_embed(f"{get_emoji('cross')} Error", f"Failed to send DM: {str(e)}")

        if ctx.interaction:
            await ctx.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)

@commands.hybrid_command(name="listallcmds", description="List all registered commands")
async def listallcmds(ctx):
    command_names = [cmd.name for cmd in ctx.bot.commands]
    embed = create_embed(
        "📜 All Bot Commands",
        "\n".join(f"• {name}" for name in sorted(command_names))
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name='vchide', description='Hide a voice channel from everyone')
@app_commands.describe(channel='Voice channel to hide (leave empty to use your current one)')
async def vchide(ctx, channel: discord.VoiceChannel = None):
    if not await has_permissions(ctx, manage_channels=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Channels** permission!")
        return await ctx.send(embed=embed)

    # If no channel is provided, use the one the author is in
    if channel is None:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
        else:
            embed = create_embed(f"{get_emoji('cross')} No Channel", "You are not in a voice channel and didn't specify one!")
            return await ctx.send(embed=embed)

    try:
        # Deny view/connect for @everyone
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = False
        overwrite.connect = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        embed = create_embed(f"{get_emoji('lock')} Voice Channel Hidden", f"**{channel.name}** is now hidden from everyone")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to manage this voice channel!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='vcunhide', description='Unhide a voice channel for everyone')
@app_commands.describe(channel='Voice channel to unhide (leave empty to use your current one)')
async def vcunhide(ctx, channel: discord.VoiceChannel = None):
    if not await has_permissions(ctx, manage_channels=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Channels** permission!")
        return await ctx.send(embed=embed)

    # If no channel is provided, use the one the author is in
    if channel is None:
        if ctx.author.voice:
            channel = ctx.author.voice.channel
        else:
            embed = create_embed(f"{get_emoji('cross')} No Channel", "You are not in a voice channel and didn't specify one!")
            return await ctx.send(embed=embed)

    try:
        # Allow view/connect for @everyone
        overwrite = channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = True
        overwrite.connect = True
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)

        embed = create_embed(f"{get_emoji('unlock')} Voice Channel Unhidden", f"**{channel.name}** is now visible to everyone")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to manage this voice channel!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name="backup", description="📦 Backup bot's core files (Owner only)")
@commands.is_owner()
async def backup(ctx):
    await ctx.defer()  # Defers response for slash command

    important_files = [
        "main.py",
        "utils.py",
        "embedbuilder.py", 
        "data.json",
        "data_backup.json",
        "requirements.txt",
        "pyproject.toml",
        "start_bot.py",
        "install_dependencies.sh",
        "uv.lock",
        "replit.md",
        "commands/__init__.py",
        "commands/admin.py",
        "commands/fun.py",
        "commands/moderation.py",
        "commands/roles.py",
        "commands/utility.py",
        "commands/custom.py",
        "PERFORMANCE_OPTIMIZATION.md",
        "Dockerfile",
        "render.yaml",
        "HOSTING_README.md"
    ]

    try:
        # Create zip in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add important files
            for file in important_files:
                if os.path.exists(file):
                    zip_file.write(file)

            # Add commands directory
            if os.path.exists('commands'):
                for root, dirs, files in os.walk('commands'):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if os.path.exists(file_path):
                            zip_file.write(file_path)

        zip_buffer.seek(0)

        # Check if any files were actually added
        if zip_buffer.getvalue():
            # Send the zip file
            await ctx.send("✅ Backup created successfully!", file=discord.File(fp=zip_buffer, filename="kabu_backup.zip"))
        else:
            embed = create_embed(f"{get_emoji('cross')} Backup Failed", "No files found to backup!")
            await ctx.send(embed=embed)

    except Exception as e:
        embed = create_embed(f"{get_emoji('cross')} Backup Error", f"Failed to create backup: {str(e)}")
        await ctx.send(embed=embed)

async def setup(bot):
    """Add admin commands to bot"""
    bot.add_command(purge)
    bot.add_command(cbot)
    bot.add_command(lock)
    bot.add_command(unlock)
    bot.add_command(slowmode)
    bot.add_command(nuke)
    bot.add_command(vcpull)
    bot.add_command(setprefix)
    bot.add_command(noprefix)
    bot.add_command(npusers)
    bot.add_command(massban)
    bot.add_command(leaveguild)
    bot.add_command(say)
    bot.add_command(dm_user)
    bot.add_command(listallcmds)
    bot.add_command(backup)
    bot.add_command(vchide)
    bot.add_command(vcunhide)
