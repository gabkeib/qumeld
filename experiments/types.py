from dataclasses import dataclass, field
import json
from statistics import variance
from qiskit import QuantumCircuit

@dataclass
class CircuitOptimisationResult:
    name: str
    swap_count: int
    cx_count: int
    depth: int
    optimisation_time: float
    expected_value: float = None
    variance: float = None
    fidelity: float = None
    optimised_circuit: QuantumCircuit = field(repr=False, default=None)

    def complex_to_dict(self, c: complex) -> dict:
        return {"real": c.real, "imag": c.imag}

    def to_dict(self) -> dict:
        
        return {
            "name": self.name,
            "swap_count": self.swap_count,
            "cx_count": self.cx_count,
            "depth": self.depth,
            "expected_value": self.expected_value,
            "variance": self.variance,
            "fidelity": self.fidelity,
            "optimisation_time": self.optimisation_time,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
