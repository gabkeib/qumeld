import qiskit
from qiskit_ibm_runtime import EstimatorV2 as Estimator, SamplerV2 as Sampler

from quantum_compiler.error_mitigation.base_technique import ErrorMitigationTechnique

class PauliTwirling(ErrorMitigationTechnique):
    """Pauli Twirling error mitigation technique."""

    @property
    def name(self) -> str:
        return "PauliTwirling"

    def apply_on_circuit(self, circuit: qiskit.QuantumCircuit, backend) -> qiskit.QuantumCircuit:
        pass

    def apply_on_estimator(self, estimator: Estimator) -> Estimator:
        """Apply Pauli Twirling to the given Estimator  .

        Args:
            estimator (Estimator): The Estimator to which Pauli Twirling will be applied.
        """
        estimator.options.twirling.enable_gates = True
        estimator.options.twirling.num_randomizations = 32
        estimator.options.twirling.shots_per_randomization = 100
        return estimator


