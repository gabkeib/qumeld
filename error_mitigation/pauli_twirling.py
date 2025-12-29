import qiskit
from qiskit_ibm_runtime import EstimatorV2 as Estimator, SamplerV2 as Sampler

def enable_pauli_twirling(processor: Estimator | Sampler):
    processor.options.twirling.enable_gates = True
    processor.options.twirling.num_randomizations = 32
    processor.options.twirling.shots_per_randomization = 100
    return processor

