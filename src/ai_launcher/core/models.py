"""Data models for claude-launcher."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Project:
    """Represents a project that can be launched with Claude."""

    path: Path
    name: str
    parent_path: Path
    is_git_repo: bool
    is_manual: bool

    @classmethod
    def from_path(cls, path: Path, is_manual: bool = False) -> "Project":
        """Create a Project from a filesystem path.

        Args:
            path: Path to the project directory
            is_manual: Whether this was manually added (vs auto-discovered)

        Returns:
            Project instance
        """
        # For manual projects, don't resolve symlinks so they appear under their symlink location
        # For discovered projects, resolve to avoid duplicates
        if is_manual:
            resolved_path = path
        else:
            resolved_path = path.resolve()

        is_git = (resolved_path / ".git").exists()
        return cls(
            path=resolved_path,
            name=resolved_path.name,
            parent_path=resolved_path.parent,
            is_git_repo=is_git,
            is_manual=is_manual,
        )

    def __str__(self) -> str:
        """String representation showing path."""
        return str(self.path)


@dataclass
class ScanConfig:
    """Configuration for project scanning."""

    paths: List[Path] = field(default_factory=list)
    max_depth: int = 5
    prune_dirs: List[str] = field(
        default_factory=lambda: [
            "node_modules",
            ".cache",
            "venv",
            "__pycache__",
            ".git",
            ".venv",
            "env",
            "ENV",
        ]
    )


@dataclass
class UIConfig:
    """Configuration for user interface."""

    preview_width: int = 70
    show_git_status: bool = True


@dataclass
class HistoryConfig:
    """Configuration for history tracking."""

    max_entries: int = 50


@dataclass
class ConfigData:
    """Complete configuration for claude-launcher."""

    scan: ScanConfig = field(default_factory=ScanConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    history: HistoryConfig = field(default_factory=HistoryConfig)


@dataclass
class PreviewContent:
    """Content to display in the project preview pane."""

    claude_md: Optional[str] = None
    git_status: Optional[str] = None
    directory_listing: Optional[str] = None
    error: Optional[str] = None

    def format(self) -> str:
        """Format preview content for display.

        Returns:
            Formatted string for fzf preview pane
        """
        lines = []

        if self.error:
            lines.append(f"ERROR: {self.error}")
            return "\n".join(lines)

        if self.claude_md:
            lines.append("=== CLAUDE.md ===")
            lines.append(self.claude_md)
            lines.append("")

        if self.git_status:
            lines.append("=== Git Status ===")
            lines.append(self.git_status)
            lines.append("")

        if self.directory_listing:
            lines.append("=== Directory ===")
            lines.append(self.directory_listing)

        return "\n".join(lines) if lines else "No preview available"
