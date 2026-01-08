from dataclasses import dataclass
import json
from typing import Dict, List
from pathlib import Path

from quantum_algorithms.registry import AlgorithmRegistry
from quantum_compiler.backends.factory import BackendFactory
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.mappers.base_mapper import QubitMapper
from quantum_compiler.core.types import CircuitOptimisationResult
from qiskit import qasm2
import logging

from qiskit.providers import BackendV2

log = logging.getLogger(__name__)

@dataclass
class ExperimentConfig:
    quantum_computer: str
    quantum_algorithm: str
    mapper_name: str
    output_dir: Path
    error_mitigation: List[str] = None
    algorithm_params: Dict[str, any] = None

    def __post_init__(self):
        if self.error_mitigation is None:
            self.error_mitigation = []
        self.output_dir = Path(self.output_dir)


class ExperimentRunner:
    """Main class for running quantum circuit optimization experiments."""

    def __init__(
        self,
        mapper_registry: MapperRegistry,
        backend_factory: BackendFactory,
        algorithm_registry: AlgorithmRegistry,
    ):
        self.mapper_registry = mapper_registry
        self.backend_factory = backend_factory
        self.algorithm_registry = algorithm_registry

    def run_experiment(self, config: ExperimentConfig) -> CircuitOptimisationResult:
        """Run a complete optimization experiment."""
        config.output_dir.mkdir(parents=True, exist_ok=True)

        backend = self.backend_factory.get_backend(config.quantum_computer)
        mapper = self.mapper_registry.get_mapper(config.mapper_name)

        try:
            if mapper.supports_circuit_mapping:
                result = self._run_circuit_experiment(mapper, backend, config)
            elif mapper.supports_raw_pauli_string_mapping:
                result = self._run_pauli_experiment(mapper, backend, config)
            else:
                raise ValueError(
                    f"Algorithm '{config.quantum_algorithm}' does not support "
                    "either circuits or Pauli strings"
                )
        except Exception as e:
            log.error(f"Experiment failed with error: {e}")
            result = CircuitOptimisationResult.create_failed(
                reason=str(e), original_circuit=None
            )

        self._save_results_to_file(result, config)

        return result

    def _run_circuit_experiment(
        self, mapper: QubitMapper, backend: BackendV2, config: ExperimentConfig
    ) -> CircuitOptimisationResult:
        """Run experiment with circuit input."""
        circuit = self.algorithm_registry.get_circuit(**config.algorithm_params)
        if circuit.num_qubits > backend.num_qubits:
            log.warning(
                f"SKIPPING: circuit requires {circuit.num_qubits} qubits, "
                f"but backend '{backend.name}' only has {backend.num_qubits} qubits."
            )
            return CircuitOptimisationResult.create_failed(
                reason=f"Circuit too large: {circuit.num_qubits} > {backend.num_qubits}",
                original_circuit=circuit,
            )
        return mapper.map_circuit(
            circuit=circuit, backend=backend, circuit_name=config.quantum_algorithm
        )

    def _run_pauli_experiment(
        self, mapper: QubitMapper, backend: BackendV2, config: ExperimentConfig
    ) -> CircuitOptimisationResult:
        """Run experiment with Pauli string input."""
        pauli_strings = self.algorithm_registry.get_pauli_strings(
            **config.algorithm_params
        )
        if len(pauli_strings[0].pauli_string) > backend.num_qubits:
            log.warning(
                f"SKIPPING: Pauli strings require {len(pauli_strings[0].pauli_string)} qubits, "
                f"but backend '{backend.name}' only has {backend.num_qubits} qubits."
            )
            return CircuitOptimisationResult.create_failed(
                reason=f"Circuit too large: {len(pauli_strings[0].pauli_string)} > {backend.num_qubits}",
                original_circuit=None,
            )
        return mapper.map_pauli_strings(
            pauli_strings=pauli_strings,
            backend=backend,
            circuit_name=config.quantum_algorithm,
        )

    def _save_results_to_file(
        self, result: CircuitOptimisationResult, config: ExperimentConfig
    ) -> None:
        json_path = config.output_dir / f"{config.mapper_name}.json"
        with open(json_path, "w") as f:
            json.dump(result.to_dict(), f, indent=4)

        if result.optimised_circuit is not None:
            qasm_path = config.output_dir / f"{config.mapper_name}.qasm"
            circuit_to_save = result.optimised_circuit.decompose()
            if circuit_to_save.num_parameters > 0:
                log.warning(
                    f"Warning: Skipping QASM export for {config.mapper_name} "
                    f"- circuit has {circuit_to_save.num_parameters} unbound parameters"
                )
            else:
                qasm2.dump(result.optimised_circuit.decompose(), open(qasm_path, "w"))
