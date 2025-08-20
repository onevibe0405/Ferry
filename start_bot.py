#!/usr/bin/env python3
"""
Discord Bot Startup Script
Ensures all dependencies are available and starts the bot safely
"""

import sys
import os
import subprocess
import importlib.util

def check_dependency(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    spec = importlib.util.find_spec(import_name)
    return spec is not None

def install_package(package):
    """Install a Python package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    print("🤖 Discord Bot Startup Check")
    print("=" * 40)
    
    # Check environment variables
    bot_token = os.getenv('DISCORD_BOT_TOKEN')
    if not bot_token or bot_token == 'your_bot_token_here':
        print("❌ DISCORD_BOT_TOKEN environment variable is not set!")
        print("   Please set it with your bot token from Discord Developer Portal")
        print("   Example: export DISCORD_BOT_TOKEN='your_actual_token_here'")
        return False
    
    print("✅ Bot token found")
    
    # Check Python dependencies
    required_packages = [
        ('discord.py', 'discord'),
        ('yt-dlp', 'yt_dlp'),
        ('aiohttp', 'aiohttp'),
        ('requests', 'requests'),
        ('Flask', 'flask'),
        ('PyNaCl', 'nacl')
    ]
    
    missing_packages = []
    for package, import_name in required_packages:
        if not check_dependency(package, import_name):
            missing_packages.append(package)
            print(f"❌ Missing: {package}")
        else:
            print(f"✅ Found: {package}")
    
    # Install missing packages
    if missing_packages:
        print(f"\n📦 Installing {len(missing_packages)} missing packages...")
        for package in missing_packages:
            print(f"   Installing {package}...")
            if install_package(package):
                print(f"   ✅ {package} installed")
            else:
                print(f"   ❌ Failed to install {package}")
                return False
    
    # Check FFmpeg
    if not check_ffmpeg():
        print("\n❌ FFmpeg is not installed!")
        print("   FFmpeg is required for music functionality")
        print("   Install it with: apt-get install ffmpeg (Linux)")
        print("   Or run: ./install_dependencies.sh")
        print("   The bot will start but music commands may not work.")
    else:
        print("✅ FFmpeg found")
    
    # Check data file
    if not os.path.exists('data.json'):
        print("⚠️  data.json not found, will be created on first run")
    else:
        print("✅ data.json found")
    
    print("\n🚀 Starting Discord Bot...")
    print("=" * 40)
    
    # Import and run the bot
    try:
        import main
        print("✅ Bot started successfully!")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
