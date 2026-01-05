from abc import ABC, abstractmethod
from typing import List
from qiskit import QuantumCircuit


class AlgorithmProvider(ABC):
    """Base class for quantum algorithm input providers."""
    
    @abstractmethod
    def get_circuit(self, **kwargs) -> QuantumCircuit:
        """Generate a quantum circuit for this algorithm."""
        pass
    
    @abstractmethod
    def get_pauli_strings(self, **kwargs) -> List[str]:
        """Generate Pauli strings for this algorithm."""
        pass
    
    @property
    @abstractmethod
    def supports_circuits(self) -> bool:
        """Whether this algorithm provides circuits."""
        pass
    
    @property
    @abstractmethod
    def supports_pauli_strings(self) -> bool:
        """Whether this algorithm provides Pauli strings."""
        pass

    @abstractmethod
    def is_supported_algorithm(self, name: str) -> bool:
        """Check if the given algorithm name is supported by this provider."""
        pass
