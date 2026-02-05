"""CLI interface for claude-launcher."""

import os
import subprocess  # nosec B404
import sys
from pathlib import Path
from typing import Optional

import typer

from ai_launcher import __version__
from ai_launcher.core.config import ConfigManager, get_database_path
from ai_launcher.core.discovery import get_all_projects
from ai_launcher.core.storage import Storage
from ai_launcher.ui.browser import browse_directory, remove_manual_path
from ai_launcher.ui.selector import select_project, show_project_list
from ai_launcher.utils.git import interactive_clone
from ai_launcher.utils.logging import setup_logging

app = typer.Typer(
    help="Fast context switching for Claude Code projects",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"claude-launcher {__version__}")
        raise typer.Exit()


@app.command()
def main(
    path: Optional[Path] = typer.Argument(
        None,
        help="Directory to scan for projects (optional)",
        exists=True,
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose logging"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
    setup: bool = typer.Option(False, "--setup", help="Run first-time setup"),
    add: bool = typer.Option(False, "--add", help="Add a manual project path"),
    remove: bool = typer.Option(False, "--remove", help="Remove a manual path"),
    list_projects: bool = typer.Option(False, "--list", help="List all projects"),
    recent: bool = typer.Option(False, "--recent", help="Jump to last opened project"),
    clone: bool = typer.Option(False, "--clone", help="Clone a git repository"),
) -> None:
    """Launch Claude Code with interactive project selection.

    Examples:
        claude-launcher                    # Use configured paths
        claude-launcher ~/projects         # Scan specific directory
        claude-launcher /home/user/work    # Scan absolute path
    """

    # Setup logging
    logger = setup_logging(verbose=verbose or debug)
    logger.debug("Claude Launcher starting")
    logger.debug(f"Version: {__version__}")

    # Initialize config and storage
    config_manager = ConfigManager()
    storage = Storage(get_database_path())

    logger.debug(f"Config path: {config_manager.config_path}")
    logger.debug(f"Database path: {storage.db_path}")

    # Handle --setup
    if setup:
        config = config_manager.run_first_time_setup()
        sys.exit(0)

    # Load config
    config = config_manager.load()

    # Determine scan paths: CLI argument takes precedence over config
    if path:
        scan_paths = [path.resolve()]
    elif config.scan.paths:
        scan_paths = config.scan.paths
    else:
        print("Error: No directory specified.")
        print("")
        print("Usage:")
        print("  claude-launcher ~/projects        # Scan a specific directory")
        print("  claude-launcher --setup           # Run setup wizard")
        print("  claude-launcher --help            # Show all options")
        sys.exit(1)

    # Handle --add
    if add:
        print("Select a directory to add as a manual project path...")
        selected_path = browse_directory()
        if selected_path:
            storage.add_manual_path(selected_path)
            print(f"Added: {selected_path}")
        sys.exit(0)

    # Handle --remove
    if remove:
        remove_manual_path(storage)
        sys.exit(0)

    # Handle --clone
    if clone:
        cloned_path = interactive_clone(storage)
        if cloned_path:
            print(f"Launching Claude in: {cloned_path}")
            launch_claude(cloned_path, storage)
        sys.exit(0)

    # Get all projects
    manual_projects = storage.get_manual_projects()
    all_projects = get_all_projects(
        scan_paths,
        config.scan.max_depth,
        config.scan.prune_dirs,
        manual_projects,
    )

    # Handle --list
    if list_projects:
        show_project_list(all_projects)
        sys.exit(0)

    # Handle --recent
    if recent:
        last_opened = storage.get_last_opened()
        if not last_opened:
            print("No recent project found.")
            sys.exit(1)

        project_path = Path(last_opened)
        if not project_path.exists():
            print(f"Last opened project not found: {project_path}")
            sys.exit(1)

        print(f"Launching Claude in: {project_path}")
        launch_claude(project_path, storage)
        sys.exit(0)

    # Interactive selection
    selected_project = select_project(
        all_projects, storage, config.ui.show_git_status, config_manager, scan_paths
    )

    if selected_project is None:
        print("Claude Launcher: No project selected")
        sys.exit(0)

    # Launch Claude
    print(f"Launching Claude in: {selected_project.path}")
    launch_claude(selected_project.path, storage)


def launch_claude(project_path: Path, storage: Storage) -> None:
    """Launch Claude Code in the specified project directory.

    Args:
        project_path: Path to the project
        storage: Storage instance for tracking
    """
    # Verify directory exists
    if not project_path.exists():
        print(f"Error: Directory not found: {project_path}")
        sys.exit(1)

    # Record as last opened
    storage.set_last_opened(project_path)

    # Change to project directory
    os.chdir(project_path)

    # Launch Claude
    try:
        subprocess.run(["claude"], check=True)  # nosec B603, B607
    except FileNotFoundError:
        print("Error: 'claude' command not found.")
        print("Make sure Claude Code CLI is installed.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error launching Claude: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)


if __name__ == "__main__":
    app()
