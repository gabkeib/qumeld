from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator, SamplerV2 as Sampler
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes.scheduling import (
    ALAPScheduleAnalysis,
    PadDynamicalDecoupling,
)
from qiskit.providers import BackendV2

from quantum_compiler.error_mitigation.base_technique import ErrorMitigationTechnique

class DynamicalDecoupling(ErrorMitigationTechnique):
    """Dynamical Decoupling error mitigation technique."""

    @property
    def name(self) -> str:
        return "DynamicalDecoupling"

    def apply_on_circuit(self, circuit: QuantumCircuit, backend: BackendV2) -> QuantumCircuit:
        """Apply Dynamical Decoupling to the given circuit.

        Args:
            circuit (QuantumCircuit): The quantum circuit to which Dynamical Decoupling will be applied.
            backend (BackendV2): The backend on which the circuit will be executed.
        Returns:
            QuantumCircuit: The modified quantum circuit with Dynamical Decoupling applied.
        """
        
        dd_pm = PassManager(
            [
                ALAPScheduleAnalysis(target=backend.target),
                PadDynamicalDecoupling(target=backend.target, dd_sequence=backend.target),
            ]
        )
        circuit = dd_pm.run(circuit)
        return circuit
    
    def apply_on_estimator(self, estimator: Estimator) -> Estimator:
        """Apply Dynamical Decoupling to the given Estimator.

        Args:
            estimator (Estimator): The Estimator to which Dynamical Decoupling will be applied.
        """
        estimator.options.dynamical_decoupling.enable = True
        estimator.options.dynamical_decoupling.sequence_type = "XpXm"
        return estimator

