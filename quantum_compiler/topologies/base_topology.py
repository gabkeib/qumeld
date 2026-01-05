from abc import ABC, abstractmethod
from typing import List

class Topology(ABC):
    """
    Abstract base class for defining quantum computer topologies.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def num_qubits(self) -> int:
        pass

    @abstractmethod
    def get_coupling_map(self) -> List[List[int]]:
        pass

    def get_basis_gates(self) -> List[str]:
        """Optional: Define specific basis gates. Defaults to standard set."""
        return ["cx", "id", "rz", "sx", "x", "swap"]
