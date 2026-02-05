# Configuration

Configuration is stored in platform-specific locations:

- **Linux/WSL:** `~/.config/ai-launcher/config.toml`
- **macOS:** `~/Library/Application Support/ai-launcher/config.toml`
- **Windows:** `%LOCALAPPDATA%\ai-launcher\config.toml`

## Default Configuration

```toml
[scan]
# Directories to scan for git repositories
paths = [
    "~/projects",
    "~/work",
]

# Maximum directory depth to scan
max_depth = 5

# Directories to skip during scanning
prune_dirs = [
    "node_modules",
    ".cache",
    "venv",
    "__pycache__",
    ".git",
]

[ui]
# Preview pane width (percentage)
preview_width = 70

# Show git status in preview
show_git_status = true

[history]
# Maximum access history entries to keep
max_entries = 50
```

## Scan Configuration

### paths

List of directories to scan for projects.

```toml
[scan]
paths = [
    "~/projects",
    "~/work",
    "/mnt/c/dev",  # WSL example
]
```

**Supports:**
- Tilde expansion (`~`)
- Environment variables (`$HOME`)
- Absolute paths
- Relative paths (from home directory)

### max_depth

Maximum directory depth to traverse when scanning.

```toml
[scan]
max_depth = 5  # Default: 5
```

Lower values = faster scanning, but might miss nested projects.

### prune_dirs

Directories to skip during scanning to improve performance.

```toml
[scan]
prune_dirs = [
    "node_modules",  # NPM packages
    ".cache",        # Cache directories
    "venv",          # Python virtual environments
    "__pycache__",   # Python cache
    ".git",          # Git internals
]
```

## UI Configuration

### preview_width

Preview pane width as a percentage (0-100).

```toml
[ui]
preview_width = 70  # 70% of screen, 30% for project list
```

### show_git_status

Show git status in the preview pane.

```toml
[ui]
show_git_status = true  # false to disable
```

## History Configuration

### max_entries

Maximum number of access history entries to keep.

```toml
[history]
max_entries = 50  # Default: 50
```

## Manual Projects

Manual projects are stored separately in SQLite:

- **Linux/WSL:** `~/.local/share/ai-launcher/projects.db`
- **macOS:** `~/Library/Application Support/ai-launcher/projects.db`
- **Windows:** `%LOCALAPPDATA%\ai-launcher\projects.db`

Managed via the UI:
- `+ Add path` - Add a project
- `- Remove path` - Remove a project
