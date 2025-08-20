"""
Role Management Commands for Discord Bot
Contains role creation, assignment, removal, and custom role commands
"""

import discord
from discord.ext import commands
from discord import app_commands
from utils import has_permissions, get_emoji, create_embed, parse_role_input, save_data
from datetime import datetime

# Role Management Commands
@commands.hybrid_command(name='addrole', description='Add role to a user')
@app_commands.describe(user='User to add role to', role='Role to add')
async def addrole(ctx, user: discord.Member, *, role: str):
    if not await has_permissions(ctx, manage_roles=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Roles** permission!")
        return await ctx.send(embed=embed)
    
    role_obj = parse_role_input(ctx.guild, role)
    if not role_obj:
        embed = create_embed(f"{get_emoji('cross')} Role Not Found", f"Role **{role}** doesn't exist!")
        return await ctx.send(embed=embed)
    
    try:
        await user.add_roles(role_obj)
        embed = create_embed(f"{get_emoji('tick')} Role Added", f"Added **{role}** to {user.mention}")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to manage this role!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='removerole', description='Remove role from a user')
@app_commands.describe(user='User to remove role from', role='Role to remove')
async def removerole(ctx, user: discord.Member, *, role: str):
    if not await has_permissions(ctx, manage_roles=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Roles** permission!")
        return await ctx.send(embed=embed)
    
    role_obj = parse_role_input(ctx.guild, role)
    if not role_obj:
        embed = create_embed(f"{get_emoji('cross')} Role Not Found", f"Role **{role}** doesn't exist!")
        return await ctx.send(embed=embed)
    
    try:
        await user.remove_roles(role_obj)
        embed = create_embed(f"{get_emoji('tick')} Role Removed", f"Removed **{role}** from {user.mention}")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to manage this role!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='createrole', description='Create a new role')
@app_commands.describe(name='Name of the role', color='Hex color code (optional)', icon='Role icon emoji (optional)')
async def createrole(ctx, name: str, color: str = None, icon: str = None):
    if not await has_permissions(ctx, manage_roles=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Roles** permission!")
        return await ctx.send(embed=embed)
    
    role_color = discord.Color.default()
    if color:
        try:
            role_color = discord.Color(int(color.replace('#', ''), 16))
        except ValueError:
            embed = create_embed(f"{get_emoji('cross')} Invalid Color", "Please provide a valid hex color code!")
            return await ctx.send(embed=embed)
    
    # Handle role icon
    role_icon = None
    if icon:
        try:
            # Check if it's a custom emoji
            if icon.startswith('<') and icon.endswith('>'):
                # Custom emoji format: <:name:id> or <a:name:id>
                emoji_id = icon.split(':')[-1][:-1]
                custom_emoji = ctx.bot.get_emoji(int(emoji_id))
                if custom_emoji:
                    # Get the emoji image as bytes
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(str(custom_emoji.url)) as resp:
                            if resp.status == 200:
                                role_icon = await resp.read()
                else:
                    embed = create_embed(f"{get_emoji('cross')} Invalid Emoji", "Could not find that custom emoji!")
                    return await ctx.send(embed=embed)
            else:
                # Unicode emoji - Discord API expects bytes for role icons
                # We'll skip unicode emojis as they need special handling
                embed = create_embed(f"{get_emoji('cross')} Emoji Type", "Please use a custom emoji for role icons!")
                return await ctx.send(embed=embed)
        except Exception as e:
            embed = create_embed(f"{get_emoji('cross')} Icon Error", f"Error processing role icon: {str(e)}")
            return await ctx.send(embed=embed)
    
    try:
        role = await ctx.guild.create_role(name=name, color=role_color, display_icon=role_icon)
        
        embed = create_embed(f"{get_emoji('tick')} Role Created", f"Created role **{role.name}**")
        if role_icon:
            embed.add_field(name="Icon", value="✅ Role icon set successfully!", inline=False)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to create roles!")
        await ctx.send(embed=embed)
    except discord.HTTPException as e:
        if "50035" in str(e):
            embed = create_embed(f"{get_emoji('cross')} Icon Error", "Role icon file is too large or invalid format!")
        else:
            embed = create_embed(f"{get_emoji('cross')} Error", f"Failed to create role: {str(e)}")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='deleterole', description='Delete a role')
@app_commands.describe(role='Role to delete')
async def deleterole(ctx, *, role: str):
    if not await has_permissions(ctx, manage_roles=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Roles** permission!")
        return await ctx.send(embed=embed)
    
    role_obj = parse_role_input(ctx.guild, role)
    if not role_obj:
        embed = create_embed(f"{get_emoji('cross')} Role Not Found", f"Role **{role}** doesn't exist!")
        return await ctx.send(embed=embed)
    
    try:
        await role_obj.delete()
        embed = create_embed(f"{get_emoji('tick')} Role Deleted", f"Deleted role **{role}**")
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", "I don't have permission to delete this role!")
        await ctx.send(embed=embed)

@commands.hybrid_command(name='massrole', description='Add role to multiple users')
@app_commands.describe(role='Role to add', users='Users to add role to (mention them)')
async def massrole(ctx, role: str, users: commands.Greedy[discord.Member]):
    if not await has_permissions(ctx, manage_roles=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Manage Roles** permission!")
        return await ctx.send(embed=embed)
    
    if not users:
        embed = create_embed(f"{get_emoji('cross')} No Users", "Please mention users to add the role to!")
        return await ctx.send(embed=embed)
    
    role_obj = parse_role_input(ctx.guild, role)
    if not role_obj:
        embed = create_embed(f"{get_emoji('cross')} Role Not Found", f"Role **{role}** doesn't exist!")
        return await ctx.send(embed=embed)
    
    # Check role hierarchy
    if role_obj >= ctx.guild.me.top_role:
        embed = create_embed(f"{get_emoji('cross')} Hierarchy Error", f"I can't assign **{role_obj.name}** - it's higher than my role!")
        return await ctx.send(embed=embed)
    
    success_count = 0
    failed_users = []
    
    # Send initial message
    progress_embed = create_embed(f"{get_emoji('loading')} Processing...", f"Adding **{role_obj.name}** to {len(users)} users...")
    progress_msg = await ctx.send(embed=progress_embed)
    
    for user in users:
        try:
            if role_obj not in user.roles:
                await user.add_roles(role_obj, reason=f"Mass role assignment by {ctx.author}")
                success_count += 1
            else:
                success_count += 1  # Already has role, count as success
        except discord.Forbidden:
            failed_users.append(f"{user.name} (No permission)")
        except discord.HTTPException as e:
            failed_users.append(f"{user.name} (HTTP Error)")
        except Exception as e:
            failed_users.append(f"{user.name} (Unknown error)")
    
    # Update with results
    result_embed = create_embed(
        f"{get_emoji('tick')} Mass Role Assignment Complete",
        f"**Successfully added** {role_obj.mention} **to {success_count}/{len(users)} users**"
    )
    
    if failed_users and len(failed_users) <= 10:
        result_embed.add_field(
            name="Failed Users",
            value="\n".join(failed_users[:10]),
            inline=False
        )
    elif failed_users:
        result_embed.add_field(
            name="Failed Users",
            value=f"{len(failed_users)} users failed (too many to display)",
            inline=False
        )
    
    await progress_msg.edit(embed=result_embed)

@commands.hybrid_command(name='autorole', description='Add autorole for new members')
@app_commands.describe(role='Role to auto-assign to new members')
async def autorole(ctx, *, role: str = None):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)
    
    guild_id = str(ctx.guild.id)
    
    if not role:
        # Show current autoroles
        current_autoroles = ctx.bot.data.get('autoroles', {}).get(guild_id, [])
        if isinstance(current_autoroles, str):
            # Convert old single autorole format to list
            current_autoroles = [current_autoroles]
            ctx.bot.data.setdefault('autoroles', {})[guild_id] = current_autoroles
            save_data(ctx.bot.data)
        
        if current_autoroles:
            autorole_list = []
            for role_id in current_autoroles:
                role_obj = ctx.guild.get_role(int(role_id))
                if role_obj:
                    autorole_list.append(f"• **{role_obj.name}** ({role_obj.mention})")
                else:
                    autorole_list.append(f"• Role not found (ID: {role_id})")
            
            embed = create_embed(
                f"{get_emoji('info')} Current Autoroles", 
                f"New members get these roles:\n\n" + "\n".join(autorole_list)
            )
        else:
            embed = create_embed(f"{get_emoji('info')} No Autorole", "No autoroles are currently set")
        return await ctx.send(embed=embed)
    
    if role.lower() == "none" or role.lower() == "disable":
        # Disable all autoroles
        if 'autoroles' not in ctx.bot.data:
            ctx.bot.data['autoroles'] = {}
        
        if guild_id in ctx.bot.data['autoroles']:
            del ctx.bot.data['autoroles'][guild_id]
            save_data(ctx.bot.data)
            embed = create_embed(f"{get_emoji('tick')} All Autoroles Disabled", "All autoroles have been disabled")
        else:
            embed = create_embed(f"{get_emoji('info')} No Autoroles", "No autoroles were set")
        return await ctx.send(embed=embed)
    
    role_obj = parse_role_input(ctx.guild, role)
    if not role_obj:
        embed = create_embed(f"{get_emoji('cross')} Role Not Found", f"Role **{role}** doesn't exist!")
        return await ctx.send(embed=embed)
    
    # Initialize autoroles structure
    if 'autoroles' not in ctx.bot.data:
        ctx.bot.data['autoroles'] = {}
    
    # Get current autoroles for this guild
    current_autoroles = ctx.bot.data['autoroles'].get(guild_id, [])
    if isinstance(current_autoroles, str):
        # Convert old single autorole format to list
        current_autoroles = [current_autoroles]
    
    # Check if role is already in autoroles
    role_id_str = str(role_obj.id)
    if role_id_str in current_autoroles:
        embed = create_embed(f"{get_emoji('cross')} Already Set", f"**{role_obj.name}** is already an autorole!")
        return await ctx.send(embed=embed)
    
    # Add new autorole
    current_autoroles.append(role_id_str)
    ctx.bot.data['autoroles'][guild_id] = current_autoroles
    save_data(ctx.bot.data)
    
    embed = create_embed(f"{get_emoji('tick')} Autorole Added", f"**{role_obj.name}** added to autoroles!\nNew members will get this role automatically.")
    await ctx.send(embed=embed)

# Pre-defined role assignment commands
@commands.hybrid_command(name='gif', description='Assign Gif exe role')
async def gif(ctx, user: discord.Member = None):
    await toggle_role(ctx, user or ctx.author, "Gif exe")

@commands.hybrid_command(name='img', description='Assign Attach exe role')
async def img(ctx, user: discord.Member = None):
    await toggle_role(ctx, user or ctx.author, "Attach exe")

@commands.hybrid_command(name='vce', description='Assign Vc exe role')
async def vce(ctx, user: discord.Member = None):
    await toggle_role(ctx, user or ctx.author, "Vc exe")

@commands.hybrid_command(name='ext', description='Assign Ext exe role')
async def ext(ctx, user: discord.Member = None):
    await toggle_role(ctx, user or ctx.author, "Ext exe")

@commands.hybrid_command(name='nick', description='Assign nick exe role')
async def nick(ctx, user: discord.Member = None):
    await toggle_role(ctx, user or ctx.author, "nick exe")

@commands.hybrid_command(name='req', description='Assign Req role')
async def req(ctx, user: discord.Member = None):
    await toggle_role(ctx, user or ctx.author, "Req")

async def toggle_role(ctx, user, role_name):
    """Helper function to toggle roles"""
    role = discord.utils.get(ctx.guild.roles, name=role_name)
    
    if not role:
        embed = create_embed(f"{get_emoji('cross')} Role Not Found", f"The **{role_name}** role doesn't exist in this server!")
        return await ctx.send(embed=embed)
    
    try:
        if role in user.roles:
            await user.remove_roles(role)
            embed = create_embed(f"{get_emoji('tick')} Role Removed", f"Removed **{role_name}** from {user.mention}")
        else:
            await user.add_roles(role)
            embed = create_embed(f"{get_emoji('tick')} Role Added", f"Added **{role_name}** to {user.mention}")
        
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = create_embed(f"{get_emoji('cross')} Error", f"I don't have permission to manage the **{role_name}** role!")
        await ctx.send(embed=embed)



@commands.hybrid_command(name='autoroleremove', description='Remove specific autorole from this server')
@app_commands.describe(role='Role to remove from autoroles (optional)')
async def autoroleremove(ctx, *, role: str = None):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)
    
    guild_id = str(ctx.guild.id)
    
    # Check if autoroles exist for this server
    if 'autoroles' not in ctx.bot.data or guild_id not in ctx.bot.data['autoroles']:
        embed = create_embed(f"{get_emoji('info')} No Autoroles", "No autoroles are set in this server")
        return await ctx.send(embed=embed)
    
    current_autoroles = ctx.bot.data['autoroles'][guild_id]
    if isinstance(current_autoroles, str):
        # Convert old single autorole format to list
        current_autoroles = [current_autoroles]
        ctx.bot.data['autoroles'][guild_id] = current_autoroles
    
    if not current_autoroles:
        embed = create_embed(f"{get_emoji('info')} No Autoroles", "No autoroles are set in this server")
        return await ctx.send(embed=embed)
    
    if not role:
        # Show all autoroles with options to remove
        autorole_options = []
        valid_autoroles = []
        
        for i, role_id in enumerate(current_autoroles):
            role_obj = ctx.guild.get_role(int(role_id))
            if role_obj:
                autorole_options.append(f"`{i+1}.` **{role_obj.name}** ({role_obj.mention})")
                valid_autoroles.append((role_id, role_obj.name))
            else:
                autorole_options.append(f"`{i+1}.` Role not found (ID: {role_id})")
                valid_autoroles.append((role_id, f"Unknown Role (ID: {role_id})"))
        
        embed = create_embed(
            f"{get_emoji('list')} Select Autorole to Remove",
            f"Current autoroles:\n\n" + "\n".join(autorole_options) + 
            f"\n\n**Usage:** `autoroleremove <role name/mention/ID>`\n" +
            f"**Example:** `autoroleremove @Member`"
        )
        return await ctx.send(embed=embed)
    
    # Find and remove specific role
    role_obj = parse_role_input(ctx.guild, role)
    if not role_obj:
        embed = create_embed(f"{get_emoji('cross')} Role Not Found", f"Role **{role}** doesn't exist!")
        return await ctx.send(embed=embed)
    
    role_id_str = str(role_obj.id)
    if role_id_str not in current_autoroles:
        embed = create_embed(f"{get_emoji('cross')} Not an Autorole", f"**{role_obj.name}** is not set as an autorole!")
        return await ctx.send(embed=embed)
    
    # Remove the specific autorole
    current_autoroles.remove(role_id_str)
    
    if not current_autoroles:
        # If no autoroles left, remove the entry entirely
        del ctx.bot.data['autoroles'][guild_id]
    else:
        ctx.bot.data['autoroles'][guild_id] = current_autoroles
    
    save_data(ctx.bot.data)
    
    embed = create_embed(
        f"{get_emoji('tick')} Autorole Removed",
        f"Successfully removed **{role_obj.name}** from autoroles\n"
        f"New members will no longer receive this role automatically"
    )
    await ctx.send(embed=embed)

@commands.hybrid_command(name='autorolebot', description='Set autorole for new bots')
@app_commands.describe(role='Role to auto-assign to new bots')
async def autorolebot(ctx, *, role: str = None):
    if not await has_permissions(ctx, administrator=True):
        embed = create_embed(f"{get_emoji('cross')} No Permission", "You need **Administrator** permission!")
        return await ctx.send(embed=embed)
    
    guild_id = str(ctx.guild.id)
    
    if not role:
        # Show current bot autorole
        current_autorole = ctx.bot.data.get('autoroles_bot', {}).get(guild_id)
        if current_autorole:
            role_obj = ctx.guild.get_role(int(current_autorole))
            if role_obj:
                embed = create_embed(f"{get_emoji('info')} Current Bot Autorole", f"New bots get: **{role_obj.name}**")
            else:
                embed = create_embed(f"{get_emoji('cross')} Bot Autorole Not Found", "The bot autorole no longer exists!")
        else:
            embed = create_embed(f"{get_emoji('info')} No Bot Autorole", "No bot autorole is currently set")
        return await ctx.send(embed=embed)
    
    if role.lower() == "none" or role.lower() == "disable":
        # Disable bot autorole
        if 'autoroles_bot' not in ctx.bot.data:
            ctx.bot.data['autoroles_bot'] = {}
        
        if guild_id in ctx.bot.data['autoroles_bot']:
            del ctx.bot.data['autoroles_bot'][guild_id]
            save_data(ctx.bot.data)
            embed = create_embed(f"{get_emoji('tick')} Bot Autorole Disabled", "Bot autorole has been disabled")
        else:
            embed = create_embed(f"{get_emoji('info')} No Bot Autorole", "No bot autorole was set")
        return await ctx.send(embed=embed)
    
    role_obj = parse_role_input(ctx.guild, role)
    if not role_obj:
        embed = create_embed(f"{get_emoji('cross')} Role Not Found", f"Role **{role}** doesn't exist!")
        return await ctx.send(embed=embed)
    
    # Set bot autorole
    if 'autoroles_bot' not in ctx.bot.data:
        ctx.bot.data['autoroles_bot'] = {}
    
    ctx.bot.data['autoroles_bot'][guild_id] = str(role_obj.id)
    save_data(ctx.bot.data)
    
    embed = create_embed(f"{get_emoji('tick')} Bot Autorole Set", f"New bots will get: **{role_obj.name}**")
    await ctx.send(embed=embed)

async def setup(bot):
    """Add role commands to bot"""
    bot.add_command(addrole)
    bot.add_command(removerole)
    bot.add_command(createrole)
    bot.add_command(deleterole)
    bot.add_command(massrole)
    bot.add_command(autorole)
    bot.add_command(autoroleremove)
    bot.add_command(autorolebot)
    bot.add_command(gif)
    bot.add_command(img)
    bot.add_command(vce)
    bot.add_command(ext)
    bot.add_command(nick)
    bot.add_command(req)
