import importlib
import inspect
import logging
from pathlib import Path
from typing import Type, List, Callable, Optional

log = logging.getLogger(__name__)

def discover_subclasses(
    base_class: Type,
    module_paths: List[str],
    filter_func: Optional[Callable[[Type], bool]] = None,
    instantiate: bool = False,
) -> dict:
    """
    Recursively discover and optionally instantiate subclasses of a base class.

    Args:
        base_class: The base class to search for subclasses
        module_paths: List of module paths to search
        filter_func: Optional function to filter discovered classes
        instantiate: Whether to instantiate the classes

    Returns:
        Dictionary mapping class names to classes or instances
    """
    discovered = {}

    for module_path in module_paths:
        _scan_module_recursive(
            module_path, base_class, discovered, filter_func, instantiate
        )

    return discovered


def _scan_module_recursive(
    module_path: str,
    base_class: Type,
    discovered: dict,
    filter_func: Optional[Callable] = None,
    instantiate: bool = False,
) -> None:
    """Recursively scan a module for subclasses."""
    try:
        module = importlib.import_module(module_path)
    except ImportError:
        return

    for name, obj in inspect.getmembers(module, inspect.isclass):
        if (
            issubclass(obj, base_class)
            and obj is not base_class
            and not inspect.isabstract(obj)
        ):
            if filter_func and not filter_func(obj):
                continue

            try:
                if instantiate:
                    discovered[name] = obj()
                else:
                    discovered[name] = obj
            except Exception as e:
                log.warning(f"Could not process {name}: {e}")

    # Scan submodules if this is a package
    if hasattr(module, "__path__"):
        package_path = Path(module.__path__[0])
        for submodule_file in package_path.glob("*.py"):
            if submodule_file.stem != "__init__":
                _scan_module_recursive(
                    f"{module_path}.{submodule_file.stem}",
                    base_class,
                    discovered,
                    filter_func,
                    instantiate,
                )
