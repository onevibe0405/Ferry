#!/bin/bash

echo "🔧 Installing system dependencies..."
echo "No additional system dependencies required - bot runs with Python packages only"

echo "📦 Installing Python packages..."

# Install or upgrade pip
pip install --upgrade pip

# Install required packages with hosting-friendly options
pip install -r requirements.txt --no-cache-dir

echo "✅ Dependencies installed successfully!"
echo "🤖 You can now start the bot with: python main.py"
