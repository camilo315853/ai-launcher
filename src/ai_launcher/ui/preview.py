"""Preview generation for claude-launcher."""

import subprocess  # nosec B404
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ai_launcher.core.models import PreviewContent, Project


def generate_preview(
    project_path: Path, show_git_status: bool = True
) -> PreviewContent:
    """Generate preview content for a project.

    Args:
        project_path: Path to the project
        show_git_status: Whether to include git status

    Returns:
        PreviewContent instance with available information
    """
    preview = PreviewContent()

    # Try to read CLAUDE.md
    claude_md_path = project_path / "CLAUDE.md"
    if claude_md_path.exists():
        try:
            with open(claude_md_path, "r", encoding="utf-8") as f:
                lines = f.readlines()[:20]  # First 20 lines
                preview.claude_md = "".join(lines).rstrip()
        except Exception as e:
            preview.error = f"Error reading CLAUDE.md: {e}"

    # Try to get git status
    if show_git_status and (project_path / ".git").exists():
        try:
            result = subprocess.run(  # nosec B603, B607
                ["git", "status", "-s"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0:
                status = result.stdout.strip()
                if status:
                    preview.git_status = status
                else:
                    preview.git_status = "Clean working tree"
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            # Git not available or error - graceful degradation
            pass

    # Directory listing as fallback
    try:
        # Separate directories and files
        dirs = []
        files = []
        for item in project_path.iterdir():
            if item.is_dir():
                dirs.append(f"📁 {item.name}/")
            else:
                files.append(f"📄 {item.name}")

        # Sort each group and combine (folders first, then files)
        items = sorted(dirs) + sorted(files)

        # Show all items (no limit)
        if items:
            preview.directory_listing = "\n".join(items)
    except Exception as e:
        if not preview.error:
            preview.error = f"Error reading directory: {e}"

    return preview


def format_project_line(
    project_path: Path,
    parent_path: Optional[Path] = None,
    is_git: bool = False,
    is_manual: bool = False,
) -> str:
    """Format a project for display in the list.

    Args:
        project_path: Path to the project
        parent_path: Parent directory path (for relative display)
        is_git: Whether this is a git repository
        is_manual: Whether this was manually added

    Returns:
        Formatted string for display
    """
    markers = []
    if is_git:
        markers.append("git")
    if is_manual:
        markers.append("manual")

    marker_str = f"[{','.join(markers)}]" if markers else ""

    # Show relative to parent if available
    if parent_path:
        try:
            rel_path = project_path.relative_to(parent_path)
            display_path = f"{parent_path.name}/{rel_path}"
        except ValueError:
            display_path = str(project_path)
    else:
        display_path = str(project_path)

    if marker_str:
        return f"{display_path} {marker_str}"
    return display_path


def build_tree_view(
    projects: List[Project], base_path: Optional[Path] = None
) -> Tuple[List[str], Dict[str, Project]]:
    """Build a hierarchical tree view showing full folder structure.

    Format: Each line contains "absolute_path\t\ttree_display"
    fzf will be configured to only show tree_display but pass the whole line.

    Args:
        projects: List of projects to display
        base_path: Base path to use for relative display (optional)

    Returns:
        Tuple of (formatted_lines, line_to_project_mapping)
    """
    if not projects:
        return [], {}

    # Use provided base_path or calculate from projects
    if base_path:
        base = base_path
    else:
        # Find common base path
        if len(projects) == 1:
            base = projects[0].path.parent
        else:
            # Find common ancestor
            all_parts = [p.path.parts for p in projects]
            common_parts = []
            for parts in zip(*all_parts):
                if len(set(parts)) == 1:
                    common_parts.append(parts[0])
                else:
                    break

            # If we only have root as common, use the parent of the first project as base
            # This avoids showing the entire filesystem
            if not common_parts or (len(common_parts) == 1 and common_parts[0] == "/"):
                # No meaningful common path - use first project's parent
                base = projects[0].path.parent
            else:
                base = Path(*common_parts)

    # Build full directory tree structure
    # Track all directories and their children (both dirs and projects)
    dir_children: Dict[Path, List[Path]] = {}  # dir -> child dirs
    dir_projects: Dict[Path, List[Project]] = {}  # dir -> projects in that dir

    # Collect all directories in the hierarchy
    all_dirs = set()
    for project in projects:
        # Add project to its parent directory
        parent = project.path.parent
        if parent not in dir_projects:
            dir_projects[parent] = []
        dir_projects[parent].append(project)

        # Add all ancestor directories
        current = project.path.parent
        while current != base and current != current.parent:
            all_dirs.add(current)
            parent_dir = current.parent
            if parent_dir != current and parent_dir != base.parent:
                if parent_dir not in dir_children:
                    dir_children[parent_dir] = []
                if current not in dir_children[parent_dir]:
                    dir_children[parent_dir].append(current)
            current = parent_dir

    # Sort children for consistent display
    for parent in dir_children:
        dir_children[parent].sort()

    formatted_lines = []
    line_to_project = {}

    def add_directory(
        dir_path: Path, prefix: str = "", is_last: bool = True, depth: int = 0
    ) -> None:
        """Recursively add directory tree."""
        # Show directory header if not the base
        if dir_path != base:
            connector = "└── " if is_last else "├── "
            # Get relative path from base for folder display
            try:
                rel_dir = dir_path.relative_to(base)
                dir_name = str(rel_dir)
            except ValueError:
                # Can't make relative - show full path
                dir_name = str(dir_path)

            dir_display = f"\033[2m{prefix}{connector}📁 {dir_name}/\033[0m"
            formatted_lines.append(f"{dir_path}\t\t{dir_display}")

            # Update prefix for children
            if is_last:
                child_prefix = prefix + "    "
            else:
                child_prefix = prefix + "│   "
        else:
            # Base directory - only show if it's meaningful (not root)
            if base != Path("/"):
                dir_display = f"\033[2m📁 {base}/\033[0m"
                formatted_lines.append(f"{base}\t\t{dir_display}")
            child_prefix = ""

        # Get subdirectories and projects
        subdirs = dir_children.get(dir_path, [])
        projects_here = dir_projects.get(dir_path, [])

        # Sort projects
        projects_here = sorted(projects_here, key=lambda p: p.path.name)

        # Calculate total items (subdirs + projects)
        total_items = len(subdirs) + len(projects_here)
        item_idx = 0

        # Add subdirectories first
        for subdir in subdirs:
            item_idx += 1
            is_last_item = item_idx == total_items
            add_directory(subdir, child_prefix, is_last_item, depth + 1)

        # Add projects
        for project in projects_here:
            item_idx += 1
            is_last_item = item_idx == total_items

            connector = "└── " if is_last_item else "├── "

            # Format markers
            markers = []
            if project.is_git_repo:
                markers.append("git")
            if project.is_manual:
                markers.append("manual")
            marker_str = f" [{','.join(markers)}]" if markers else ""

            # Just show project name, not full path
            tree_display = f"{child_prefix}{connector}{project.path.name}{marker_str}"
            full_line = f"{project.path}\t\t{tree_display}"
            formatted_lines.append(full_line)
            line_to_project[full_line] = project

    # Start with base directory
    add_directory(base, "", True, 0)

    return formatted_lines, line_to_project
