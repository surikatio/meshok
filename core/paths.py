import sys
import os


def get_app_dir() -> str:
    """Директория рядом с exe (в сборке) или корень проекта (при запуске из исходников)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
