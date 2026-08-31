import os
import sys

from boot_paths import ROOT_DIR, SRC_DIR


def setup() -> None:
    src = str(SRC_DIR)
    if src not in sys.path:
        sys.path.insert(0, src)


def get_src_dir() -> str:
    return str(SRC_DIR)


def get_project_dir() -> str:
    return str(ROOT_DIR)
