import qiskit
from qiskit_ibm_runtime import EstimatorV2 as Estimator, SamplerV2 as Sampler

def enable_twirled_readout_error_extinction(processor: Estimator | Sampler):
    processor.options.resilience.measure_mitigation = True
    processor.options.resilience.measure_noise_learning.num_randomizations = 32
    processor.options.resilience.measure_noise_learning.shots_per_randomization = 10
    return processor

