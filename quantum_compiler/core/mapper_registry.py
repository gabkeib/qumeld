from typing import List, Dict
import importlib
import inspect
from pathlib import Path
import logging

from quantum_compiler.mappers.base_mapper import QubitMapper
from quantum_compiler.utils.class_discovery import discover_subclasses

log = logging.getLogger(__name__)

class MapperRegistry:
    """A registry that automatically discovers and loads mapper implementations."""

    def __init__(self, base_paths: List[str] = None, disabled: List[str] = None):
        """
        Args:
            base_paths: List of module paths to search (example: ['mappers.native', 'mappers.wrappers'])
            disabled: List of mapper names to disable on the auto-discovery (blacklist)
        """
        self.base_paths = base_paths or [
            "quantum_compiler.mappers.native",
            "quantum_compiler.mappers.wrappers",
        ]
        self.disabled = set(disabled or [])
        self._mappers: Dict[str, QubitMapper] = {}
        self._discover_mappers()

    def _discover_mappers(self) -> None:
        """Scan specified paths and discover all mapper implementations."""
        discovered = discover_subclasses(
            base_class=QubitMapper, module_paths=self.base_paths, instantiate=True
        )

        for mapper_instance in discovered.values():
            mapper_name = mapper_instance.name

            if mapper_name in self.disabled:
                log.warning(f"Skipping mapper: {mapper_name} (in disabled list)")
                continue

            self._mappers[mapper_name] = mapper_instance
            log.info(f"Discovered mapper: {mapper_name}")
    def get_mapper(self, name: str) -> QubitMapper:
        """Retrieve a mapper by name."""
        if name not in self._mappers:
            available = list(self._mappers.keys())
            raise ValueError(
                f"Mapper '{name}' not found. Available mappers: {available}"
            )
        return self._mappers[name]

    def register_mapper(self, mapper: QubitMapper) -> None:
        """Manually register a mapper instance."""
        mapper_name = mapper.name
        self._mappers[mapper_name] = mapper
        log.info(f"Manually registered mapper: {mapper_name}")

    def list_available_mappers(self) -> List[str]:
        """List all registered mapper names."""
        return list(self._mappers.keys())

    def get_all_mappers(self) -> Dict[str, QubitMapper]:
        """Get all registered mappers."""
        return self._mappers.copy()
