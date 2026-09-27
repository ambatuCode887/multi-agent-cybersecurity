from __future__ import annotations

from pathlib import Path

from .config import load_environment, project_env_path


def load_project_env() -> Path | None:
    """Load and return the configured project environment file."""
    load_environment()
    return project_env_path()

ENV_PATH = load_project_env()