"""
Richtato CLI - Interactive development and deployment tool

Usage:
    richtato              # Interactive menu
    richtato build        # Build Docker image
    richtato publish      # Build & push to Docker Hub
    richtato dev          # Start dev environment
    richtato logs         # View container logs
    richtato shell        # Open container shell
    richtato migrate      # Run Django migrations
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from simple_term_menu import TerminalMenu


# ANSI colors
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    END = "\033[0m"


# Menu styling
MENU_STYLE = {
    "menu_cursor": "❯ ",
    "menu_cursor_style": ("fg_cyan", "bold"),
    "menu_highlight_style": ("fg_cyan", "bold"),
    "shortcut_key_highlight_style": ("fg_yellow",),
    "shortcut_brackets_highlight_style": ("fg_gray",),
}


def print_banner():
    """Print the Richtato banner."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
  ╔═══════════════════════════════════════════════════════════════════╗
  ║                                                                   ║
  ║   ██████╗ ██╗ ██████╗██╗  ██╗████████╗ █████╗ ████████╗ ██████╗   ║
  ║   ██╔══██╗██║██╔════╝██║  ██║╚══██╔══╝██╔══██╗╚══██╔══╝██╔═══██╗  ║
  ║   ██████╔╝██║██║     ███████║   ██║   ███████║   ██║   ██║   ██║  ║
  ║   ██╔══██╗██║██║     ██╔══██║   ██║   ██╔══██║   ██║   ██║   ██║  ║
  ║   ██║  ██║██║╚██████╗██║  ██║   ██║   ██║  ██║   ██║   ╚██████╔╝  ║
  ║   ╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝   ╚═╝    ╚═════╝   ║
  ║                                                                   ║
  ╚═══════════════════════════════════════════════════════════════════╝
{Colors.END}"""
    print(banner)


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}▸ {text}{Colors.END}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.DIM}  {text}{Colors.END}")


def select(title: str, options: list[str], default: int = 0) -> Optional[int]:
    """Show an interactive menu and return the selected index."""
    print(f"{Colors.DIM}{title}{Colors.END}")
    menu = TerminalMenu(
        options,
        cursor_index=default,
        **MENU_STYLE,
    )
    return menu.show()


def prompt(text: str, default: Optional[str] = None) -> str:
    """Prompt user for input with optional default."""
    if default:
        display = f"{Colors.YELLOW}{text} [{Colors.BOLD}{default}{Colors.END}{Colors.YELLOW}]: {Colors.END}"
    else:
        display = f"{Colors.YELLOW}{text}: {Colors.END}"

    response = input(display).strip()
    return response if response else (default or "")


def confirm(text: str, default: bool = True) -> bool:
    """Interactive yes/no confirmation with arrow keys."""
    options = ["Yes", "No"] if default else ["No", "Yes"]
    default_idx = 0

    print(f"{Colors.YELLOW}{text}{Colors.END}")
    menu = TerminalMenu(
        options,
        cursor_index=default_idx,
        **MENU_STYLE,
    )
    idx = menu.show()

    if idx is None:
        return False

    selected = options[idx]
    return selected == "Yes"


def run_cmd(cmd: list[str], cwd: Optional[str] = None) -> int:
    """Run a command and return exit code."""
    print(f"{Colors.DIM}$ {' '.join(cmd)}{Colors.END}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def get_project_root() -> str:
    """
    Get the project root directory.

    Priority:
    1. RICHTATO_ROOT environment variable
    2. Walk up from current directory looking for docker-compose.yml
    3. Fall back to current directory
    """
    if env_root := os.environ.get("RICHTATO_ROOT"):
        return env_root

    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "docker-compose.yml").exists() and (parent / "backend").is_dir():
            return str(parent)

    return str(current)


# ============================================================
# Commands
# ============================================================


def cmd_build():
    """Build Docker image locally."""
    print_header("Build Docker Image")

    tag = prompt("Image tag", "richtato:latest")
    api_base = prompt("VITE_API_BASE_URL", "/api")

    print()
    print_info(f"Image: {tag}")
    print_info(f"API Base URL: {api_base}")
    print()

    if not confirm("Proceed with build?"):
        print_info("Cancelled.")
        return

    print()
    root = get_project_root()

    cmd = [
        "docker",
        "build",
        "-f",
        "Dockerfile",
        "--build-arg",
        f"VITE_API_BASE_URL={api_base}",
        "-t",
        tag,
        ".",
    ]

    result = run_cmd(cmd, cwd=root)

    if result == 0:
        print()
        print_success(f"Built image: {tag}")
    else:
        print_error("Build failed!")
        sys.exit(1)


def cmd_publish():
    """Build and push Docker image to Docker Hub."""
    print_header("Publish to Docker Hub")

    tag = prompt("Tag", "latest")
    api_base = prompt("VITE_API_BASE_URL", "/api")

    print()
    platforms_options = [
        "linux/amd64,linux/arm64  (multi-arch)",
        "linux/amd64              (x86 only)",
        "linux/arm64              (ARM only)",
    ]
    platforms_values = [
        "linux/amd64,linux/arm64",
        "linux/amd64",
        "linux/arm64",
    ]

    idx = select("Select platform:", platforms_options, default=0)
    if idx is None:
        print_info("Cancelled.")
        return
    platforms = platforms_values[idx]

    print()
    push = confirm("Push to Docker Hub?")

    image = f"bropotato/richtato:{tag}"

    print()
    print_info(f"Image: {image}")
    print_info(f"Platforms: {platforms}")
    print_info(f"API Base URL: {api_base}")
    print_info(f"Push: {'Yes' if push else 'No (local only)'}")
    print()

    if not confirm("Proceed?"):
        print_info("Cancelled.")
        return

    print()
    root = get_project_root()

    cmd = [
        "docker",
        "buildx",
        "build",
        "-f",
        "Dockerfile",
        "--build-arg",
        f"VITE_API_BASE_URL={api_base}",
        "--platform",
        platforms,
        "-t",
        image,
    ]

    if push:
        cmd.append("--push")
    else:
        cmd.append("--load")

    cmd.append(".")

    result = run_cmd(cmd, cwd=root)

    if result == 0:
        print()
        if push:
            print_success(f"Published: {image}")
        else:
            print_success(f"Built locally: {image}")
    else:
        print_error("Build failed!")
        sys.exit(1)


def cmd_dev():
    """Start development environment."""
    print_header("Development Environment")

    options = [
        "Start containers         (docker compose up -d)",
        "Start with rebuild       (docker compose up --build -d)",
        "Stop containers          (docker compose down)",
        "Restart containers       (docker compose restart)",
        "View status              (docker compose ps)",
    ]

    idx = select("Select action:", options, default=0)
    if idx is None:
        print_info("Cancelled.")
        return

    root = get_project_root()

    commands = [
        ["docker", "compose", "up", "-d"],
        ["docker", "compose", "up", "--build", "-d"],
        ["docker", "compose", "down"],
        ["docker", "compose", "restart"],
        ["docker", "compose", "ps"],
    ]

    cmd = commands[idx]

    print()
    result = run_cmd(cmd, cwd=root)

    if result == 0:
        print()
        print_success("Done!")
    else:
        print_error("Command failed!")
        sys.exit(1)


def cmd_logs():
    """View container logs."""
    print_header("Container Logs")

    options = ["backend", "frontend", "db", "all services"]

    idx = select("Select service:", options, default=0)
    if idx is None:
        print_info("Cancelled.")
        return

    services = [["backend"], ["frontend"], ["db"], []]
    service = services[idx]

    print()
    follow = confirm("Follow logs?")

    root = get_project_root()
    cmd = ["docker", "compose", "logs"]

    if follow:
        cmd.append("-f")

    cmd.extend(service)

    print()
    print_info("Press Ctrl+C to stop")
    print()

    try:
        run_cmd(cmd, cwd=root)
    except KeyboardInterrupt:
        print()
        print_info("Stopped.")


def cmd_shell():
    """Open shell in container."""
    print_header("Container Shell")

    options = [
        "backend   → Django shell",
        "backend   → bash",
        "frontend  → sh",
        "db        → psql",
    ]

    idx = select("Select shell:", options, default=0)
    if idx is None:
        print_info("Cancelled.")
        return

    root = get_project_root()

    commands = [
        ["docker", "compose", "exec", "backend", "python", "manage.py", "shell"],
        ["docker", "compose", "exec", "backend", "bash"],
        ["docker", "compose", "exec", "frontend", "sh"],
        ["docker", "compose", "exec", "db", "psql", "-U", "richtato"],
    ]

    cmd = commands[idx]

    print()
    os.chdir(root)
    os.execvp(cmd[0], cmd)


def cmd_migrate():
    """Run Django migrations."""
    print_header("Django Migrations")

    options = [
        "Run migrations       (migrate)",
        "Make migrations      (makemigrations)",
        "Show status          (showmigrations)",
    ]

    idx = select("Select action:", options, default=0)
    if idx is None:
        print_info("Cancelled.")
        return

    root = get_project_root()

    commands = [
        ["docker", "compose", "exec", "backend", "python", "manage.py", "migrate"],
        [
            "docker",
            "compose",
            "exec",
            "backend",
            "python",
            "manage.py",
            "makemigrations",
        ],
        [
            "docker",
            "compose",
            "exec",
            "backend",
            "python",
            "manage.py",
            "showmigrations",
        ],
    ]

    cmd = commands[idx]

    print()
    result = run_cmd(cmd, cwd=root)

    if result == 0:
        print()
        print_success("Done!")


def show_menu():
    """Show the main interactive menu."""
    print_banner()

    print(f"{Colors.BOLD}What would you like to do?{Colors.END}")
    print(f"{Colors.DIM}Use ↑↓ arrows to navigate, Enter to select{Colors.END}\n")

    options = [
        "[dev]      Start/stop dev containers",
        "[logs]     View container logs",
        "[shell]    Open container shell",
        "[migrate]  Run Django migrations",
        "───────────────────────────────",
        "[build]    Build Docker image locally",
        "[publish]  Build & push to Docker Hub",
        "───────────────────────────────",
        "[quit]     Exit",
    ]

    # Separator indices (non-selectable)
    skip_indices = [4, 7]

    menu = TerminalMenu(
        options,
        cursor_index=0,
        skip_empty_entries=True,
        **MENU_STYLE,
    )

    idx = menu.show()

    if idx is None or idx == 8:  # quit
        print_info("Goodbye!")
        sys.exit(0)

    handlers = [
        cmd_dev,  # 0
        cmd_logs,  # 1
        cmd_shell,  # 2
        cmd_migrate,  # 3
        None,  # 4 (separator)
        cmd_build,  # 5
        cmd_publish,  # 6
        None,  # 7 (separator)
        None,  # 8 (quit)
    ]

    handler = handlers[idx]
    if handler:
        handler()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        handlers = {
            "build": cmd_build,
            "publish": cmd_publish,
            "dev": cmd_dev,
            "logs": cmd_logs,
            "shell": cmd_shell,
            "migrate": cmd_migrate,
            "help": lambda: print(__doc__),
            "--help": lambda: print(__doc__),
            "-h": lambda: print(__doc__),
        }

        handler = handlers.get(cmd)
        if handler:
            if cmd not in ("help", "--help", "-h"):
                print_banner()
            handler()
        else:
            print_error(f"Unknown command: {cmd}")
            print(__doc__)
            sys.exit(1)
    else:
        show_menu()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_info("Cancelled.")
        sys.exit(0)
