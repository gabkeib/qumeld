import re
from quantum_algorithms.registry import AlgorithmRegistry
from quantum_compiler.backends.factory import BackendFactory
from quantum_compiler.core import mapper_selector
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.core.mapper_selector import MapperSelector, MappingMetric
from quantum_compiler.core.mapper_registry import MapperRegistry
from typing import Any
import json

def generalisation_evaluation(metric: MappingMetric) -> dict:
    algorithm_registry = AlgorithmRegistry()
    mapper_registry = MapperRegistry()
    mapper_selector_default = MapperSelector(mapper_registry, metric=metric)
    backend_factory = BackendFactory()

    algorithms = algorithm_registry.list_algorithms()
    backends = backend_factory.list_available()

    results = []
    mapper_selector = mapper_selector_default
    for algorithm_name in algorithms:
        for backend_name in backends:
            backend = backend_factory.get_backend(backend_name)
            algorithm_params: dict[str, Any] = {"name": algorithm_name}
            if algorithm_name == "qaoa" or algorithm_name == "qaoa_ansatz":
                algorithm_params["graph"] = [
                    [0, 1, 1, 0, 1],
                    [1, 0, 1, 0, 0],
                    [1, 1, 0, 1, 0],
                    [0, 0, 1, 0, 1],
                    [1, 0, 0, 1, 0],
                ]
                algorithm_params["num_qubits"] = 5

            if algorithm_name == "efficient_su2":
                algorithm_params["num_qubits"] = 5

            if algorithm_name == "liH":
                mapper_registry_diff = MapperRegistry(disabled=["doustra"])
                mapper_selector = MapperSelector(mapper_registry_diff)
            optimal_mapper = None
            selected_mapper_by_generalisation = None
            if algorithm_registry.algorithm_supports_pauli_strings(algorithm_name):
                pauli_strings = algorithm_registry.get_pauli_strings(**algorithm_params)
                if len(pauli_strings[0].pauli_string) > backend.num_qubits:
                    # Skip if Pauli strings do not fit on the backend
                    continue
                _, optimal_mapper, best_res = mapper_selector.find_optimal_mapping_pauli_strings(
                    pauli_strings=pauli_strings,
                    backend=backend,
                )
                _, selected_mapper_by_generalisation, calc_res = mapper_selector.find_optimal_mapping_pauli_strings_fast(
                    pauli_strings=pauli_strings,
                    backend=backend,
                )

            elif algorithm_registry.algorithm_supports_circuits(algorithm_name):
                circuit = algorithm_registry.get_circuit(**algorithm_params)
                if circuit.num_qubits > backend.num_qubits:
                    # Skip if circuit does not fit on the backend
                    continue
                _, optimal_mapper, best_res = mapper_selector.find_optimal_mapping_circuit(
                    circuit=circuit,
                    backend=backend,
                )
                _, selected_mapper_by_generalisation, calc_res = mapper_selector.find_optimal_mapping_circuit_fast(
                    circuit=circuit,
                    backend=backend,
                )
            else:
                print(
                    f"Algorithm '{algorithm_name}' does not support "
                    "either circuits or Pauli strings"
                )
                continue

            mapper_selector = mapper_selector_default
            correct_selection = optimal_mapper == selected_mapper_by_generalisation

            map_results = {}
            map_results["algorithm_name"] = algorithm_name
            map_results["backend"] = backend_name
            map_results["optimal_mapper"] = optimal_mapper
            map_results["selected_mapper_by_generalisation"] = selected_mapper_by_generalisation
            map_results["correct_selection"] = correct_selection
            map_results["best_score"] = best_res
            map_results["calculated_score"] = calc_res

            results.append(map_results)

    return results



if __name__ == "__main__":
    evaluation_results = generalisation_evaluation(MappingMetric.CNOT_COUNT)
    with open("generalisation_evaluation_results_cnot.json", "w") as f:
        json.dump(evaluation_results, f, indent=4)
