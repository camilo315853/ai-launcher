#!/usr/bin/env python3
"""Preview helper script for fzf."""

import sys
from pathlib import Path

from ai_launcher.ui.preview import generate_preview


def main() -> None:
    """Generate preview from fzf selection line."""
    if len(sys.argv) < 2:
        print("No selection provided")
        return

    line = sys.argv[1]

    # Extract path from formatted line
    # Format is: "absolute_path\t\ttree_display" or special markers
    # Special markers: __SPACE__ (spacing line), __ACTION__ (action menu items)
    parts = line.split("\t\t", 1)

    if len(parts) == 2 and parts[0] not in ("__SPACE__", "__ACTION__"):
        # Normal line - first field is absolute path (project or directory)
        path_str = parts[0]
    else:
        # Spacing line, action menu, or malformed - show nothing
        return

    try:
        path = Path(path_str).expanduser().resolve()

        # Show full path at top with divider
        print(f"{path}")
        print("━" * 80)
        print()

        # Check if it's a directory (folder header) or project
        if path.is_dir() and not (path / ".git").exists():
            # Directory header - show directory contents
            print("Contents:")
            print("─" * 40)
            try:
                # Separate directories and files
                dirs = []
                files = []
                for item in path.iterdir():
                    if item.is_dir():
                        dirs.append(f"📁 {item.name}/")
                    else:
                        files.append(f"📄 {item.name}")

                # Sort each group and combine (folders first)
                items = sorted(dirs) + sorted(files)

                # Show all items (no limit)
                if items:
                    print("\n".join(items))
                else:
                    print("(empty directory)")
            except PermissionError:
                print("(permission denied)")
        else:
            # Project directory - show full preview
            preview = generate_preview(path, show_git_status=True)
            print(preview.format())
    except Exception as e:
        print(f"Error generating preview: {e}")


if __name__ == "__main__":
    main()
