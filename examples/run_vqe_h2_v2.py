from qiskit import QuantumCircuit, generate_preset_pass_manager
from qiskit.circuit.library import efficient_su2
from qiskit_ibm_runtime.fake_provider import FakeNairobiV2
import numpy as np
from qiskit_aer import AerSimulator
from qiskit.primitives import BackendEstimatorV2
from scipy.optimize import minimize

from quantum_algorithms.registry import AlgorithmRegistry


def get_ansatz(num_qubits: int, entanglement: str, decompose: bool = False) -> QuantumCircuit:
    circ = efficient_su2(num_qubits=num_qubits, entanglement=entanglement)
    if decompose:
        circ = circ.decompose()
    return circ

def cost_func(params: list, ansatz: QuantumCircuit, H: QuantumCircuit, estimator):
    pub = (ansatz, [H], [params])
    result = estimator.run(pubs=[pub]).result()
    energy = result[0].data.evs[0]
    return energy

def run_vqe():
    backend = FakeNairobiV2()
    num_qubits = backend.num_qubits

    ansatz = get_ansatz(num_qubits=num_qubits, entanglement="linear")
    x0 = 2 * np.pi * np.random.random(ansatz.num_parameters)

    algorithm_registry = AlgorithmRegistry()
    
    hamiltonian: QuantumCircuit = algorithm_registry.get_circuit(name="h2")

    backend_sim = AerSimulator.from_backend(backend)
    estimator = BackendEstimatorV2(backend=backend_sim)

    target = backend.target
    pm = generate_preset_pass_manager(target=target, optimization_level=3)
    
    ansatz_isa = pm.run(ansatz)
    hamiltonian_isa = hamiltonian.apply_layout(ansatz_isa.layout)

    res = minimize(
        cost_func,
        x0,
        args=(ansatz_isa, hamiltonian_isa, estimator),
        method="cobyla",
        options={"maxiter": 10, "disp": True},
    )

    print(res)

if __name__ == "__main__":
    run_vqe()
