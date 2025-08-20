"""
Commands package for Discord Bot
Organized command modules by category
"""

from .moderation import setup as setup_moderation
from .utility import setup as setup_utility  
from .fun import setup as setup_fun
from .roles import setup as setup_roles
from .admin import setup as setup_admin
from .custom import setup as setup_custom

async def setup_all_commands(bot):
    """Load all command modules"""
    await setup_moderation(bot)
    await setup_utility(bot)
    await setup_fun(bot)
    await setup_roles(bot)
    await setup_admin(bot)
    await setup_custom(bot)
    
    print(f"✅ Loaded {len(bot.commands)} commands from organized modules")
