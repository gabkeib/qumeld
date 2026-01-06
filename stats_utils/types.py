from dataclasses import dataclass


@dataclass
class CircuitOptimisationStatistics:
    variance_before: float = None
    expected_value_before: float = None
    fidelity: float = None
    expected_value_after: float = None
    variance_after: float = None
