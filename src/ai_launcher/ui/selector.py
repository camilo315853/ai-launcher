"""Project selector UI for claude-launcher."""

import os
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import List, Optional

from ai_launcher.core.config import ConfigManager
from ai_launcher.core.discovery import get_all_projects
from ai_launcher.core.models import Project
from ai_launcher.core.storage import Storage
from ai_launcher.ui.preview import build_tree_view


def clear_screen() -> None:
    """Clear the terminal screen using ANSI escape codes."""
    print("\033[H\033[2J", end="", flush=True)


def select_project(
    projects: List[Project],
    storage: Storage,
    show_git_status: bool = True,
    config_manager: Optional[ConfigManager] = None,
    scan_paths: Optional[List[Path]] = None,
) -> Optional[Project]:
    """Show interactive project selector with action support.

    Args:
        projects: List of projects to choose from (already sorted)
        storage: Storage instance for last opened tracking
        show_git_status: Whether to show git status in preview
        config_manager: Config manager for add/remove actions (optional)
        scan_paths: Original scan paths for rescan action (optional)

    Returns:
        Selected Project or None if cancelled
    """
    # Action loop - allows rescanning, adding, removing
    current_projects = projects
    while True:
        if not current_projects:
            print(
                "No projects found. Add scan paths with --setup or add manual paths with --add"
            )
            return None

        # Clear screen before launching fzf
        clear_screen()

        # Get default selection index
        # Note: Not currently used - could reorder choices to put default first
        # default_index = storage.get_default_selection_index(current_projects)

        # Determine base path for display
        # Use the actual scan path for header and tree display
        if scan_paths:
            if len(scan_paths) == 1:
                base_path = scan_paths[0]
            else:
                # Multiple scan paths - find common base
                common = os.path.commonpath([str(p) for p in scan_paths])
                base_path = Path(common)
        else:
            base_path = Path.cwd()

        # Build tree view of projects with the base path
        # Format: "absolute_path\t\ttree_display"
        choices, choice_to_project = build_tree_view(current_projects, base_path)

        # Add action menu items at the bottom
        choices.append("__ACTION__\t\t")
        choices.append("__ACTION__\t\t↻ Rescan")
        choices.append("__ACTION__\t\t+ Add path")
        choices.append("__ACTION__\t\t- Remove path")

        # Build header with project info
        project_count = len(current_projects)

        header = f"""╭─────────────────────────────────────────╮
│      Claude Code Launcher               │
╰─────────────────────────────────────────╯

{project_count} project{"s" if project_count != 1 else ""} in {base_path}

Type to filter, arrows to navigate.
"""

        # Build preview command using helper script
        helper_script = Path(__file__).parent / "_preview_helper.py"
        preview_cmd = f"{sys.executable} {helper_script} {{}}"

        # Run fzf directly via subprocess
        try:
            fzf_cmd = [
                "fzf",
                "--prompt=❯ ",
                "--height=100%",
                "--layout=reverse",  # Nav at top
                "--border=rounded",
                "--border-label= Projects | Solent Labs™ ",
                "--delimiter=\t\t",  # Use double-tab as delimiter
                "--with-nth=2..",  # Show only the tree display (field 2 onwards)
                "--preview-window=right:70%:wrap:border-left:nohidden",  # Preview 70%, list 30%
                f"--preview={preview_cmd}",
                f"--header={header}",
                "--header-first",  # Display header before prompt
                "--info=default",  # Show match count on separate line
                "--color=header:italic",
                "--ansi",  # Enable ANSI color codes
                "--exact",  # Use exact substring matching instead of fuzzy
            ]

            # Pass choices via stdin
            input_data = "\n".join(choices)

            # Run fzf with stdin, but let it use the terminal for UI
            # Do NOT capture stdout/stderr - fzf needs direct terminal access
            process = subprocess.Popen(  # nosec B603
                fzf_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
            )

            stdout, _ = process.communicate(input=input_data)
            result_code = process.returncode

            # Check if user cancelled (exit code 130 = Ctrl+C, 1 = no match/cancelled)
            if result_code in (1, 130):
                clear_screen()
                return None

            if result_code != 0:
                clear_screen()
                print(f"Error running fzf: exit code {result_code}")
                return None

            # Get selected line
            selected = stdout.strip()
            if not selected:
                return None

            # Handle action menu items
            if selected == "__ACTION__\t\t↻ Rescan":
                # Rescan - refresh project list
                clear_screen()
                if scan_paths and config_manager:
                    config = config_manager.load()
                    manual_projects = storage.get_manual_projects()
                    current_projects = get_all_projects(
                        scan_paths,
                        config.scan.max_depth,
                        config.scan.prune_dirs,
                        manual_projects,
                    )
                    continue  # Loop back to show updated list
                else:
                    # Can't rescan without scan_paths
                    continue

            elif selected == "__ACTION__\t\t+ Add path":
                # Add manual project
                clear_screen()
                from ai_launcher.ui.browser import browse_directory

                new_path = browse_directory()
                if new_path:
                    storage.add_manual_path(new_path)
                    clear_screen()
                    print(f"✓ Added: {new_path}\n")
                    # Refresh project list
                    if scan_paths and config_manager:
                        config = config_manager.load()
                        manual_projects = storage.get_manual_projects()
                        current_projects = get_all_projects(
                            scan_paths,
                            config.scan.max_depth,
                            config.scan.prune_dirs,
                            manual_projects,
                        )
                continue  # Loop back

            elif selected == "__ACTION__\t\t- Remove path":
                # Remove manual project
                clear_screen()
                from ai_launcher.ui.browser import remove_manual_path

                removed_path = storage.get_manual_paths()  # Get current paths
                if remove_manual_path(storage):
                    clear_screen()
                    # Show which path was removed by comparing before/after
                    after_paths = set(storage.get_manual_paths())
                    before_paths = set(removed_path)
                    removed = before_paths - after_paths
                    if removed:
                        print(f"✓ Removed: {removed.pop()}\n")
                    # Refresh project list
                    if scan_paths and config_manager:
                        config = config_manager.load()
                        manual_projects = storage.get_manual_projects()
                        current_projects = get_all_projects(
                            scan_paths,
                            config.scan.max_depth,
                            config.scan.prune_dirs,
                            manual_projects,
                        )
                continue  # Loop back

            # Handle empty line action item (just loop back)
            elif selected == "__ACTION__\t\t":
                continue

            # Regular project selection
            if not selected:
                return None

            # Look up the project from the formatted line
            project = choice_to_project.get(selected)
            if project:
                # Clear screen before launching Claude
                clear_screen()
                return project

            # Fallback: try to match by index
            try:
                selected_index = choices.index(selected)
                # Clear screen before launching Claude
                clear_screen()
                return current_projects[selected_index]
            except ValueError:
                clear_screen()
                print(f"Warning: Could not find selected project: {selected}")
                return None

        except FileNotFoundError:
            print("Error: fzf not found. Please install fzf:")
            print("  Ubuntu/Debian: sudo apt install fzf")
            print("  macOS: brew install fzf")
            return None
        except Exception as e:
            print(f"Error in project selector: {e}")
            import traceback

            traceback.print_exc()
            return None


def show_project_list(projects: List[Project]) -> None:
    """Show a simple list of all projects.

    Args:
        projects: List of projects to display
    """
    if not projects:
        print("No projects found.")
        return

    print(f"\nFound {len(projects)} project(s):\n")

    for project in projects:
        markers = []
        if project.is_git_repo:
            markers.append("git")
        if project.is_manual:
            markers.append("manual")

        marker_str = f" [{','.join(markers)}]" if markers else ""
        print(f"  {project.path}{marker_str}")

    print()
