from enum import Enum
from typing import Protocol
from qiskit import QuantumCircuit
from qiskit.providers import BackendV2

from quantum_compiler.backends.utils import TopologyGroup, extract_topology_features, topology_group
from quantum_compiler.circuits.utils import extract_circuit_features
from quantum_compiler.converters.pauli_strings_to_circuit import convert_pauli_strings_to_circuit
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.core.types import CircuitOptimisationResult, PauliString
from quantum_compiler.mappers.base_mapper import QubitMapper
from scripts.run_extract_backend_features import extract_backend_features


class MappingMetric(Enum):
    DEPTH = "depth"
    CNOT_COUNT = "cnot_count"


class CircuitEvaluator(Protocol):
    def evaluate(self, circuit: QuantumCircuit) -> float: ...
    def select_optimal_mapper_circuit(self, circuit: QuantumCircuit, backend: BackendV2) -> str: ...
    def select_optimal_mapper_pauli_strings(self, pauli_strings: list[PauliString], backend: BackendV2) -> str: ...


class DepthEvaluator:
    def evaluate(self, circuit: QuantumCircuit) -> float:
        return float(circuit.depth())
    
    def select_optimal_mapper_circuit(self, circuit: QuantumCircuit, backend: BackendV2) -> str:
        topology_features = extract_topology_features(backend)

        topology_group_value = topology_group(
            topology_features["average_degree"],
            topology_features["edge_density"]
        )

        if topology_group_value == TopologyGroup.FULLY_CONNECTED:
            return "rustiq"
        
        if topology_features["num_qubits"] > 100:
            return "qiskit_ai"
        else:
            return "rustiq"
        
    def select_optimal_mapper_pauli_strings(self, pauli_strings: list[PauliString], backend: BackendV2) -> str:
        topology_features = extract_topology_features(backend)

        circuit = convert_pauli_strings_to_circuit(
            pauli_strings, num_qubits=len(pauli_strings[0].pauli_string)
        )
        circuit_features = extract_circuit_features(circuit)

        if circuit_features['max_interactions_per_edge'] == 1:
            return "qiskit_ai"
        else:
            return "pauliforest"



class CNOTCountEvaluator:
    def evaluate(self, circuit: QuantumCircuit) -> float:
        return float(circuit.count_ops().get("cx", 0))
    
    def select_optimal_mapper_circuit(self, circuit: QuantumCircuit, backend: BackendV2) -> str:
        return "lightSABRE_lookahead"
        
    def select_optimal_mapper_pauli_strings(self, pauli_strings: list[PauliString], backend: BackendV2) -> str:
        topology_features = extract_topology_features(backend)

        circuit = convert_pauli_strings_to_circuit(
            pauli_strings, num_qubits=len(pauli_strings[0].pauli_string)
        )
        circuit_features = extract_circuit_features(circuit)
        
        topology_group_value = topology_group(
            topology_features["average_degree"],
            topology_features["edge_density"]
        )

        if topology_group_value == TopologyGroup.FULLY_CONNECTED:
            return "pauliforest"

        if circuit_features['num_qubits'] <= 5 and circuit_features['graph_density'] >= 0.9:
            return "pauliforest"
        
        if circuit_features['circuit_depth'] > 1000:
            return "rustiq"

        if topology_group_value == TopologyGroup.HEAVY_HEX:
            return "lightSABRE_lookahead"
        else:
            return "rustiq"


class MapperSelector:
    """Selects the optimal mapper based on a given metric."""

    def __init__(
        self,
        mapper_registry: MapperRegistry,
        metric: MappingMetric = MappingMetric.DEPTH,
    ):
        self.mapper_registry = mapper_registry
        self.evaluator: CircuitEvaluator
        self.current_metric: MappingMetric
        self.set_metric(metric)

    def set_metric(self, metric: MappingMetric) -> None:
        """Change the optimization metric"""
        evaluators: dict[MappingMetric, CircuitEvaluator] = {
            MappingMetric.DEPTH: DepthEvaluator(),
            MappingMetric.CNOT_COUNT: CNOTCountEvaluator(),
        }
        self.evaluator = evaluators[metric]
        self.current_metric = metric

    def find_optimal_mapping_pauli_strings(
        self,
        pauli_strings: list[PauliString],
        backend: BackendV2
    ) -> tuple[CircuitOptimisationResult, str, float]:
        """
        Brute force: tries all mappers and returns the best result.

        Returns:
            tuple: (best_circuit, best_mapper_name, score)
        """
        best_circuit: CircuitOptimisationResult | None = None
        best_mapper_name: str | None = None
        best_score: float = float("inf")  # Lower is better

        mappers = self.mapper_registry.get_all_mappers()

        for mapper in mappers.values():
            if mapper.supports_raw_pauli_string_mapping:
                mapped_circuit = mapper.map_pauli_strings(
                    pauli_strings, backend
                )
            else:
                circuit = convert_pauli_strings_to_circuit(
                    pauli_strings, num_qubits=len(pauli_strings[0].pauli_string)
                )
                mapped_circuit = mapper.map_circuit(circuit, backend)

            if mapped_circuit is None:
                continue

            score = self.evaluator.evaluate(mapped_circuit.optimised_circuit)
            print(f"Mapper {mapper.name} produced score {score} with circuit {mapped_circuit.optimised_circuit.name} (depth={mapped_circuit.depth}, cx_count={mapped_circuit.optimised_circuit.count_ops().get("cx", 0)})")

            if score < best_score:
                best_score = score
                best_circuit = mapped_circuit
                best_mapper_name = mapper.name

        if best_circuit is None or best_mapper_name is None:
            raise ValueError("No valid mapper found")

        return best_circuit, best_mapper_name, best_score

    def find_optimal_mapping_circuit(
        self, circuit: QuantumCircuit, backend: BackendV2
    ) -> tuple[CircuitOptimisationResult, str, float]:
        """
        Brute force: tries all mappers and returns the best result.

        Returns:
            tuple: (best_circuit, best_mapper_name, score)
        """
        best_circuit: QuantumCircuit | None = None
        best_mapper_name: str | None = None
        best_score: float = float("inf")  # Lower is better

        mappers = self.mapper_registry.get_all_mappers()

        for mapper in mappers.values():
            mapped_circuit = mapper.map_circuit(circuit, backend)

            if mapped_circuit is None:
                continue

            score = self.evaluator.evaluate(mapped_circuit.optimised_circuit)
            print(f"Mapper {mapper.name} produced score {score} with circuit {mapped_circuit.optimised_circuit.name} (depth={mapped_circuit.depth}, cx_count={mapped_circuit.optimised_circuit.count_ops().get("cx", 0)})")

            if score < best_score:
                best_score = score
                best_circuit = mapped_circuit
                best_mapper_name = mapper.name

        if best_circuit is None or best_mapper_name is None:
            raise ValueError("No valid mapper found")

        return best_circuit, best_mapper_name, best_score
    
    def find_optimal_mapping_pauli_strings_fast(
            self,
            pauli_strings: list[PauliString],
            backend: BackendV2
    ) -> tuple[CircuitOptimisationResult, str, float]:
        algorithm_to_use = self.evaluator.select_optimal_mapper_pauli_strings(
            pauli_strings, backend
        )

        mapper = self.mapper_registry.get_mapper(algorithm_to_use)
        if mapper.supports_raw_pauli_string_mapping:
            mapped_circuit = mapper.map_pauli_strings(
                pauli_strings, backend
            )
        else:
            circuit = convert_pauli_strings_to_circuit(
                pauli_strings, num_qubits=len(pauli_strings[0].pauli_string)
            )
            mapped_circuit = mapper.map_circuit(circuit, backend)

        score = self.evaluator.evaluate(mapped_circuit.optimised_circuit)

        return mapped_circuit, algorithm_to_use, score        

    def find_optimal_mapping_circuit_fast(
        self,
        circuit: QuantumCircuit,
        backend: BackendV2
    ) -> tuple[CircuitOptimisationResult, str, float]:
        algorithm_to_use = self.evaluator.select_optimal_mapper_circuit(
            circuit, backend
        )

        mapper = self.mapper_registry.get_mapper(algorithm_to_use)
        mapped_circuit = mapper.map_circuit(circuit, backend)
        if mapped_circuit is None:
            return None, algorithm_to_use, float("inf")
        score = self.evaluator.evaluate(mapped_circuit.optimised_circuit)

        return mapped_circuit, algorithm_to_use, score
