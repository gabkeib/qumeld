from enum import Enum
from typing import Protocol
from qiskit import QuantumCircuit
from qiskit.providers import BackendV2

from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.core.types import CircuitOptimisationResult

class MappingMetric(Enum):
    DEPTH = "depth"
    CNOT_COUNT = "cnot_count"
    SWAP_COUNT = "swap_count"
    GATE_COUNT = "gate_count"

class CircuitEvaluator(Protocol):
    def evaluate(self, circuit: QuantumCircuit) -> float:
        ...

class DepthEvaluator:
    def evaluate(self, circuit: QuantumCircuit) -> float:
        return float(circuit.depth())

class CNOTCountEvaluator:
    def evaluate(self, circuit: QuantumCircuit) -> float:
        return float(circuit.count_ops().get('cx', 0))

class SwapCountEvaluator:
    def evaluate(self, circuit: QuantumCircuit) -> float:
        return float(circuit.count_ops().get('swap', 0))

class MapperSelector:
    """Selects the optimal mapper based on a given metric."""

    def __init__(self, mapper_registry: MapperRegistry, metric: MappingMetric = MappingMetric.DEPTH):
        self.mapper_registry = mapper_registry
        self.evaluator: CircuitEvaluator
        self.current_metric: MappingMetric
        self.set_metric(metric)
    
    def set_metric(self, metric: MappingMetric) -> None:
        """Change the optimization metric"""
        evaluators: dict[MappingMetric, CircuitEvaluator] = {
            MappingMetric.DEPTH: DepthEvaluator(),
            MappingMetric.CNOT_COUNT: CNOTCountEvaluator(),
            MappingMetric.SWAP_COUNT: SwapCountEvaluator(),
        }
        self.evaluator = evaluators[metric]
        self.current_metric = metric
    
    def find_optimal_mapping(self, circuit: QuantumCircuit, backend: BackendV2) -> tuple[CircuitOptimisationResult, str, float]:
        """
        Brute force: tries all mappers and returns the best result.
        
        Returns:
            tuple: (best_circuit, best_mapper_name, score)
        """
        best_circuit: QuantumCircuit | None = None
        best_mapper_name: str | None = None
        best_score: float = float('inf')  # Lower is better

        mappers = self.mapper_registry.get_all_mappers()
        
        for mapper in mappers.values():
            mapped_circuit = mapper.map_circuit(circuit, backend)
            
            if mapped_circuit is None:
                continue

            score = self.evaluator.evaluate(mapped_circuit.optimised_circuit)
            
            if score < best_score:
                best_score = score
                best_circuit = mapped_circuit
                best_mapper_name = mapper.name
        
        if best_circuit is None or best_mapper_name is None:
            raise ValueError("No valid mapper found")
        
        return best_circuit, best_mapper_name, best_score
