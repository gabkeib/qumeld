from platform import processor
import qiskit
from qiskit_ibm_runtime import EstimatorV2 as Estimator, SamplerV2 as Sampler

from quantum_compiler.error_mitigation.base_technique import ErrorMitigationTechnique

class Trex(ErrorMitigationTechnique):
    """T-REx error mitigation technique."""

    @property
    def name(self) -> str:
        return "Trex"

    def apply_on_circuit(self, circuit: qiskit.QuantumCircuit, backend) -> qiskit.QuantumCircuit:
        pass

    def apply_on_estimator(self, estimator: Estimator) -> Estimator:
        """Apply T-REx to the given Estimator.

        Args:
            estimator (Estimator): The Estimator to which T-REx will be applied.
        """
        estimator.options.resilience.measure_mitigation = True
        estimator.options.resilience.measure_noise_learning.num_randomizations = 32
        estimator.options.resilience.measure_noise_learning.shots_per_randomization = 10
        return estimator

