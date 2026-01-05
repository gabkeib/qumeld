from abc import ABC, abstractmethod

from qiskit import QuantumCircuit
from qiskit.providers import BackendV2  
from qiskit_ibm_runtime import EstimatorV2 as Estimator, SamplerV2 as Sampler


class ErrorMitigationTechnique(ABC):
    """Base class for error mitigation techniques."""


    @abstractmethod
    def apply_on_circuit(self, circuit: QuantumCircuit, backend: BackendV2) -> QuantumCircuit:
        """Apply the error mitigation technique to the given circuit.

        Args:
            circuit (QuantumCircuit): The quantum circuit to which the error mitigation technique will be applied.
            backend (BackendV2): The backend on which the circuit will be executed.
        Returns:
            QuantumCircuit: The modified quantum circuit with the error mitigation technique applied.
        """
        pass

    def apply_on_estimator(self, estimator: Estimator) -> Estimator:
        """Apply the error mitigation technique to the given Estimator.

        Args:
            estimator (Estimator): The Estimator to which the error mitigation technique will be applied.
        """
        pass
