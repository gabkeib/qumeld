from typing import List
from qiskit import QuantumCircuit, qasm2
from pathlib import Path
from quantum_compiler.backends.factory import BackendFactory
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.core.mapper_selector import MapperSelector
from quantum_compiler.core.types import CircuitOptimisationResult
from quantum_compiler.mappers.base_mapper import QubitMapper


def run_circuit_optimisation(
    circuit: QuantumCircuit,
    quantum_computer: str,
    mappers_to_use: List[str],
    output_dir: Path = None,
) -> List[CircuitOptimisationResult]:
    """Run optimisation on a custom circuit."""

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    backend_factory = BackendFactory()
    backend = backend_factory.get_backend(quantum_computer)

    mapper_registry = MapperRegistry()

    if mappers_to_use[0] == "auto" and len(mappers_to_use) == 1:
        mappers_selector = MapperSelector(mapper_registry)
        best_circuit_res, _, _ = mappers_selector.find_optimal_mapping(circuit, backend)

        if output_dir is not None:
            qasm_path = output_dir / f"optimised_circuit_{mappers_to_use}.qasm"
            with open(qasm_path, "w") as f:
                qasm2.dump(best_circuit_res.optimised_circuit, f)
        return [best_circuit_res]
    elif mappers_to_use[0] == "auto" and len(mappers_to_use) > 1:
        raise ValueError(
            "When using 'auto' as optimizer, it must be the only entry in the list."
        )

    results: List[CircuitOptimisationResult] = []
    for mapper_name in mappers_to_use:
        mapper = mapper_registry.get_mapper(mapper_name)
        result = mapper.map_circuit(
            circuit=circuit, backend=backend, circuit_name="custom_circuit"
        )
        results.append(result)

        if output_dir is not None:
            qasm_path = output_dir / f"optimised_circuit_{mapper_name}.qasm"
            with open(qasm_path, "w") as f:
                qasm2.dump(result.optimised_circuit, f)

    return results
