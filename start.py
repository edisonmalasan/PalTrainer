from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


# ============================================================
# PALTRAINER
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
VENV_DIR = PROJECT_DIR / ".venv"


# ============================================================
# COLORS
# ============================================================

USE_ANSI = True

if os.name == "nt":
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)

        mode = ctypes.c_uint32()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)

    except Exception:
        USE_ANSI = False


def ansi(code: str) -> str:
    return code if USE_ANSI else ""


RESET = ansi("\033[0m")
BOLD = ansi("\033[1m")
DIM = ansi("\033[2m")

GREEN = ansi("\033[92m")
CYAN = ansi("\033[96m")
YELLOW = ansi("\033[93m")
RED = ansi("\033[91m")
WHITE = ansi("\033[97m")


# ============================================================
# PALTRAINER LOGO
# ============================================================

LOGO = f"""
{CYAN}██████╗  █████╗ ██╗         ████████╗██████╗  █████╗ ██╗███╗   ██╗███████╗██████╗
██╔══██╗██╔══██╗██║         ╚══██╔══╝██╔══██╗██╔══██╗██║████╗  ██║██╔════╝██╔══██╗
██████╔╝███████║██║            ██║   ██████╔╝███████║██║██╔██╗ ██║█████╗  ██████╔╝
██╔═══╝ ██╔══██║██║            ██║   ██╔══██╗██╔══██║██║██║╚██╗██║██╔══╝  ██╔══██╗
██║     ██║  ██║███████╗       ██║   ██║  ██║██║  ██║██║██║ ╚████║███████╗██║  ██║
╚═╝     ╚═╝  ╚═╝╚══════╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝{RESET}
"""


# ============================================================
# UI
# ============================================================

def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def success(message: str) -> None:
    print(f"  {GREEN}✓{RESET} {message}")


def info(message: str) -> None:
    print(f"  {CYAN}›{RESET} {message}")


def warning(message: str) -> None:
    print(f"  {YELLOW}!{RESET} {message}")


def error(message: str) -> None:
    print(f"  {RED}✗{RESET} {message}")


def divider(char: str = "─", width: int = 64) -> None:
    print(f"{DIM}{char * width}{RESET}")


# ============================================================
# VIRTUAL ENVIRONMENT
# ============================================================

def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"

    return VENV_DIR / "bin" / "python"


def uv_available() -> bool:
    return shutil.which("uv") is not None


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=cwd or PROJECT_DIR,
        text=True,
    )


def ensure_venv() -> bool:
    vpy = venv_python()

    # Already installed
    if vpy.exists():
        return True

    # Check UV
    if not uv_available():
        error("UV was not found on your system.")
        return False

    info("Creating virtual environment...")

    result = run_command(
        ["uv", "venv", str(VENV_DIR)]
    )

    if result.returncode != 0:
        error("Failed to create virtual environment.")
        return False

    info("Installing dependencies...")

    result = run_command(
        ["uv", "sync"]
    )

    if result.returncode != 0:
        error("Failed to install dependencies.")

        if VENV_DIR.exists():
            shutil.rmtree(VENV_DIR, ignore_errors=True)

        return False

    return True


# ============================================================
# START PALTRAINER
# ============================================================

def start_paltrainer() -> int:
    bootup_py = PROJECT_DIR / "src" / "bootup.py"
    vpy = venv_python()

    if not bootup_py.exists():
        error("Could not find src/bootup.py.")
        return 1

    if not vpy.exists():
        error("PALTRAINER environment was not found.")
        return 1

    print()
    info("Starting PALTRAINER...")
    print()

    try:
        result = subprocess.run(
            [str(vpy), str(bootup_py)],
            cwd=PROJECT_DIR,
        )

        return result.returncode

    except KeyboardInterrupt:
        return 0

    except Exception as exc:
        error(f"Failed to start PALTRAINER: {exc}")
        return 1


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    clear_screen()

    print(LOGO)

    # Setup
    if not ensure_venv():
        print()
        error("PALTRAINER setup failed.")
        print()

        if os.name == "nt":
            input("Press Enter to exit...")

        sys.exit(1)

    # Start
    exit_code = start_paltrainer()

    if exit_code != 0:
        print()
        error(f"PALTRAINER exited with code {exit_code}.")
        print()

        if os.name == "nt":
            input("Press Enter to exit...")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
