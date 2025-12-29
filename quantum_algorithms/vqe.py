import ast
from typing import List
from qiskit import generate_preset_pass_manager
from qiskit.circuit.library import efficient_su2
from qiskit.quantum_info import SparsePauliOp
import numpy as np
from qiskit_aer import AerSimulator
from scipy.optimize import minimize
 
# Import an estimator, this time from qiskit (we will import from Runtime for real hardware)
from qiskit.primitives import BackendEstimatorV2


def get_ansatz(num_qubits, entanglement, decompose=False):
    circ = efficient_su2(num_qubits=num_qubits, entanglement=entanglement)
    if decompose:
        circ = circ.decompose()
    return circ

def cost_func(params, ansatz, H, estimator):
    pub = (ansatz, [H], [params])
    result = estimator.run(pubs=[pub]).result()
    energy = result[0].data.evs[0]
    return energy


# example vqe algorithm. TODO: make it variable
def run_vqe(hamiltonian, num_qubits, backend):
    ansatz = get_ansatz(num_qubits=num_qubits, entanglement="linear")
    x0 = 2 * np.pi * np.random.random(ansatz.num_parameters)

    backend_sim = AerSimulator.from_backend(backend)
    estimator = BackendEstimatorV2(backend=backend_sim)

    target = backend.target
    pm = generate_preset_pass_manager(target=target, optimization_level=3)
    
    ansatz_isa = pm.run(ansatz)
    hamiltonian_isa = hamiltonian.apply_layout(ansatz_isa.layout)

    res = minimize(
        cost_func,
        x0,
        args=(ansatz_isa, hamiltonian, estimator),
        method="cobyla",
        options={"maxiter": 10, "disp": True},
    )
    return ansatz
