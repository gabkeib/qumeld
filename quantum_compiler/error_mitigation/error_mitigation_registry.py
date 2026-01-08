from quantum_compiler.utils.class_discovery import discover_subclasses
from quantum_compiler.error_mitigation.base_technique import ErrorMitigationTechnique
import logging

log = logging.getLogger(__name__)

class ErrorMitigationRegistry:
    def __init__(self):
        self._techniques = {}
        self._discover_techniques()

    def _discover_techniques(self) -> None:
        """Scan specified paths and discover all error mitigation technique implementations."""
        discovered = discover_subclasses(
            base_class=ErrorMitigationTechnique,
            module_paths=["quantum_compiler.error_mitigation.techniques"],
            instantiate=True,
        )

        for technique_instance in discovered.values():
            technique_name = technique_instance.name
            self._techniques[technique_name] = technique_instance
            log.info(f"Discovered error mitigation technique: {technique_name}")

    def register_technique(self, technique: ErrorMitigationTechnique) -> None:
        """Manually register an error mitigation technique instance."""
        technique_name = technique.name
        self._techniques[technique_name] = technique
        log.info(f"Manually registered error mitigation technique: {technique_name}")

    def get_technique(self, name: str) -> ErrorMitigationTechnique:
        """Retrieve an error mitigation technique by name."""
        if name not in self._techniques:
            available = list(self._techniques.keys())
            raise ValueError(
                f"Error mitigation technique '{name}' not found. Available techniques: {available}"
            )
        return self._techniques[name]
