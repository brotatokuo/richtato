"""
Richtato CLI - Interactive development and deployment tool

Usage:
    richtato              # Interactive menu
    richtato build        # Build Docker image
    richtato publish      # Build & push to Docker Hub
    richtato bank         # Bank sync setup and operations
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional, Sequence

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


def run_cmd(
    cmd: list[str],
    cwd: Optional[str] = None,
    env: Optional[dict[str, str]] = None,
) -> int:
    """Run a command and return exit code."""
    print(f"{Colors.DIM}$ {' '.join(cmd)}{Colors.END}")
    result = subprocess.run(cmd, cwd=cwd, env=env)
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


def _bank_agent_venv(root: str) -> Path:
    return Path(root) / "scripts" / "bank_sync" / ".venv"


def _bank_agent_python(root: str) -> Path:
    return _bank_agent_venv(root) / "bin" / "python"


def _bank_agent_log(root: str) -> Path:
    return Path(root) / "local_data" / "bank-agent.log"


def _default_bank_setup_path(root: str) -> Path:
    return Path(root) / "richtato-bank-agent-setup.yml"


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        if key in {
            "BANK_AGENT_FERNET_KEY",
            "RICHTATO_API_TOKEN",
            "RICHTATO_API_BASE_URL",
        }:
            values[key] = value.strip().strip("'\"")
    return values


def _parse_setup_yaml_env(path: Path) -> dict[str, str]:
    """Read only the generated setup YAML env block, without logging secrets."""
    values: dict[str, str] = {}
    if not path.exists():
        return values

    in_env_block = False
    for line in path.read_text().splitlines():
        if line.strip() == "env:":
            in_env_block = True
            continue
        if not in_env_block:
            continue
        if line and not line.startswith((" ", "\t")):
            break
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        key = key.strip()
        if key in {
            "BANK_AGENT_FERNET_KEY",
            "RICHTATO_API_TOKEN",
            "RICHTATO_API_BASE_URL",
        }:
            values[key] = value.strip().strip("'\"")
    return values


def _bank_agent_env(root: str, setup_path: Optional[Path] = None) -> dict[str, str]:
    env = os.environ.copy()
    root_path = Path(root)
    loaded = _parse_env_file(root_path / ".env")
    if setup_path:
        loaded.update(_parse_setup_yaml_env(setup_path))
    else:
        loaded.update(_parse_setup_yaml_env(_default_bank_setup_path(root)))

    env.update({key: value for key, value in loaded.items() if value})
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        f"{root}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else root
    )
    return env


def _prime_bank_agent_process_env(setup_path: Path) -> None:
    """Keep follow-up commands in one guided flow using the same setup YAML."""
    os.environ.update(
        {
            key: value
            for key, value in _parse_setup_yaml_env(setup_path).items()
            if value
        }
    )


def _ensure_bank_agent_runtime(root: str) -> bool:
    venv = _bank_agent_venv(root)
    python = _bank_agent_python(root)
    requirements = Path(root) / "scripts" / "bank_sync" / "requirements.txt"

    if python.exists():
        return True

    print_header("Bank Agent Runtime")
    print_info("Creating local Playwright runtime in scripts/bank_sync/.venv")
    result = run_cmd(["python3", "-m", "venv", str(venv)], cwd=root)
    if result != 0:
        print_error("Could not create bank-agent virtualenv.")
        return False

    result = run_cmd(
        [str(python), "-m", "pip", "install", "-q", "-r", str(requirements)],
        cwd=root,
    )
    if result != 0:
        print_error("Could not install bank-agent Python requirements.")
        return False

    result = run_cmd([str(python), "-m", "playwright", "install", "chromium"], cwd=root)
    if result != 0:
        print_error("Could not install Playwright Chromium.")
        return False

    print_success("Bank-agent runtime is ready.")
    return True


def _run_bank_agent(
    args: Sequence[str],
    *,
    root: Optional[str] = None,
    setup_path: Optional[Path] = None,
    ensure_runtime: bool = True,
) -> int:
    root = root or get_project_root()
    if ensure_runtime and not _ensure_bank_agent_runtime(root):
        return 1

    cmd = [str(_bank_agent_python(root)), "-m", "scripts.bank_sync.agent", *args]
    return run_cmd(cmd, cwd=root, env=_bank_agent_env(root, setup_path))


def _resolve_setup_path(root: str, path_arg: Optional[str] = None) -> Optional[Path]:
    if path_arg:
        path = Path(path_arg).expanduser()
        if not path.is_absolute():
            path = Path(root) / path
    else:
        path = _default_bank_setup_path(root)

    if path.exists():
        return path

    print_error(f"Setup YAML not found: {path}")
    entered = prompt(
        "Path to richtato-bank-agent-setup.yml (blank to cancel)",
        "",
    )
    if not entered:
        return None
    entered_path = Path(entered).expanduser()
    if not entered_path.is_absolute():
        entered_path = Path(root) / entered_path
    if not entered_path.exists():
        print_error(f"Setup YAML not found: {entered_path}")
        return None
    return entered_path


def _login_ids_prompt(text: str) -> list[str]:
    raw = prompt(text, "")
    return [part.strip() for part in raw.split(",") if part.strip()]


def _bank_status(root: str) -> int:
    print_header("Bank Sync Status")
    return _run_bank_agent(["status"], root=root)


def _bank_apply(root: str, setup_path: Optional[Path] = None) -> int:
    setup_path = setup_path or _resolve_setup_path(root)
    if setup_path is None:
        print_info("Cancelled.")
        return 1
    _prime_bank_agent_process_env(setup_path)
    print_header("Apply Bank Sync Setup")
    return _run_bank_agent(["apply", str(setup_path)], root=root, setup_path=setup_path)


def _bank_signin(root: str, login_id: Optional[str] = None) -> int:
    if not login_id:
        _bank_status(root)
        login_id = prompt("Login ID to sign in", "")
    if not login_id:
        print_info("Cancelled.")
        return 1
    print_header(f"Bank Sign-In #{login_id}")
    return _run_bank_agent(["login", "signin", login_id], root=root)


def _bank_sync(root: str, login_id: Optional[str] = None, headed: bool = False) -> int:
    if not login_id:
        _bank_status(root)
        login_id = prompt("Login ID to sync", "")
    if not login_id:
        print_info("Cancelled.")
        return 1
    args = ["sync", login_id]
    if headed:
        args.append("--headed")
    print_header(f"Bank Sync #{login_id}")
    return _run_bank_agent(args, root=root)


def _bank_start_daemon(root: str) -> int:
    if not _ensure_bank_agent_runtime(root):
        return 1

    existing = subprocess.run(
        ["pgrep", "-f", "scripts.bank_sync.agent run"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if existing.returncode == 0 and existing.stdout.strip():
        print_info("Bank-agent daemon already appears to be running.")
        return 0

    log_path = _bank_agent_log(root)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(_bank_agent_python(root)), "-m", "scripts.bank_sync.agent", "run"]
    print(f"{Colors.DIM}$ {' '.join(cmd)} > {log_path}{Colors.END}")
    with log_path.open("ab") as log_file:
        subprocess.Popen(
            cmd,
            cwd=root,
            env=_bank_agent_env(root),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    print_success(f"Bank-agent daemon started. Log: {log_path}")
    return 0


def _bank_logs(root: str, follow: bool = False) -> int:
    log_path = _bank_agent_log(root)
    if not log_path.exists():
        print_error(f"No bank-agent log found yet: {log_path}")
        return 1
    cmd = ["tail"]
    if follow:
        cmd.append("-f")
    else:
        cmd.extend(["-n", "80"])
    cmd.append(str(log_path))
    return run_cmd(cmd, cwd=root)


def cmd_bank_setup(path_arg: Optional[str] = None):
    """Guided setup for the local Playwright bank-agent."""
    root = get_project_root()
    print_header("Guided Bank Sync Setup")

    setup_path = _resolve_setup_path(root, path_arg)
    if setup_path is None:
        print_info("Cancelled.")
        return

    if not _ensure_bank_agent_runtime(root):
        sys.exit(1)

    result = _bank_apply(root, setup_path)
    if result != 0:
        sys.exit(result)

    _bank_status(root)

    print_info(
        "Optional: enter login IDs from the status list to refresh bank cookies."
    )
    print_info("Leave blank if all listed logins are already active.")
    for login_id in _login_ids_prompt(
        "Login IDs to sign in or re-authenticate (comma-separated)"
    ):
        result = _bank_signin(root, login_id)
        if result != 0 and not confirm("Continue with remaining sign-ins?"):
            sys.exit(result)

    print_info("Optional: enter login IDs to run an immediate sync now.")
    print_info("Leave blank to finish setup without syncing.")
    for login_id in _login_ids_prompt("Login IDs to sync now (comma-separated)"):
        result = _bank_sync(root, login_id)
        if result != 0 and not confirm("Continue with remaining syncs?"):
            sys.exit(result)

    print_success("Bank sync setup flow complete.")


def cmd_bank_menu():
    """Interactive bank sync operations menu."""
    root = get_project_root()
    print_header("Bank Sync")

    options = [
        "Guided setup",
        "Status",
        "Sign in / refresh cookies",
        "Run manual sync",
        "Start daemon",
        "View log",
        "Apply setup YAML",
        "Back",
    ]
    idx = select("Select bank sync action:", options, default=0)
    if idx is None or idx == 7:
        print_info("Cancelled.")
        return

    if idx == 0:
        cmd_bank_setup()
    elif idx == 1:
        _bank_status(root)
    elif idx == 2:
        _bank_signin(root)
    elif idx == 3:
        _bank_sync(root)
    elif idx == 4:
        _bank_start_daemon(root)
    elif idx == 5:
        _bank_logs(root, follow=confirm("Follow log?", default=False))
    elif idx == 6:
        result = _bank_apply(root)
        if result == 0:
            _bank_status(root)


def cmd_bank(args: Optional[Sequence[str]] = None):
    """Bank sync setup and operations."""
    args = list(args or [])
    root = get_project_root()

    if not args:
        cmd_bank_menu()
        return

    command = args[0]
    if command in ("help", "--help", "-h"):
        print(
            "Usage: richtato bank [setup|status|signin|sync|daemon|logs|apply]\n\n"
            "Examples:\n"
            "  richtato bank setup\n"
            "  richtato bank status\n"
            "  richtato bank signin 1\n"
            "  richtato bank sync 1\n"
            "  richtato bank daemon\n"
            "  richtato bank logs --follow\n"
        )
    elif command == "setup":
        cmd_bank_setup(args[1] if len(args) > 1 else None)
    elif command == "status":
        sys.exit(_bank_status(root))
    elif command == "signin":
        sys.exit(_bank_signin(root, args[1] if len(args) > 1 else None))
    elif command == "sync":
        headed = "--headed" in args[1:]
        login_ids = [arg for arg in args[1:] if arg != "--headed"]
        sys.exit(_bank_sync(root, login_ids[0] if login_ids else None, headed=headed))
    elif command == "daemon":
        sys.exit(_bank_start_daemon(root))
    elif command == "logs":
        sys.exit(_bank_logs(root, follow="--follow" in args[1:] or "-f" in args[1:]))
    elif command == "apply":
        setup_path = _resolve_setup_path(root, args[1] if len(args) > 1 else None)
        if setup_path is None:
            sys.exit(1)
        sys.exit(_bank_apply(root, setup_path))
    else:
        print_error(f"Unknown bank command: {command}")
        sys.exit(1)


def show_menu():
    """Show the main interactive menu."""
    print_banner()

    print(f"{Colors.BOLD}What would you like to do?{Colors.END}")
    print(f"{Colors.DIM}Use ↑↓ arrows to navigate, Enter to select{Colors.END}\n")

    options = [
        "[bank]     Bank sync setup and operations",
        "───────────────────────────────",
        "[build]    Build Docker image locally",
        "[publish]  Build & push to Docker Hub",
        "───────────────────────────────",
        "[quit]     Exit",
    ]

    # Separator indices (non-selectable)
    skip_indices = [1, 4]

    menu = TerminalMenu(
        options,
        cursor_index=0,
        skip_empty_entries=True,
        **MENU_STYLE,
    )

    idx = menu.show()

    if idx is None or idx == 5:  # quit
        print_info("Goodbye!")
        sys.exit(0)

    handlers = [
        cmd_bank_menu,  # 0
        None,  # 1 (separator)
        cmd_build,  # 2
        cmd_publish,  # 3
        None,  # 4 (separator)
        None,  # 5 (quit)
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
            "bank": lambda: cmd_bank(sys.argv[2:]),
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
