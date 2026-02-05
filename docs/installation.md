# Installation Guide

## Quick Install (Recommended)

```bash
curl -sSL https://raw.githubusercontent.com/solentlabs/ai-launcher/master/install.sh | bash
```

The install script:
- Installs pipx (if needed)
- Installs ai-launcher
- Checks for fzf dependency
- Optionally configures Windows Terminal (WSL2)

## Manual Installation

### Ubuntu/Debian/WSL2

```bash
sudo apt install -y pipx fzf
pipx install ai-launcher
pipx ensurepath
```

### macOS

```bash
brew install pipx fzf
pipx install ai-launcher
pipx ensurepath
```

### Windows (PowerShell)

```powershell
choco install pipx fzf
pipx install ai-launcher
pipx ensurepath
```

## From Source

```bash
git clone https://github.com/solentlabs/ai-launcher.git
cd ai-launcher
pip install -e ".[dev]"
```

## Post-Install

After installation, restart your terminal or run:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Verify installation:

```bash
ai-launcher --version
```

## Dependencies

- **Python 3.8+** - Required
- **fzf** - For fuzzy search (install script handles this)
- **Claude Code CLI** - Must be in PATH
- **Git** - For repository detection (optional)

## Troubleshooting

See [Troubleshooting Guide](troubleshooting.md) for common issues.
