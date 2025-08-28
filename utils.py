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
    """Simple, error-free dashboard page"""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Discord Bot Dashboard</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 900px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: gradientShift 3s ease infinite;
        }
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }
        .status-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 30px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #f04747;
            margin-right: 10px;
            animation: pulse 2s infinite;
        }
        .status-online { background: #43b581; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-5px);
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #4ecdc4;
        }
        .stat-label {
            font-size: 1.1em;
            opacity: 0.8;
        }
        .refresh-btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 20px auto;
            display: block;
        }
        .refresh-btn:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        .features {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            margin-top: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        .features h3 {
            margin-bottom: 20px;
            color: #4ecdc4;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .feature-item {
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            border-left: 4px solid #4ecdc4;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            opacity: 0.7;
        }
        .loading { opacity: 0.6; }
        .error { color: #ff6b6b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Discord Bot Dashboard</h1>
            <p>Real-time monitoring for your Discord moderation bot</p>
        </div>

        <div class="status-card">
            <h2>
                <span class="status-indicator" id="status-indicator"></span>
                Bot Status: <span id="status">Loading...</span>
            </h2>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="guilds">-</div>
                <div class="stat-label">Servers</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="users">-</div>
                <div class="stat-label">Users</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="commands">-</div>
                <div class="stat-label">Commands Used</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="uptime">-</div>
                <div class="stat-label">Uptime</div>
            </div>
        </div>

        <button class="refresh-btn" onclick="refreshStatus()">🔄 Refresh Status</button>

        <div class="features">
            <h3>✨ Bot Features</h3>
            <div class="feature-grid">
                <div class="feature-item">
                    <strong>🛡️ Moderation</strong><br>
                    Complete moderation toolkit with ban, kick, mute, warn, and more
                </div>
                <div class="feature-item">
                    <strong>👑 Role Management</strong><br>
                    Advanced role assignment with custom commands and autoroles
                </div>
                <div class="feature-item">
                    <strong>🎉 Fun Commands</strong><br>
                    Games, polls, jokes, and entertainment features
                </div>
                <div class="feature-item">
                    <strong>🛠️ Utilities</strong><br>
                    User info, server stats, AFK system, and more tools
                </div>
                <div class="feature-item">
                    <strong>🎨 Custom Embeds</strong><br>
                    Create and manage beautiful custom embed messages
                </div>
                <div class="feature-item">
                    <strong>⚡ Hybrid Commands</strong><br>
                    Supports both slash commands and prefix commands
                </div>
            </div>
        </div>

        <div class="footer">
            <p>Made with ❤️ by Onevibe | Powered by Discord.py</p>
        </div>
    </div>

    <script>
        let refreshTimeout;
        
        function refreshStatus() {
            clearTimeout(refreshTimeout);
            
            const statusEl = document.getElementById('status');
            const indicatorEl = document.getElementById('status-indicator');
            
            // Show loading state
            statusEl.textContent = 'Loading...';
            statusEl.className = 'loading';
            
            fetch('/api/status')
                .then(response => {
                    if (!response.ok) throw new Error('Network error');
                    return response.json();
                })
                .then(data => {
                    // Update status
                    statusEl.textContent = data.status || 'Unknown';
                    statusEl.className = '';
                    
                    // Update indicator
                    indicatorEl.className = 'status-indicator ' + 
                        (data.status === 'online' ? 'status-online' : '');
                    
                    // Update stats safely
                    document.getElementById('guilds').textContent = data.guilds || '0';
                    document.getElementById('users').textContent = data.users || '0';
                    document.getElementById('commands').textContent = data.commands_used || '0';
                    document.getElementById('uptime').textContent = data.uptime || 'Unknown';
                })
                .catch(error => {
                    console.error('Error:', error);
                    statusEl.textContent = 'Offline';
                    statusEl.className = 'error';
                    indicatorEl.className = 'status-indicator';
                });
            
            // Schedule next refresh (every 30 seconds to reduce load)
            refreshTimeout = setTimeout(refreshStatus, 30000);
        }
        
        // Initial load
        document.addEventListener('DOMContentLoaded', refreshStatus);
    </script>
</body>
</html>"""

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
