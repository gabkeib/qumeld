from dataclasses import dataclass, field
import json
from typing import List, Optional
from qiskit import QuantumCircuit

@dataclass
class CircuitOptimisationResult:
    name: str
    swap_count: int
    cx_count: int
    depth: int
    optimisation_time: float
    optimised_circuit: QuantumCircuit = field(repr=False, default=None)
    expected_value: float = None
    variance: float = None
    fidelity: float = None
    failed: bool = False
    failure_reason: str = None
    mapper: str = None

    @classmethod
    def create_failed(
        cls,
        reason: str,
        name: str = "failed",
        original_circuit: Optional[QuantumCircuit] = None
    ) -> 'CircuitOptimisationResult':
        """Create a failed optimization result."""
        return cls(
            name=name,
            swap_count=-1,
            cx_count=-1,
            depth=-1,
            optimisation_time=0.0,
            failed=True,
            failure_reason=reason,
            optimised_circuit=original_circuit
        )

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
            "failed": self.failed,
            "failure_reason": self.failure_reason,
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
