
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select
from utils import has_permissions, get_emoji, create_embed, save_data, load_data

# Dropdown View for Embed Selection
class EmbedDropdownView(View):
    def __init__(self, bot, ctx, command_type, **kwargs):
        super().__init__(timeout=60)
        self.bot = bot
        self.ctx = ctx
        self.command_type = command_type
        self.kwargs = kwargs
        
        # Add the dropdown
        self.add_item(EmbedDropdown(bot, ctx, command_type, **kwargs))

class EmbedDropdown(Select):
    def __init__(self, bot, ctx, command_type, **kwargs):
        self.bot = bot
        self.ctx = ctx
        self.command_type = command_type
        self.kwargs = kwargs
        
        guild_id = str(ctx.guild.id)
        embeds = bot.data.get('embeds', {}).get(guild_id, {})
        
        # Create options from saved embeds
        options = []
        for embed_name in list(embeds.keys())[:25]:  # Discord limit of 25 options
            options.append(discord.SelectOption(
                label=embed_name[:100],  # Discord limit
                description=f"Select {embed_name}"[:100],
                value=embed_name
            ))
        
        super().__init__(
            placeholder="📋 Choose an embed...",
            min_values=1,
            max_values=1,
            options=options
        )
    
    async def callback(self, interaction: discord.Interaction):
        selected_embed = self.values[0]
        guild_id = str(self.ctx.guild.id)
        
        if self.command_type == "setwelcome":
            # Handle setwelcome logic
            channel = self.kwargs.get('channel')
            message = self.kwargs.get('message')
            
            # Configure welcome
            if 'welcome' not in self.bot.data:
                self.bot.data['welcome'] = {}

            self.bot.data['welcome'][guild_id] = {
                'embed_name': selected_embed,
                'channel_id': channel.id,
                'enabled': True
            }

            # Handle custom message
            message_status = ""
            if message:
                if message.lower() == "none":
                    # Remove custom message if it exists
                    if 'message' in self.bot.data['welcome'][guild_id]:
                        del self.bot.data['welcome'][guild_id]['message']
                    message_status = "\n**Custom Message:** Removed"
                else:
                    # Set custom message
                    self.bot.data['welcome'][guild_id]['message'] = message
                    message_status = f"\n**Custom Message:** Set"

            save_data(self.bot.data)
                        
            # Force sync the data to ensure persistence
            self.bot.data = load_data()

            embed = create_embed(
                f"{get_emoji('tick')} Welcome Configured",
                f"**Embed:** `{selected_embed}`\n**Channel:** {channel.mention}\n**Status:** Enabled{message_status}"
            )

            if message and message.lower() != "none":
                embed.add_field(
                    name="Custom Message Preview",
                    value=f"```{message[:200]}{'...' if len(message) > 200 else ''}```",
                    inline=False
                )
                embed.add_field(
                    name="Available Placeholders",
                    value="`{user}` - mentions the user\n`{username}` - user's name\n`{server}` - server name",
                    inline=False
                )

            await interaction.response.edit_message(embed=embed, view=None)
            
        elif self.command_type == "embedsend":
            # Handle embedsend logic
            target_channel = self.kwargs.get('channel')
            
            # Get saved embed data and recreate
            embed_data = self.bot.data['embeds'][guild_id][selected_embed]

            # Import the build function
            from utils import build_embed_from_data

            # Create embed from saved data with placeholders
            embed_to_send = build_embed_from_data(
                embed_data,
                user=self.ctx.author,
                bot=self.bot.user,
                guild=self.ctx.guild,
                channel=target_channel
            )

            try:
                await target_channel.send(embed=embed_to_send)

                if target_channel != self.ctx.channel:
                    confirmation = create_embed(f"{get_emoji('tick')} Embed Sent", f"Sent **{selected_embed}** to {target_channel.mention}")
                else:
                    confirmation = create_embed(f"{get_emoji('tick')} Embed Sent", f"Sent **{selected_embed}** to this channel")
                
                await interaction.response.edit_message(embed=confirmation, view=None)

            except discord.Forbidden:
                error_embed = create_embed(f"{get_emoji('cross')} Error", f"I don't have permission to send messages in {target_channel.mention}!")
                await interaction.response.edit_message(embed=error_embed, view=None)
                
        elif self.command_type == "embededit":
            # Handle embededit logic
            from embedbuilder import EmbedBuilderView

            embed = create_embed(
                "✏️ Editing Embed",
                f"Editing embed: **{selected_embed}**\n"
                f"Use the buttons below to modify your embed!"
            )

            view = EmbedBuilderView(self.bot, self.ctx, selected_embed)

            # Load existing embed data into the view
            embed_data = self.bot.data['embeds'][guild_id][selected_embed]
            view.raw_title = embed_data.get('title', '')
            view.raw_description = embed_data.get('description', '')
            view.raw_color = embed_data.get('color', '')
            view.raw_thumbnail = embed_data.get('thumbnail', '')
            view.raw_image = embed_data.get('image', '')
            view.raw_footer = embed_data.get('footer', '')
            view.raw_author_name = embed_data.get('author', {}).get('name', '')
            view.raw_author_icon = embed_data.get('author', {}).get('icon_url', '')
            view.timestamp_enabled = embed_data.get('timestamp', False)

            await interaction.response.edit_message(embed=embed, view=view)
            
        elif self.command_type == "testwelcome":
            # Handle testwelcome logic
            user = self.kwargs.get('user')
            
            embed_data = self.bot.data['embeds'][guild_id][selected_embed]

            # Import the build function
            from utils import build_embed_from_data

            # Create test welcome embed with placeholders replaced
            test_embed = build_embed_from_data(
                embed_data,
                user=user,
                bot=self.bot.user,
                guild=self.ctx.guild,
                channel=self.ctx.channel
            )

            # Create container embed
            embed = create_embed(
                "🧪 Welcome Test",
                f"This is how **{selected_embed}** would look as welcome for {user.mention}:"
            )

            await interaction.response.edit_message(embed=embed, view=None)
            await interaction.followup.send(embed=test_embed)


"""
Custom Commands and Features for Discord Bot
Contains custom role commands, aliases, embed management, and welcome system
"""

import discord
from discord.ext import commands
from discord import app_commands
from utils import has_permissions, get_emoji, create_embed, save_data

@commands.hybrid_command(name='listcmds', description='List all custom commands')
async def listcmds(ctx):
    guild_id = str(ctx.guild.id)
    custom_commands = ctx.bot.custom_commands.get(guild_id, {})

    if not custom_commands:
        embed = create_embed(f"{get_emoji('info')} No Custom Commands", "This server has no custom commands!")
        return await ctx.send(embed=embed)

    command_list = []
    for cmd_name, cmd_data in custom_commands.items():
        role_name = cmd_data.get('role_name', 'Unknown Role')
        command_list.append(f"**{cmd_name}** - Assigns `{role_name}` role")

    embed = create_embed(
        "📋 Custom Commands",
        f"**{len(custom_commands)}** custom commands in this server:\n\n" + "\n".join(command_list)
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name='steal', description='Steal custom emoji (including animated) or sticker to this server')
@app_commands.describe(emoji_or_sticker='Emoji or sticker to steal')
async def steal(ctx, *, emoji_or_sticker: str):
    if not await has_permissions(ctx, manage_emojis=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Emojis** permission!")
        return await ctx.send(embed=embed)

    import re
    import aiohttp

    # Parse emoji
    emoji_match = re.match(r'<(a?):(\w+):(\d+)>', emoji_or_sticker.strip())

    if not emoji_match:
        embed = create_embed(
            f"{get_emoji('cross')} Invalid Emoji",
            "Please provide a valid custom emoji!\n"
            "Example: `:emojiname:` or paste the emoji directly"
        )
        return await ctx.send(embed=embed)

    animated = emoji_match.group(1) == 'a'
    name = emoji_match.group(2)
    emoji_id = emoji_match.group(3)

    # Construct emoji URL
    extension = 'gif' if animated else 'png'
    url = f'https://cdn.discordapp.com/emojis/{emoji_id}.{extension}'

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    embed = create_embed(f"{get_emoji('cross')} Download Failed", "Could not download the emoji!")
                    return await ctx.send(embed=embed)

                emoji_data = await resp.read()

        # Add emoji to server
        emoji = await ctx.guild.create_custom_emoji(name=name, image=emoji_data)

        embed = create_embed(
            f"{get_emoji('tick')} Emoji Stolen",
            f"Successfully added {emoji} as `:{name}:`"
        )
        await ctx.send(embed=embed)

    except discord.HTTPException as e:
        if e.status == 400:
            embed = create_embed(f"{get_emoji('cross')} Error", "Invalid emoji data or name!")
        elif e.status == 403:
            embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to manage emojis!")
        else:
            embed = create_embed(f"{get_emoji('cross')} Error", f"Failed to add emoji: {str(e)}")
        await ctx.send(embed=embed)
    except Exception as e:
        embed = create_embed(f"{get_emoji('cross')} Error", f"An error occurred: {str(e)}")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='addcmd', description='Create custom role command')
@app_commands.describe(name='Command name', role='Role to assign', description='Command description')
async def addcmd(ctx, name: str, role: discord.Role, *, description: str = "Custom role command"):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    # Initialize custom commands for guild
    if guild_id not in ctx.bot.custom_commands:
        ctx.bot.custom_commands[guild_id] = {}

    # Check if command already exists
    if name.lower() in ctx.bot.custom_commands[guild_id]:
        embed = create_embed(f"{get_emoji('cross')} Command Exists", f"Command **{name}** already exists!")
        return await ctx.send(embed=embed)

    # Add the custom command
    ctx.bot.custom_commands[guild_id][name.lower()] = {
        'role_id': role.id,
        'role_name': role.name,
        'description': description,
        'created_by': ctx.author.id
    }

    # Save data
    ctx.bot.data['custom_commands'] = ctx.bot.custom_commands
    save_data(ctx.bot.data)

    embed = create_embed(
        f"{get_emoji('tick')} Custom Command Added",
        f"**Command:** {name}\n**Role:** {role.mention}\n**Description:** {description}"
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name='delcmd', description='Delete custom command')
@app_commands.describe(name='Command name to delete')
async def delcmd(ctx, name: str):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    if guild_id not in ctx.bot.custom_commands or name.lower() not in ctx.bot.custom_commands[guild_id]:
        embed = create_embed(f"{get_emoji('cross')} Command Not Found", f"Command **{name}** doesn't exist!")
        return await ctx.send(embed=embed)

    try:
        # Remove the command
        del ctx.bot.custom_commands[guild_id][name.lower()]

        # Save data
        ctx.bot.data['custom_commands'] = ctx.bot.custom_commands
        save_data(ctx.bot.data)

        embed = create_embed(f"{get_emoji('tick')} Custom Command Deleted", f"Command **{name}** has been deleted")
        await ctx.send(embed=embed)

    except Exception as e:
        embed = create_embed(f"{get_emoji('cross')} Error", f"Failed to delete command: {str(e)}")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='addalias', description='Add an alias to an existing command')
@app_commands.describe(alias='New alias name', command='Existing command name')
async def addalias(ctx, alias: str, *, command: str):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    # Initialize aliases for guild
    if 'aliases' not in ctx.bot.data:
        ctx.bot.data['aliases'] = {}
    if guild_id not in ctx.bot.data['aliases']:
        ctx.bot.data['aliases'][guild_id] = {}

    # Check if alias already exists
    if alias.lower() in ctx.bot.data['aliases'][guild_id]:
        embed = create_embed(f"{get_emoji('cross')} Alias Exists", f"Alias **{alias}** already exists!")
        return await ctx.send(embed=embed)

    # Add the alias
    ctx.bot.data['aliases'][guild_id][alias.lower()] = command.lower()
    save_data(ctx.bot.data)

    embed = create_embed(
        f"{get_emoji('tick')} Alias Added",
        f"**Alias:** {alias}\n**Command:** {command}"
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name='delalias', description='Delete an existing alias')
@app_commands.describe(alias='Alias name to delete')
async def delalias(ctx, alias: str):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    if ('aliases' not in ctx.bot.data or 
        guild_id not in ctx.bot.data['aliases'] or 
        alias.lower() not in ctx.bot.data['aliases'][guild_id]):
        embed = create_embed(f"{get_emoji('cross')} Alias Not Found", f"Alias **{alias}** doesn't exist!")
        return await ctx.send(embed=embed)

    # Remove the alias
    del ctx.bot.data['aliases'][guild_id][alias.lower()]
    save_data(ctx.bot.data)

    embed = create_embed(f"{get_emoji('tick')} Alias Deleted", f"Alias **{alias}** has been deleted")
    await ctx.send(embed=embed)

@commands.hybrid_command(name='listalias', description='List all aliases in this server')
async def listalias(ctx):
    guild_id = str(ctx.guild.id)
    aliases = ctx.bot.data.get('aliases', {}).get(guild_id, {})

    if not aliases:
        embed = create_embed(f"{get_emoji('info')} No Aliases", "This server has no command aliases!")
        return await ctx.send(embed=embed)

    alias_list = []
    for alias, command in aliases.items():
        alias_list.append(f"**{alias}** → {command}")

    embed = create_embed(
        "📝 Command Aliases",
        f"**{len(aliases)}** aliases in this server:\n\n" + "\n".join(alias_list)
    )
    await ctx.send(embed=embed)

# Embed management commands (from embedbuilder.py)
@commands.hybrid_command(name="embedadd", description="Create & save custom embed")
@app_commands.describe(name='Name for the embed template')
async def embedadd(ctx, *, name: str):
    if not await has_permissions(ctx, manage_messages=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Messages** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    # Check if embed name already exists
    if ('embeds' in ctx.bot.data and 
        guild_id in ctx.bot.data['embeds'] and 
        name in ctx.bot.data['embeds'][guild_id]):
        embed = create_embed(f"{get_emoji('cross')} Embed Exists", f"Embed **{name}** already exists!")
        return await ctx.send(embed=embed)

    # Import and use the embed builder
    from embedbuilder import EmbedBuilderView

    embed = create_embed(
        "🔧 Embed Builder Started",
        f"Creating embed: **{name}**\n"
        f"Use the buttons below to customize your embed!"
    )

    view = EmbedBuilderView(ctx.bot, ctx, name)
    await ctx.send(embed=embed, view=view)

@commands.hybrid_command(name="embedlist", description="📋 List all saved embeds")
async def embedlist(ctx):
    guild_id = str(ctx.guild.id)
    embeds = ctx.bot.data.get('embeds', {}).get(guild_id, {})

    if not embeds:
        embed = create_embed(f"{get_emoji('info')} No Saved Embeds", "This server has no saved embeds!")
        return await ctx.send(embed=embed)

    embed_list = [f"• **{name}**" for name in embeds.keys()]

    embed = create_embed(
        "📋 Saved Embeds",
        f"**{len(embeds)}** saved embeds:\n\n" + "\n".join(embed_list)
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name="embeddel", description="🗑 Delete a saved embed")
@app_commands.describe(name='Name of embed to delete')
async def embeddel(ctx, *, name: str):
    if not await has_permissions(ctx, manage_messages=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Messages** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    if ('embeds' not in ctx.bot.data or 
        guild_id not in ctx.bot.data['embeds'] or 
        name not in ctx.bot.data['embeds'][guild_id]):
        embed = create_embed(f"{get_emoji('cross')} Embed Not Found", f"Embed **{name}** doesn't exist!")
        return await ctx.send(embed=embed)

    # Delete the embed
    del ctx.bot.data['embeds'][guild_id][name]
    save_data(ctx.bot.data)

    embed = create_embed(f"{get_emoji('tick')} Embed Deleted", f"Embed **{name}** has been deleted")
    await ctx.send(embed=embed)

@commands.hybrid_command(name="embededit", description="✏️ Edit a saved embed")
async def embededit(ctx):
    if not await has_permissions(ctx, manage_messages=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Messages** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    # Check if there are any saved embeds
    if ('embeds' not in ctx.bot.data or 
        guild_id not in ctx.bot.data['embeds'] or 
        not ctx.bot.data['embeds'][guild_id]):
        embed = create_embed(f"{get_emoji('cross')} No Embeds Found", "No saved embeds found! Create one with `embedadd` first.")
        return await ctx.send(embed=embed)

    # Show dropdown to select embed
    view = EmbedDropdownView(ctx.bot, ctx, "embededit")
    embed = create_embed(
        "📋 Choose Embed to Edit",
        "Select an embed from the dropdown below to edit:"
    )
    await ctx.send(embed=embed, view=view)

@commands.hybrid_command(name="embedsend", description="Send a saved embed")
@app_commands.describe(channel='Channel to send to (optional)')
async def embedsend(ctx, channel: discord.TextChannel = None):
    if not await has_permissions(ctx, manage_messages=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Messages** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    # Check if there are any saved embeds
    if ('embeds' not in ctx.bot.data or 
        guild_id not in ctx.bot.data['embeds'] or 
        not ctx.bot.data['embeds'][guild_id]):
        embed = create_embed(f"{get_emoji('cross')} No Embeds Found", "No saved embeds found! Create one with `embedadd` first.")
        return await ctx.send(embed=embed)

    target_channel = channel or ctx.channel

    # Show dropdown to select embed
    view = EmbedDropdownView(ctx.bot, ctx, "embedsend", channel=target_channel)
    embed = create_embed(
        "📋 Choose Embed to Send",
        f"**Target Channel:** {target_channel.mention}\n"
        f"Select an embed from the dropdown below:"
    )
    await ctx.send(embed=embed, view=view)

# Welcome system commands
@commands.hybrid_command(name="setwelcome", description="Set welcome embed, channel and optional custom message")
@app_commands.describe(
    channel='Channel to send welcome messages',
    message='Optional custom message to send above embed (use "none" to remove existing message)'
)
async def setwelcome(ctx, channel: discord.TextChannel = None, *, message: str = None):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    # Check if there are any saved embeds
    if ('embeds' not in ctx.bot.data or 
        guild_id not in ctx.bot.data['embeds'] or 
        not ctx.bot.data['embeds'][guild_id]):
        embed = create_embed(f"{get_emoji('cross')} No Embeds Found", "No saved embeds found! Create one with `embedadd` first.")
        return await ctx.send(embed=embed)

    # If no channel provided, use current channel
    if channel is None:
        channel = ctx.channel

    # Validate channel exists and bot has permissions
    if not isinstance(channel, discord.TextChannel):
        embed = create_embed(f"{get_emoji('cross')} Invalid Channel", "Please provide a valid text channel!")
        return await ctx.send(embed=embed)

    # Check if bot can send messages in the channel
    bot_perms = channel.permissions_for(ctx.guild.me)
    if not bot_perms.send_messages or not bot_perms.embed_links:
        embed = create_embed(
            f"{get_emoji('cross')} Permission Error", 
            f"I don't have permission to send messages or embeds in {channel.mention}!"
        )
        return await ctx.send(embed=embed)

    # Show dropdown to select embed
    view = EmbedDropdownView(ctx.bot, ctx, "setwelcome", channel=channel, message=message)
    embed = create_embed(
        "📋 Choose Welcome Embed",
        f"**Channel:** {channel.mention}\n"
        f"Select an embed from the dropdown below:"
    )
    
    if message:
        if message.lower() == "none":
            embed.add_field(name="Custom Message", value="Will be removed", inline=False)
        else:
            embed.add_field(name="Custom Message Preview", value=f"```{message[:200]}{'...' if len(message) > 200 else ''}```", inline=False)
            embed.add_field(name="Available Placeholders", value="`{user}` - mentions the user\n`{username}` - user's name\n`{server}` - server name", inline=False)
    
    await ctx.send(embed=embed, view=view)

@commands.hybrid_command(name="delwelcome", description="Remove welcome configuration")
async def delwelcome(ctx):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    if 'welcome' in ctx.bot.data and guild_id in ctx.bot.data['welcome']:
        del ctx.bot.data['welcome'][guild_id]
        save_data(ctx.bot.data)
        embed = create_embed(f"{get_emoji('tick')} Welcome Removed", "Welcome system has been disabled and configuration removed")
    else:
        embed = create_embed(f"{get_emoji('info')} Not Configured", "Welcome system is not configured for this server")

    await ctx.send(embed=embed)

@commands.hybrid_command(name="togglewelcome", description="Enable / disable welcome system")
async def togglewelcome(ctx):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    guild_id = str(ctx.guild.id)

    if 'welcome' not in ctx.bot.data or guild_id not in ctx.bot.data['welcome']:
        embed = create_embed(f"{get_emoji('cross')} Not Configured", "Welcome system is not configured! Use `setwelcome` first.")
        return await ctx.send(embed=embed)

    # Toggle enabled status
    current_status = ctx.bot.data['welcome'][guild_id].get('enabled', False)
    ctx.bot.data['welcome'][guild_id]['enabled'] = not current_status
    save_data(ctx.bot.data)

    status = "enabled" if not current_status else "disabled"
    embed = create_embed(f"{get_emoji('tick')} Welcome {status.title()}", f"Welcome system has been {status}")
    await ctx.send(embed=embed)

@commands.hybrid_command(name="testwelcome")
@app_commands.describe(user='User to test welcome message for')
async def testwelcome(ctx, user: discord.Member = None):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)

    user = user or ctx.author
    guild_id = str(ctx.guild.id)

    # Check if welcome is configured
    if 'welcome' in ctx.bot.data and guild_id in ctx.bot.data['welcome']:
        # Use current welcome embed
        welcome_config = ctx.bot.data['welcome'][guild_id]
        embed_name = welcome_config['embed_name']

        # Get the welcome embed and send it
        if ('embeds' in ctx.bot.data and 
            guild_id in ctx.bot.data['embeds'] and 
            embed_name in ctx.bot.data['embeds'][guild_id]):

            embed_data = ctx.bot.data['embeds'][guild_id][embed_name]
            custom_message = welcome_config.get('message', '')

            # Import the build function
            from utils import build_embed_from_data

            # Create test welcome embed with placeholders replaced
            test_embed = build_embed_from_data(
                embed_data,
                user=user,
                bot=ctx.bot.user,
                guild=ctx.guild,
                channel=ctx.channel
            )

            # Create container embed
            embed = create_embed(
                "🧪 Welcome Test (Current Setup)",
                f"This is how the welcome message would look for {user.mention}:"
            )

            await ctx.send(embed=embed)
            
            # Send with custom message if it exists (same as real welcome)
            if custom_message:
                # Replace placeholders in custom message
                processed_message = custom_message.replace('{user}', user.mention)
                processed_message = processed_message.replace('{username}', user.name)
                processed_message = processed_message.replace('{server}', ctx.guild.name)
                await ctx.send(content=processed_message, embed=test_embed)
            else:
                # Send only embed if no custom message
                await ctx.send(embed=test_embed)
        else:
            embed = create_embed(f"{get_emoji('cross')} Embed Not Found", f"Welcome embed **{embed_name}** no longer exists!")
            await ctx.send(embed=embed)
    else:
        # No welcome configured, show dropdown to test any embed
        if ('embeds' not in ctx.bot.data or 
            guild_id not in ctx.bot.data['embeds'] or 
            not ctx.bot.data['embeds'][guild_id]):
            embed = create_embed(f"{get_emoji('cross')} Not Configured", "Welcome system is not configured and no saved embeds found!")
            return await ctx.send(embed=embed)

        # Show dropdown to select embed for testing
        view = EmbedDropdownView(ctx.bot, ctx, "testwelcome", user=user)
        embed = create_embed(
            "📋 Choose Embed to Test",
            f"Welcome system is not configured.\n"
            f"Select an embed to test as welcome for {user.mention}:"
        )
        await ctx.send(embed=embed, view=view)

# This command is now redundant as setwelcome handles custom messages
# @commands.hybrid_command(name="setwelcomemsg", description="Set or update custom welcome message")
# @app_commands.describe(message='Custom message to send above embed (use "none" to remove)')
# async def setwelcomemsg(ctx, *, message: str):
#     if not await has_permissions(ctx, administrator=True):
#         embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
#         return await ctx.send(embed=embed)

#     guild_id = str(ctx.guild.id)

#     if 'welcome' not in ctx.bot.data or guild_id not in ctx.bot.data['welcome']:
#         embed = create_embed(f"{get_emoji('cross')} Not Configured", "Welcome system is not configured! Use `setwelcome` first.")
#         return await ctx.send(embed=embed)

#     if message.lower() == "none":
#         # Remove custom message
#         if 'message' in ctx.bot.data['welcome'][guild_id]:
#             del ctx.bot.data['welcome'][guild_id]['message']
#         save_data(ctx.bot.data)
#         embed = create_embed(f"{get_emoji('tick')} Message Removed", "Custom welcome message has been removed")
#     else:
#         # Set custom message
#         ctx.bot.data['welcome'][guild_id]['message'] = message
#         save_data(ctx.bot.data)
#         embed = create_embed(
#             f"{get_emoji('tick')} Message Updated", 
#             f"Custom welcome message set:\n```{message[:200]}{'...' if len(message) > 200 else ''}```"
#         )
#         embed.add_field(
#             name="Available Placeholders",
#             value="`{user}` - mentions the user\n`{username}` - user's name\n`{server}` - server name",
#             inline=False
#         )

#     await ctx.send(embed=embed)

# Setup function to add commands to bot

async def setup(bot):
    """Add custom commands to bot"""
    bot.add_command(listcmds)
    bot.add_command(steal)
    bot.add_command(addcmd)
    bot.add_command(delcmd)
    bot.add_command(addalias)
    bot.add_command(delalias)
    bot.add_command(listalias)
    bot.add_command(embedadd)
    bot.add_command(embedlist)
    bot.add_command(embeddel)
    bot.add_command(embededit)
    bot.add_command(embedsend)
    bot.add_command(setwelcome)
    bot.add_command(delwelcome)
    bot.add_command(togglewelcome)
    bot.add_command(testwelcome)
    # bot.add_command(setwelcomemsg) # This command is now redundant
