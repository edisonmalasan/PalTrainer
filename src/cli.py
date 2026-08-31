from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional, Sequence


def env_flag(name: str) -> bool:
    return os.environ.get(name, '') in ('1', 'true', 'True')


def env_value(name: str, default: str = '') -> str:
    value = os.environ.get(name)
    return value if value is not None else default


@dataclass
class BootOptions:
    """Options that control the boot splash and process startup."""

    debug: bool = False
    no_gui: bool = False
    bootup_delay: Optional[int] = None


@dataclass
class AppOptions:
    """Options that control the main Qt application entry point."""

    save_path: Optional[str] = None
    logs: bool = False
    fix: bool = False
    test_loading_popup: bool = False


def parse_boot_options(argv: Optional[Sequence[str]] = None) -> BootOptions:
    """Parse boot-time CLI flags with legacy environment-variable fallbacks."""
    parser = _boot_parser()
    args, _ = parser.parse_known_args(list(argv) if argv is not None else sys.argv[1:])
    return BootOptions(
        debug=bool(args.debug) or env_flag('PALTRAINER_DEBUG'),
        no_gui=bool(args.no_gui) or env_flag('PALTRAINER_NO_GUI'),
        bootup_delay=args.bootup_delay if args.bootup_delay is not None else None,
    )


def parse_app_options(argv: Optional[Sequence[str]] = None) -> AppOptions:
    """Parse the save-processing CLI surface used by the Qt entry point.

    ``argv`` is the argument list without the script name (as from
    ``sys.argv[1:]``). The first non-``--`` argument is the save path and is
    preserved verbatim, so legacy paths without a ``.sav`` suffix are kept.
    """
    args = list(argv) if argv is not None else sys.argv[1:]
    opts = AppOptions()
    if args and not args[0].startswith('--'):
        opts.save_path = args[0].strip().strip('"')
    rest = args[1:] if opts.save_path else args
    for arg in rest:
        if arg in ('-logs', '--logs', '-log'):
            opts.logs = True
        elif arg in ('-fix', '--fix'):
            opts.fix = True
        elif arg == '--test-loading-popup':
            opts.test_loading_popup = True
    if opts.save_path and not (opts.logs or opts.fix):
        opts.logs = True
        opts.fix = True
    if opts.fix:
        opts.logs = True
    return opts


def _boot_parser():
    import argparse

    parser = argparse.ArgumentParser(prog='paltrainer', add_help=False)
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--no-gui', action='store_true', help='Disable the splash GUI')
    parser.add_argument('--bootup-delay', type=int, default=None, help='Splash delay in milliseconds')
    return parser
