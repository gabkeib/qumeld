import qiskit
from mitiq import zne
from qiskit_ibm_runtime import EstimatorV2 as Estimator, SamplerV2 as Sampler

from quantum_compiler.error_mitigation.base_technique import ErrorMitigationTechnique


class ZeroNoiseExtrapolation(ErrorMitigationTechnique):
    """Zero Noise Extrapolation error mitigation technique."""

    @property
    def name(self) -> str:
        return "ZeroNoiseExtrapolation"

    def apply_on_circuit(
        self, circuit: qiskit.QuantumCircuit, backend
    ) -> qiskit.QuantumCircuit:
        """Apply Zero Noise Extrapolation to the given circuit.

        Args:
            circuit (QuantumCircuit): The quantum circuit to which Zero Noise Extrapolation will be applied.
            backend: The backend on which the circuit will be executed.
        Returns:
            QuantumCircuit: The modified quantum circuit with Zero Noise Extrapolation applied.
        """
        return zne.execute_with_zne(
            circuit,
            zne.scaling.fold_gates_at_random,
            num_folds=2,
            scale_factors=[1, 3, 5],
            extrapolator=zne.extrapolators.ExponentialExtrapolator(),
        )

    def apply_on_estimator(self, estimator: Estimator) -> Estimator:
        """Apply Zero Noise Extrapolation to the given Estimator.

        Args:
            estimator (Estimator): The Estimator to which Zero Noise Extrapolation will be applied.
        """
        estimator.options.resilience.zne_mitigation = True
        estimator.options.resilience.zne.noise_factors = (1, 3, 5)
        estimator.options.resilience.zne.extrapolator = "exponential"
        return estimator
