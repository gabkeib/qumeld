import qiskit
from mitiq import zne
from qiskit_ibm_runtime import EstimatorV2 as Estimator, SamplerV2 as Sampler

def enable_zero_noise_extrapolation(processor: Estimator | Sampler):
    processor.options.resilience.zne_mitigation = True
    processor.options.resilience.zne.noise_factors = (1, 3, 5)
    processor.options.resilience.zne.extrapolator = "exponential"
    return processor


def execute_with_mitiq_zero_noise_extrapolation(circuit):
    return zne.execute_with_zne(circuit, zne.scaling.fold_gates_at_random, num_folds=2, scale_factors=[1, 3, 5], extrapolator=zne.extrapolators.ExponentialExtrapolator())
