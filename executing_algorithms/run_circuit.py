from qiskit import QuantumCircuit
from typing import List
from qiskit_ibm_runtime import EstimatorV2 as Estimator
from error_mitigation.utils import get_error_mitigation_algorithm 

def run_circuit_simulation(
        circuit: QuantumCircuit, 
        error_mitigation_techniques: List[str],
    ):
    estimator = Estimator()
    for technique in error_mitigation_techniques:
        algorithm = get_error_mitigation_algorithm(technique)
        estimator = algorithm(estimator)
    
    job = estimator.run(circuits=[circuit], shots=1024)
    result = job.result()
    return result