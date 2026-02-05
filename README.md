# AI Launcher

Universal AI CLI launcher with local context management. Launch any AI coding assistant from a single entry point with persistent context across sessions.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Local-First Design** - All context and data stays on your machine. No cloud dependencies.

## What Is This?

A terminal-first launcher that:
- 🎯 **Single Entry Point** - One command to access all your AI coding tools
- 🧠 **Context Management** - Maintains persistent context across sessions
- 🔒 **Local-Only** - Everything stays on your machine
- 🔍 **Project Switching** - Fuzzy search across all your projects
- 🤖 **Multi-Tool Support** - Works with Claude Code, Gemini CLI, and more (coming soon)

## Current Status

**v0.1.0** - Initial release supporting Claude Code. Multi-tool support coming soon.

## Install

**With pipx (recommended):**
```bash
pipx install ai-launcher
```

**From source:**
```bash
git clone https://github.com/solentlabs/ai-launcher.git
cd ai-launcher
pip install -e .
```

## Use

```bash
ai-launcher ~/projects
```

Select a project, and your AI tool opens with full context.

## Features

- 🔍 **Fuzzy search** - Type to filter projects instantly
- 📁 **Tree navigation** - See your project structure at a glance
- 📋 **Preview pane** - Git status, context files, directory contents
- ⚡ **Last opened** - Cursor starts on your most recent project
- ➕ **Manual projects** - Add non-git directories
- 🔗 **Symlink support** - Works with linked directories
- 🧠 **Context awareness** - Detects and displays CLAUDE.md and other context files

## Requirements

- Python 3.8+
- fzf (for fuzzy search)
- An AI CLI tool (Claude Code, Gemini CLI, etc.)

## Configuration

First run creates `~/.config/ai-launcher/config.toml`:

```toml
[scan]
paths = ["~/projects", "~/work"]
max_depth = 5

[ai-tools]
default = "claude-code"
# Multi-tool support coming soon
```

## Roadmap

- [x] Project discovery and selection
- [x] Claude Code integration
- [x] Local context file detection
- [ ] Gemini CLI support
- [ ] Universal context management (.ai-context/)
- [ ] Context file templates and scaffolding
- [ ] Cross-system sync (via git/rsync/dotfiles)
- [ ] Multi-tool selector UI

## Why Local-Only?

Your code and context should stay on your machine. AI Launcher:
- Never sends data to external services
- Works offline
- Respects your privacy
- Gives you full control

## Documentation

- [Installation Guide](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Windows Terminal Setup](docs/windows-terminal.md)
- [Troubleshooting](docs/troubleshooting.md)

## License

MIT - see [LICENSE](LICENSE)

---

**Made by [Solent Labs™](https://github.com/solentlabs)** - Building tools for developers who value privacy and local-first software.
