from abc import ABC, abstractmethod
from typing import List, Optional

from qiskit import QuantumCircuit
from qiskit.providers import BackendV2

from quantum_compiler.core.types import CircuitOptimisationResult


class QubitMapper(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of the mapper."""
        pass

    @property
    @abstractmethod
    def supports_circuit_mapping(self) -> bool:
        """Return whether the mapper supports circuit mapping."""
        pass

    @property
    @abstractmethod
    def supports_raw_pauli_string_mapping(self) -> bool:
        """Return whether the mapper supports Pauli string mapping."""
        pass

    @abstractmethod
    def map_circuit(
        self,
        circuit: QuantumCircuit,
        backend: BackendV2,
        circuit_name: Optional[str] = None,
    ) -> CircuitOptimisationResult:
        """Map the given quantum circuit to the target qubit architecture."""
        pass

    @abstractmethod
    def map_pauli_strings(
        self,
        pauli_strings: List[str],
        backend: BackendV2,
        circuit_name: Optional[str] = None,
    ) -> CircuitOptimisationResult:
        """Map the given Pauli strings to the target qubit architecture."""
        pass
