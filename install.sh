#!/usr/bin/env bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Installing ai-launcher...${NC}"

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "Installing pipx..."
    if command -v apt &> /dev/null; then
        sudo apt update && sudo apt install -y pipx
    elif command -v brew &> /dev/null; then
        brew install pipx
    elif command -v choco &> /dev/null; then
        choco install pipx
    else
        echo "Error: Could not detect package manager. Please install pipx manually."
        exit 1
    fi
fi

# Install ai-launcher
echo "Installing ai-launcher..."
pipx install ai-launcher

# Ensure PATH is configured
echo "Configuring PATH..."
pipx ensurepath

# Check if fzf is installed
if ! command -v fzf &> /dev/null; then
    echo ""
    echo "Note: fzf is required for ai-launcher."
    if command -v apt &> /dev/null; then
        read -p "Install fzf now? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo apt install -y fzf
        fi
    else
        echo "Please install fzf manually:"
        echo "  - macOS: brew install fzf"
        echo "  - Windows: choco install fzf"
    fi
fi

# Configure Windows Terminal profile (WSL2 only)
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo ""
    read -p "Configure Windows Terminal profile? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter default projects folder (default: ~/projects): " PROJECTS_PATH
        PROJECTS_PATH=${PROJECTS_PATH:-~/projects}

        # Find Windows Terminal settings
        WT_SETTINGS="$HOME/AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json"

        if [ ! -f "$WT_SETTINGS" ]; then
            # Try to find via /mnt/c path
            WIN_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')
            WT_SETTINGS="/mnt/c/Users/${WIN_USER}/AppData/Local/Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json"
        fi

        if [ -f "$WT_SETTINGS" ]; then
            # Check if profile already exists
            if ! grep -q '"name": "Claude Code"' "$WT_SETTINGS"; then
                echo "Adding Windows Terminal profile..."

                # Generate new GUID
                NEW_GUID=$(uuidgen | tr '[:upper:]' '[:lower:]')

                # Add profile using Python (safer than sed for JSON)
                python3 -c "
import json
import sys

with open('$WT_SETTINGS', 'r') as f:
    config = json.load(f)

# Find WSL icon path
wsl_icon = 'C:\\\\Users\\\\${WIN_USER}\\\\AppData\\\\Local\\\\wsl\\\\{a0446c4a-5b36-463f-b64f-09d8c4c55c8c}\\\\shortcut.ico'

# Add new profile
new_profile = {
    'commandline': 'wsl.exe -d Ubuntu bash -lic \"ai-launcher ${PROJECTS_PATH}\"',
    'guid': '{${NEW_GUID}}',
    'icon': wsl_icon,
    'name': 'Claude Code',
    'startingDirectory': '//wsl.localhost/Ubuntu${PROJECTS_PATH}'
}

config['profiles']['list'].insert(0, new_profile)

# Make it default
config['defaultProfile'] = '{${NEW_GUID}}'

with open('$WT_SETTINGS', 'w') as f:
    json.dump(config, f, indent=4)

print('✓ Windows Terminal profile added!')
"
            else
                echo "Claude Code profile already exists in Windows Terminal"
            fi
        else
            echo "Windows Terminal settings not found, skipping profile configuration"
        fi
    fi
fi

echo ""
echo -e "${GREEN}✓ Installation complete!${NC}"
echo ""
echo "Run: ai-launcher --version"
echo "     ai-launcher ~/projects"
echo ""
echo "Note: You may need to restart your terminal for PATH changes to take effect."
