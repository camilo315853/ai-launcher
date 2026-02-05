# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-02-05

### Fixed
- Preview pane no longer shows errors when hovering over action menu items (Rescan, Add path, Remove path)

### Changed
- README simplified and focused on core developer workflow
- Moved detailed documentation to `docs/` directory
  - Installation guide
  - Configuration reference
  - Windows Terminal integration
  - Troubleshooting guide

## [0.1.0] - 2026-02-04

### Added
- Interactive project selector with tree-structured navigation
- fzf-powered fuzzy search interface
- Automatic git repository discovery with configurable scan paths
- Manual project management (add/remove paths)
- Rich preview pane showing:
  - CLAUDE.md contents (first 20 lines)
  - Git status
  - Directory listing
- Tree view with hierarchical folder structure
- Smart default cursor positioning (last opened project)
- Symlink support for manual paths
- Exact substring matching for project filtering
- Action menu (Rescan, Add path, Remove path)
- Cross-platform support (Linux, macOS, Windows/WSL)
- Automated PyPI publishing via GitHub Actions
- Pre-commit hooks for code quality

### Technical Details
- Python 3.8+ compatibility
- SQLite storage for manual paths and history
- Platform-specific config and data directories
- Robust error recovery (database corruption, missing paths)
- TOML-based configuration

[0.1.0]: https://github.com/solentlabs/ai-launcher/releases/tag/v0.1.0
