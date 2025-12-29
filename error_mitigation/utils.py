from error_mitigation.dynamical_decoupling import enable_dynamical_decoupling
from error_mitigation.pauli_twirling import enable_pauli_twirling
from error_mitigation.trex import enable_twirled_readout_error_extinction
from error_mitigation.zero_noise_extrapolation import enable_zero_noise_extrapolation


error_mitigation_algorithms_sampler_or_estimator = {
    "dynamical_decoupling": enable_dynamical_decoupling,
    "trex": enable_twirled_readout_error_extinction,
    "zne": enable_zero_noise_extrapolation,
    "doustra": enable_pauli_twirling
}

def get_error_mitigation_algorithm(name: str):
    if name in error_mitigation_algorithms_sampler_or_estimator:
        return error_mitigation_algorithms_sampler_or_estimator[name]
    else:
        raise ValueError(f"Error mitigation algorithm not found: {name}")
