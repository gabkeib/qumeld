from dataclasses import dataclass

@dataclass
class CircuitOptimisationResult:
    name: str
    swap_count: int
    depth: int
    optimisation_time: float