"""Git utilities for claude-launcher."""

import subprocess  # nosec B404
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ai_launcher.core.storage import Storage


def clone_repository(
    url: str,
    target_base: Path,
    subfolder: Optional[str] = None,
) -> Path:
    """Clone a git repository.

    Args:
        url: Git repository URL (https or ssh)
        target_base: Base directory for cloning
        subfolder: Optional subfolder within target_base

    Returns:
        Path to cloned repository

    Raises:
        ValueError: If URL is invalid or target exists
        RuntimeError: If git clone fails
    """
    # Validate URL format
    if not (url.startswith("https://") or url.startswith("git@")):
        raise ValueError(
            f"Invalid git URL: {url}\nMust start with 'https://' or 'git@'"
        )

    # Extract repository name from URL
    repo_name = url.rstrip("/").split("/")[-1].replace(".git", "")

    # Construct target path
    if subfolder:
        target_path = target_base / subfolder / repo_name
    else:
        target_path = target_base / repo_name

    # Check if target already exists
    if target_path.exists():
        raise ValueError(f"Directory already exists: {target_path}")

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Clone repository
    try:
        print(f"Cloning {url}...")
        print(f"Target: {target_path}\n")

        subprocess.run(  # nosec B603, B607
            ["git", "clone", url, str(target_path)],
            capture_output=True,
            text=True,
            check=True,
        )

        print("Clone successful!")
        return target_path

    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Git clone failed: {error_msg}")
    except FileNotFoundError:
        raise RuntimeError("Git command not found. Please install git.")


def interactive_clone(storage: "Storage") -> Optional[Path]:
    """Interactive git clone workflow.

    Args:
        storage: Storage instance for adding manual paths

    Returns:
        Path to cloned repository or None if cancelled
    """

    # Get git URL
    print("\n=== Clone Git Repository ===\n")
    url = input("Git repository URL (https:// or git@): ").strip()

    if not url:
        print("Cancelled.")
        return None

    # Validate URL
    if not (url.startswith("https://") or url.startswith("git@")):
        print("Error: Invalid URL. Must start with 'https://' or 'git@'")
        return None

    # Get target folder
    print("\nSelect target folder:")
    print("  1. Home directory (~)")
    print("  2. ~/projects")
    print("  3. ~/work")
    print("  4. Custom path")

    choice = input("\nChoice (1-4): ").strip()

    if choice == "1":
        target_base = Path.home()
        subfolder = None
    elif choice == "2":
        target_base = Path.home()
        subfolder = "projects"
    elif choice == "3":
        target_base = Path.home()
        subfolder = "work"
    elif choice == "4":
        custom = input("Enter custom path: ").strip()
        if not custom:
            print("Cancelled.")
            return None
        target_base = Path(custom).expanduser().resolve()
        subfolder = None
    else:
        print("Invalid choice.")
        return None

    # Clone
    try:
        cloned_path = clone_repository(url, target_base, subfolder)

        # Ask if they want to add as manual path
        print(f"\nCloned to: {cloned_path}")
        add_manual = input("Add to manual paths? (y/n): ").strip().lower()

        if add_manual == "y":
            storage.add_manual_path(cloned_path)
            print("Added to manual paths.")

        # Ask if they want to launch Claude
        launch = input("Launch Claude now? (y/n): ").strip().lower()

        if launch == "y":
            return cloned_path

        return None

    except (ValueError, RuntimeError) as e:
        print(f"\nError: {e}")
        return None
