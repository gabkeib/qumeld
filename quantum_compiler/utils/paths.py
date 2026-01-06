from pathlib import Path


def get_project_root() -> Path:
    """Returns project root folder."""
    current_path = Path(__file__).resolve().parent

    for parent in [current_path] + list(current_path.parents):
        if (parent / "pyproject.toml").exists() or (
            parent / "requirements.txt"
        ).exists():
            return parent

    return current_path
