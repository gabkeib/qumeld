import qiskit
from qiskit_ibm_runtime import QiskitRuntimeService, EstimatorV2 as Estimator, SamplerV2 as Sampler
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes.scheduling import (
    ALAPScheduleAnalysis,
    PadDynamicalDecoupling,
)

def enable_dynamical_decoupling(processor: Estimator | Sampler):
    processor.options.dynamical_decoupling.enable = True
    processor.options.dynamical_decoupling.sequence_type = "XpXm"
    return processor

def dynamic_decoupling_pass_manager(target, dd_sequence="XY4"):
    dd_pm = PassManager(
    [
        ALAPScheduleAnalysis(target=target),
        PadDynamicalDecoupling(target=target, dd_sequence=dd_sequence),
    ]
)