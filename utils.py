"""
Utility functions and web dashboard for Discord Moderation Bot
Contains helper functions, Flask web server, and data management
Enhanced with persistent storage for prefixes and new command features
"""

import discord
import json
import os
import threading
import time
from datetime import datetime
from flask import Flask, jsonify
import re
import io

# Bot Configuration
EMBED_COLOR = discord.Color.from_rgb(255, 192, 203)
FOOTER_TEXT = "Made by Onevibe"

# Bot statistics for web dashboard
bot_stats = {
    'status': 'offline',
    'guilds': 0,
    'users': 0,
    'commands_used': 0,
    'uptime': None,
    'last_activity': None
}

# Flask app for web server
app = Flask(__name__)

@app.route('/')
def dashboard():
    """Main dashboard page"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Discord Bot Dashboard</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: #2f3136; 
                color: white; 
                margin: 0; 
                padding: 20px; 
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
                background: #36393f; 
                padding: 30px; 
                border-radius: 10px; 
            }
            .status { 
                padding: 10px; 
                border-radius: 5px; 
                margin: 10px 0; 
            }
            .online { background: #43b581; }
            .offline { background: #f04747; }
            h1 { color: #7289da; }
            .stat { 
                display: inline-block; 
                margin: 10px 20px; 
                text-align: center; 
            }
            .refresh { 
                background: #7289da; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 5px; 
                cursor: pointer; 
            }
            .refresh:hover {
                background: #5b6eae;
            }
            .feature-list {
                background: #2f3136;
                padding: 15px;
                border-radius: 5px;
                margin-top: 20px;
            }
            .new-badge {
                background: #43b581;
                color: white;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
        </style>
        <script>
            function refreshStatus() {
                fetch('/api/status')
                    .then(response => response.json())
                    .then(data => {
                        const statusElement = document.getElementById('status');
                        const statusContainer = statusElement.parentElement;

                        statusElement.textContent = data.status;
                        document.getElementById('guilds').textContent = data.guilds;
                        document.getElementById('users').textContent = data.users;
                        document.getElementById('commands').textContent = data.commands_used;
                        document.getElementById('uptime').textContent = data.uptime || 'Unknown';

                        // Update status color
                        statusContainer.className = 'status ' + (data.status === 'online' ? 'online' : 'offline');
                    })
                    .catch(error => {
                        console.error('Error fetching status:', error);
                        document.getElementById('status').textContent = 'Error';
                    });
            }

            // Auto-refresh every 5 seconds
            setInterval(refreshStatus, 5000);

            // Initial load
            window.onload = refreshStatus;
        </script>
    </head>
    <body>
        <div class="container">
            <h1>🤖 Discord Moderation Bot Dashboard</h1>
            <div class="status offline">
                <strong>Status:</strong> <span id="status">Loading...</span>
            </div>
            <div class="stat">
                <h3 id="guilds">-</h3>
                <p>Servers</p>
            </div>
            <div class="stat">
                <h3 id="users">-</h3>
                <p>Users</p>
            </div>
            <div class="stat">
                <h3 id="commands">-</h3>
                <p>Commands Used</p>
            </div>
            <div class="stat">
                <h3 id="uptime">-</h3>
                <p>Uptime</p>
            </div>
            <br><br>
            <button class="refresh" onclick="refreshStatus()">Refresh Status</button>

            <div class="feature-list">
                <h3>🎵 Enhanced Features</h3>
                <ul>
                    <li>48+ Commands with hybrid support (prefix/slash/no-prefix)</li>
                    <li>Enhanced music system with Spotify URL conversion</li>
                    <li>Complete moderation toolkit with vcpull command</li>
                    <li>Custom command system for role assignment</li>
                    <li><span class="new-badge">NEW</span> List custom commands with <code>listcmds</code></li>
                    <li><span class="new-badge">NEW</span> Persistent server prefixes with <code>setprefix</code></li>
                    <li><span class="new-badge">NEW</span> Steal emojis and stickers with <code>steal</code></li>
                    <li><span class="new-badge">NEW</span> Owner-only <code>say</code> command</li>
                    <li>AFK system and reminders</li>
                    <li>24/7 uptime with auto-restart mechanism</li>
                    <li>Persistent data storage with JSON backup system</li>
                    <li>Web dashboard monitoring with real-time stats</li>
                </ul>
            </div>

            <div style="margin-top: 15px; text-align: center; color: #7289da;">
                <p>Made by Onevibe | Enhanced Music & Command System</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/api/status')
def api_status():
    """API endpoint for bot status"""
    try:
        return jsonify(bot_stats)
    except Exception as e:
        print(f"Error in API status: {e}")
        return jsonify({
            'status': 'error',
            'guilds': 0,
            'users': 0,
            'commands_used': 0,
            'uptime': 'Unknown',
            'error': str(e)
        })

@app.route('/api/ping')
def api_ping():
    """Simple ping endpoint to keep bot alive"""
    return jsonify({
        'status': 'alive',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'uptime': bot_stats.get('uptime', 'Unknown'),
        'bot_status': bot_stats.get('status', 'offline')
    })

def start_web_server():
    """Start the Flask web server in a separate thread"""
    def run_app():
        try:
            app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, threaded=True)
        except Exception as e:
            print(f"❌ Error starting web server: {e}")

    web_thread = threading.Thread(target=run_app, daemon=True)
    web_thread.start()
    print("🌐 Web dashboard started on http://0.0.0.0:5000")

def update_bot_stats(bot):
    """Update bot statistics with rate limiting"""
    try:
        bot_stats['status'] = 'online' if bot.is_ready() else 'offline'
        
        # Only update guild/user counts if bot is ready and we have guilds
        if bot.is_ready() and hasattr(bot, 'guilds') and bot.guilds:
            bot_stats['guilds'] = len(bot.guilds)
            
            # Simplified user count calculation to reduce API calls
            total_users = sum(guild.member_count or 0 for guild in bot.guilds if guild.member_count)
            bot_stats['users'] = total_users
        else:
            bot_stats['guilds'] = 0
            bot_stats['users'] = 0
            
        bot_stats['last_activity'] = datetime.now().isoformat()

        if hasattr(bot, 'start_time'):
            uptime = datetime.now() - bot.start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            bot_stats['uptime'] = f"{hours}h {minutes}m {seconds}s"
        
        # Only print stats update every 5 updates to reduce log spam
        if not hasattr(update_bot_stats, 'call_count'):
            update_bot_stats.call_count = 0
        update_bot_stats.call_count += 1
        
        if update_bot_stats.call_count % 5 == 0:
            print(f"📊 Stats updated: {bot_stats['guilds']} guilds, {bot_stats['users']} users")
            
    except Exception as e:
        print(f"Error updating bot stats: {e}")

# Enhanced persistent storage functions with backup system
def load_data():
    """Load persistent data from JSON file with enhanced error handling"""
    try:
        if not os.path.exists('data.json'):
            # Create default data if file doesn't exist
            default_data = {
                'no_prefix_users': [957110332495630366],  # Include owner by default
                'custom_commands': {},
                'guild_prefixes': {},
                'stolen_emojis': {},
                'stolen_stickers': {},
                'embeds': {},
                'welcome': {},
                'autoroles': {},
                'autoroles_bot': {},
                'aliases': {},
                'gpd_enabled': {}
            }
            save_data(default_data)
            return default_data

        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Ensure all required keys exist with defaults
        required_keys = {
            'no_prefix_users': [957110332495630366],
            'custom_commands': {},
            'guild_prefixes': {},
            'stolen_emojis': {},
            'stolen_stickers': {},
            'embeds': {},
            'welcome': {},
            'autoroles': {},
            'autoroles_bot': {},
            'aliases': {},
            'gpd_enabled': {}
        }

        for key, default_value in required_keys.items():
            if key not in data:
                data[key] = default_value
                print(f"🔧 Added missing key: {key}")

        # Force save to ensure all keys are written
        save_data(data)
        print("💾 Data validated and saved after loading")

        return data

    except json.JSONDecodeError as e:
        print(f"❌ Error reading data.json (corrupted): {e}")
        # Backup corrupted file and create new one
        try:
            import shutil
            shutil.copy('data.json', f'data_backup_corrupted_{int(time.time())}.json')
            print("📁 Corrupted data.json backed up")
        except:
            pass

        default_data = {
            'no_prefix_users': [957110332495630366],
            'custom_commands': {},
            'guild_prefixes': {},
            'stolen_emojis': {},
            'stolen_stickers': {}
        }
        save_data(default_data)
        return default_data

    except Exception as e:
        print(f"❌ Error loading data: {e}")
        default_data = {
            'no_prefix_users': [957110332495630366],
            'custom_commands': {},
            'guild_prefixes': {},
            'stolen_emojis': {},
            'stolen_stickers': {}
        }
        save_data(default_data)
        return default_data

# Global variables for optimized saving
_last_save_time = 0
_save_queue = False

def save_data(data, force_save=False):
    """Save persistent data to JSON file with rate limiting"""
    global _last_save_time, _save_queue
    
    current_time = time.time()
    
    # Rate limit saves to once every 30 seconds unless forced
    if not force_save and current_time - _last_save_time < 30:
        _save_queue = True
        return
    
    try:
        # Create a backup of existing data (only if file exists and is recent)
        if os.path.exists('data.json'):
            try:
                import shutil
                file_age = current_time - os.path.getmtime('data.json')
                if file_age > 300:  # Only backup if file is older than 5 minutes
                    shutil.copy('data.json', 'data_backup.json')
            except Exception as backup_error:
                print(f"Warning: Could not create backup: {backup_error}")

        # Write new data with compact formatting for better performance
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, separators=(',', ':'), ensure_ascii=False)

        _last_save_time = current_time
        _save_queue = False
        print("💾 Data saved successfully")

    except Exception as e:
        print(f"❌ Error saving data: {e}")
        # Try to restore backup if save failed
        if os.path.exists('data_backup.json'):
            try:
                import shutil
                shutil.copy('data_backup.json', 'data.json')
                print("🔄 Restored data from backup")
            except Exception as restore_error:
                print(f"❌ Failed to restore backup: {restore_error}")

def save_data_queued():
    """Save data if there's a queued save"""
    global _save_queue
    if _save_queue:
        # This will be called by a periodic task
        pass

# Enhanced emoji fallback system
def get_emoji(emoji_name):
    """Get custom emoji or fallback to default with more options"""
    emoji_map = {
        'cross': '❌', 'tick': '<a:tick:1398908163016626248>', 'hmmm': '🎭', 'admin': '🛡️',
        'tools': '🛠️', 'speaker': '🔊', 'mute': '🔇', 'image': '🖼️',
        'sleepy': '💤', 'note': '📝', 'lock': '🔒', 'unlock': '🔓',
        'music': '🎵', 'pause': '⏸️', 'play': '▶️', 'stop': '⏹️',
        'skip': '⏭️', 'queue': '📋', 'volume': '🔉', 'list': '📄',
        'steal': '🔰', 'prefix': '⚙️', 'custom': '🎯', 'owner': '👑',
        'new': '🆕', 'settings': '⚙️', 'warning': '⚠️', 'info': 'ℹ️'
    }
    return emoji_map.get(emoji_name, '❓')

# Utility functions
def create_embed(title, description=None, color=EMBED_COLOR):
    """Create a standardized embed with enhanced formatting"""
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=FOOTER_TEXT)
    embed.timestamp = datetime.now()
    return embed

def parse_time(time_str):
    """Parse time string like '10m', '1h', '2d' into seconds"""
    if not time_str:
        return None

    # Remove whitespace and convert to lowercase
    time_str = time_str.strip().lower()

    # Match pattern: number + unit
    match = re.match(r'^(\d+)([smhd])$', time_str)
    if not match:
        return None

    amount, unit = match.groups()
    amount = int(amount)

    # Convert to seconds
    multipliers = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400
    }

    return amount * multipliers.get(unit, 1)

async def has_permissions(ctx, **permissions):
    """Check if context author has specific permissions"""
    if not ctx.guild:
        return False
    
    member = ctx.author
    for permission, required in permissions.items():
        if required and not getattr(member.guild_permissions, permission, False):
            return False
    return True

def has_permissions_sync(member, permission):
    """Sync version for checking member permissions"""
    return getattr(member.guild_permissions, permission, False)

def parse_role_input(guild, role_input):
    """Enhanced role parsing - accepts mention, name, or ID"""
    # Try mention format first
    if role_input.startswith('<@&') and role_input.endswith('>'):
        role_id = int(role_input[3:-1])
        return guild.get_role(role_id)
    
    # Try direct ID
    if role_input.isdigit():
        return guild.get_role(int(role_input))
    
    # Try exact name match (case sensitive)
    role = discord.utils.get(guild.roles, name=role_input)
    if role:
        return role
    
    # Try case insensitive match
    role = discord.utils.get(guild.roles, name__iexact=role_input)
    if role:
        return role
    
    # Try partial match
    for role in guild.roles:
        if role_input.lower() in role.name.lower():
            return role
    
    return None

def replace_placeholders(text, user=None, bot=None, guild=None, channel=None):
    """Replace placeholders in text with actual values"""
    if not text:
        return text
    
    replacements = {}
    
    if user:
        replacements.update({
            '{user}': user.mention,
            '{username}': user.display_name,
            '{user_name}': user.name,
            '{user_id}': str(user.id),
            '{user_avatar}': user.display_avatar.url,
            '{user_discriminator}': user.discriminator if hasattr(user, 'discriminator') else '0'
        })
    
    if bot:
        replacements.update({
            '{bot}': bot.mention,
            '{bot_name}': bot.display_name,
            '{bot_avatar}': bot.display_avatar.url
        })
    
    if guild:
        replacements.update({
            '{server}': guild.name,
            '{server_name}': guild.name,
            '{server_id}': str(guild.id),
            '{server_icon}': guild.icon.url if guild.icon else '',
            '{member_count}': str(guild.member_count)
        })
    
    if channel:
        replacements.update({
            '{channel}': channel.mention,
            '{channel_name}': channel.name,
            '{channel_id}': str(channel.id)
        })
    
    # Replace all placeholders
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, str(value))
    
    return text

def build_embed_from_data(embed_data, user=None, bot=None, guild=None, channel=None):
    """Build Discord embed from stored data with placeholder replacement"""
    # Create embed with replaced title and description
    title = replace_placeholders(embed_data.get('title', ''), user, bot, guild, channel)
    description = replace_placeholders(embed_data.get('description', ''), user, bot, guild, channel)
    
    embed = discord.Embed(title=title, description=description)
    
    # Set color (handle both old and new formats)
    color_value = embed_data.get('color')
    if color_value is not None and color_value != "":
        if isinstance(color_value, int):
            embed.color = discord.Color(color_value)
        elif isinstance(color_value, str):
            try:
                # Remove # if present and convert hex to int
                if color_value.startswith('#'):
                    color_value = color_value[1:]
                embed.color = discord.Color(int(color_value, 16))
            except (ValueError, TypeError):
                pass
    
    # Set thumbnail
    thumbnail_url = embed_data.get('thumbnail')
    if thumbnail_url:
        thumbnail_url = replace_placeholders(thumbnail_url, user, bot, guild, channel)
        embed.set_thumbnail(url=thumbnail_url)
    
    # Set image
    image_url = embed_data.get('image')
    if image_url:
        image_url = replace_placeholders(image_url, user, bot, guild, channel)
        embed.set_image(url=image_url)
    
    # Set footer (handle both old and new formats)
    footer_text = embed_data.get('footer')
    if footer_text:
        footer_text = replace_placeholders(footer_text, user, bot, guild, channel)
        embed.set_footer(text=footer_text)
    
    # Set author
    author_data = embed_data.get('author', {})
    author_name = author_data.get('name') or embed_data.get('author_name')
    if author_name:
        author_name = replace_placeholders(author_name, user, bot, guild, channel)
        author_icon = author_data.get('icon_url') or embed_data.get('author_icon')
        if author_icon:
            author_icon = replace_placeholders(author_icon, user, bot, guild, channel)
        embed.set_author(name=author_name, icon_url=author_icon)
    
    # Set timestamp
    if embed_data.get('timestamp'):
        embed.timestamp = datetime.now()
    
    return embed
