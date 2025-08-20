# Discord Moderation Bot

## Overview

This is a comprehensive Discord moderation bot built with discord.py that provides 78 commands for server management and custom functionality. The bot features a hybrid command system supporting both traditional prefix commands and modern slash commands, along with advanced features like custom role assignment commands, embed builders, and a web dashboard for monitoring. Music functionality has been completely removed to eliminate hosting complications.

## User Preferences

Preferred communication style: Simple, everyday language.

## Performance Notes

- **Replit Performance**: ~40ms latency (optimized environment)
- **Render Performance**: ~80-90ms latency (typical for hosting platforms)
- Performance difference is normal due to hosting platform variations
- See PERFORMANCE_OPTIMIZATION.md for hosting platform optimization tips

## System Architecture

### Core Bot Framework
- **Discord.py Library**: Uses discord.py 2.5.2+ with full intents for comprehensive Discord API access
- **Hybrid Commands**: Implements both traditional prefix commands and modern slash commands for maximum compatibility
- **Dynamic Prefix System**: Supports per-guild custom prefixes stored in JSON, with fallback to default prefix
- **No-Prefix Users**: Special user list that can execute commands without prefixes for convenience
- **Modular Architecture**: Commands organized into separate category files for better maintainability and scalability

### Data Management
- **JSON Storage**: Uses file-based JSON storage in `data.json` for persistent configuration
- **Backup System**: Automatic backup creation for data integrity
- **Data Structure**: Organized storage for guild prefixes, custom commands, role mappings, stolen emojis/stickers, command aliases, and embed templates
- **Real-time Updates**: Live data saving and loading for configuration changes

### Permission & Security
- **Role-based Access**: Commands require appropriate Discord permissions
- **Owner Restrictions**: Certain commands restricted to bot owner only
- **Permission Checking**: Built-in permission validation before command execution
- **Guild-specific Settings**: Per-server configuration isolation

### Custom Command System
- **Role Assignment**: Custom commands that assign specific roles to users
- **Placeholder Support**: Dynamic content replacement in custom embeds ({user}, {username}, {user_avatar})
- **Guild-specific Commands**: Custom commands isolated per Discord server
- **Alias System**: Command aliases for different languages/preferences

### Embed Builder
- **Interactive UI**: Discord button-based interface for embed creation
- **Real-time Preview**: Live embed preview during creation
- **Template Storage**: Save and reuse embed templates
- **Rich Content Support**: Support for images, thumbnails, footers, authors, and timestamps

### Music System - REMOVED
- Music functionality completely disabled to eliminate hosting platform complications
- Removed yt-dlp dependency and YouTube/Spotify integration
- Voice commands (play, pause, skip, queue, volume) no longer available
- Search command also removed due to YouTube authentication issues
- Total commands reduced from 89 to 78 after removing all music-related functionality
- All music dependencies (yt-dlp, pynacl, FFmpeg) removed for clean hosting

### Web Dashboard
- **Flask Server**: Built-in web server for bot monitoring
- **Real-time Stats**: Live bot statistics including guild count, user count, uptime
- **Status Monitoring**: Bot status and activity tracking
- **REST API**: JSON endpoints for programmatic access to bot stats

### Command Categories (Organized Structure)
- **Moderation** (`commands/moderation.py`): ban, kick, mute, warn, timeout, unban
- **Utility** (`commands/utility.py`): userinfo, serverinfo, avatar, ping, uptime, calculator
- **Fun** (`commands/fun.py`): joke, fact, 8ball, dice, ship, poll, coinflip
- **Roles** (`commands/roles.py`): addrole, createrole, massrole, autorole, gif, img, vce
- **Admin** (`commands/admin.py`): purge, lock, slowmode, setprefix, noprefix, backup (creates zip files of required project files)
- **Custom** (`commands/custom.py`): addcmd, delcmd, listcmds, embedsend, welcome system
- **Voice** (`voice.py`): DELETED - File removed as all music commands were disabled
- **Search** (`search.py`): DISABLED - Search command removed due to YouTube authentication complications

## External Dependencies

### Required Python Packages
- **discord.py**: Core Discord API wrapper and bot framework
- **aiohttp**: Async HTTP client for web requests
- **flask**: Web server framework for dashboard
- **requests**: HTTP library for API calls
- **psutil**: System and process utilities
- **python-dotenv**: Environment variable management
- **pynacl**: REMOVED - No longer required for voice functionality
- **yt-dlp**: REMOVED - No longer required

### System Dependencies
- **Python 3.8+**: Minimum Python version requirement
- **FFmpeg**: REMOVED - No longer required as audio processing is disabled

### Discord Services
- **Discord Bot Token**: Required environment variable for bot authentication
- **Discord Developer Portal**: Bot application and permissions management
- **Discord Guilds**: Server-specific configurations and command execution

### External APIs
- **YouTube**: Video and audio content streaming
- **Spotify**: Music URL processing and metadata
- **Discord CDN**: Image and asset hosting for embeds

### Environment Configuration
- **DISCORD_BOT_TOKEN**: Bot authentication token
- **BOT_PREFIX**: Default command prefix (fallback: "!")
- **Port Configuration**: Web server port for dashboard access