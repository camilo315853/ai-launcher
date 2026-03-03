# Terminal Window Title

AI Launcher can automatically set your terminal window title to show which project and AI provider you're working with. This makes it easy to identify different terminal windows when you have multiple projects open.

## Configuration

The terminal title feature is enabled by default. To customize it, edit `~/.config/ai-launcher/config.toml`:

```toml
[ui]
# Enable or disable terminal title setting
set_terminal_title = true

# Customize the title format
terminal_title_format = "{project} → {provider}"
```

## Format Variables

You can customize the terminal title using these variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `{project}` | Project folder name | `my-app` |
| `{provider}` | Provider display name | `Claude Code` |
| `{path}` | Full project path | `/home/user/projects/my-app` |
| `{parent}` | Parent directory name | `projects` |

## Format Examples

### Simple project name
```toml
terminal_title_format = "{project}"
```
**Result:** `my-app`

### Project with provider (default)
```toml
terminal_title_format = "{project} → {provider}"
```
**Result:** `my-app → Claude Code`

### With emoji
```toml
terminal_title_format = "🤖 {project} | {provider}"
```
**Result:** `🤖 my-app | Claude Code`

### With parent directory context
```toml
terminal_title_format = "{parent}/{project} - {provider}"
```
**Result:** `projects/my-app - Claude Code`

### Full path
```toml
terminal_title_format = "{path}"
```
**Result:** `/home/user/projects/my-app`

### Provider first
```toml
terminal_title_format = "{provider}: {project}"
```
**Result:** `Claude Code: my-app`

## Supported Terminals

The terminal title feature works on most modern terminal emulators:

- ✅ **xterm** and xterm-256color
- ✅ **GNOME Terminal** (and other VTE-based terminals)
- ✅ **iTerm2** (macOS)
- ✅ **Terminal.app** (macOS)
- ✅ **Alacritty**
- ✅ **Kitty**
- ✅ **Windows Terminal**
- ✅ **tmux**
- ✅ **screen**
- ✅ **VS Code integrated terminal**
- ✅ **Konsole** (KDE)
- ✅ **Tilix**
- ✅ **Hyper**
- ❌ **Basic CMD.exe** (Windows) - not supported

## Disabling Terminal Title

If you don't want AI Launcher to change your terminal title, you can disable it:

```toml
[ui]
set_terminal_title = false
```

## How It Works

AI Launcher uses ANSI escape sequences to set the terminal title. The sequence `\033]0;{title}\007` is recognized by most modern terminal emulators.

### Special Handling for tmux

When running inside tmux, AI Launcher uses tmux-specific escape sequences (`\033k{title}\033\\`) to ensure the title is set correctly.

### Terminal Detection

The feature automatically detects whether your terminal supports title setting by checking:
- Whether stdout is a TTY
- The `TERM` environment variable
- The `TERM_PROGRAM` environment variable (for iTerm, VS Code)
- The `WT_SESSION` environment variable (for Windows Terminal)
- The `TMUX` environment variable (for tmux)

If your terminal doesn't support title setting, the feature will silently do nothing (no errors).

## Troubleshooting

### Terminal title not changing?

1. **Check if your terminal supports title setting:**
   Most modern terminals do, but some minimal terminals don't.

2. **Verify the feature is enabled:**
   Check your config file at `~/.config/ai-launcher/config.toml`:
   ```toml
   [ui]
   set_terminal_title = true
   ```

3. **Try setting TERM environment variable:**
   ```bash
   export TERM=xterm-256color
   ai-launcher ~/projects
   ```

4. **Check if you're using a supported terminal:**
   See the "Supported Terminals" section above.

### Terminal title shows wrong text?

1. **Check your format string:**
   Edit `~/.config/ai-launcher/config.toml` and verify `terminal_title_format` is correct.

2. **Make sure variable names are correct:**
   Valid variables are: `{project}`, `{provider}`, `{path}`, `{parent}`

3. **Test with the default format:**
   ```toml
   terminal_title_format = "{project} → {provider}"
   ```

### Terminal title persists after closing AI tool?

This is normal behavior. Most terminal emulators keep the last set title until:
- The terminal window is closed
- Another program sets a new title
- You manually clear the title

To manually clear the title:
```bash
echo -ne "\033]0;\007"
```

Or set it to something else:
```bash
echo -ne "\033]0;Terminal\007"
```

## Privacy Note

The terminal title is only set locally in your terminal window. It's not sent to any external services and is purely for your visual convenience when managing multiple terminal windows.

## Examples in Practice

### Multiple Projects
When working on several projects simultaneously:

**Window 1:** `ai-launcher → Claude Code`
**Window 2:** `backend-api → Claude Code`
**Window 3:** `frontend-ui → Gemini`

You can instantly identify which window has which project!

### Organization Context
Using the parent directory to show organization:

```toml
terminal_title_format = "{parent}/{project}"
```

**Result:** `solentlabs/ai-launcher`, `personal/blog`, `work/dashboard`

### Focused Workflow
Minimal format for distraction-free work:

```toml
terminal_title_format = "{project}"
```

Clean and simple, just the project name.

---

**See also:**
- [Configuration Guide](configuration.md)
- [Installation Guide](installation.md)
- [Troubleshooting](troubleshooting.md)
