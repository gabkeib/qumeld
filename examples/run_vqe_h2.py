import numpy as np
from scipy.optimize import minimize
from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp
from qiskit.providers import BackendV2

from quantum_compiler.backends.factory import BackendFactory
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.mappers.base_mapper import QubitMapper
from quantum_algorithms.registry import AlgorithmRegistry


def create_vqe_ansatz(
    num_qubits: int, num_layers: int = 2
) -> tuple[QuantumCircuit, ParameterVector]:
    """
    Create a hardware-efficient ansatz for VQE.

    Args:
        num_qubits: Number of qubits
        num_layers: Number of repetition layers

    Returns:
        Tuple of (circuit, parameters)
    """
    params = ParameterVector("θ", num_qubits * num_layers * 2)
    qc = QuantumCircuit(num_qubits)

    param_idx = 0
    for layer in range(num_layers):
        # Rotation layer
        for i in range(num_qubits):
            qc.ry(params[param_idx], i)
            param_idx += 1
            qc.rz(params[param_idx], i)
            param_idx += 1

        # Entanglement layer
        for i in range(num_qubits - 1):
            qc.cx(i, i + 1)
        if num_qubits > 2:
            qc.cx(num_qubits - 1, 0)

    return qc, params


class VQECostFunction:
    """Cost function for VQE optimization"""

    def __init__(
        self,
        hamiltonian: QuantumCircuit,
        num_qubits: int,
        num_layers: int,
        backend: BackendV2,
        qubit_mapper: QubitMapper,
    ):
        self.hamiltonian = hamiltonian
        self.num_qubits = num_qubits
        self.num_layers = num_layers
        self.backend = backend
        self.qubit_mapper = qubit_mapper
        self.estimator = StatevectorEstimator()
        self.iteration = 0
        self.energy_history = []

        # Create ansatz once
        self.ansatz, self.params = create_vqe_ansatz(num_qubits, num_layers)

    def __call__(self, params_values: np.ndarray) -> float:
        """Compute energy expectation value for given parameters"""

        param_dict = {self.params[i]: params_values[i] for i in range(len(self.params))}
        bound_circuit = self.ansatz.assign_parameters(param_dict)

        mapped_result = self.qubit_mapper.map_circuit(bound_circuit, self.backend)
        mapped_circuit = mapped_result.optimised_circuit

        # Expanding Hamiltonian to match mapped circuit size
        expanded_hamiltonian = self._expand_hamiltonian(mapped_circuit.num_qubits)

        job = self.estimator.run([(mapped_circuit, expanded_hamiltonian)])
        result = job.result()
        energy = result[0].data.evs

        self.iteration += 1
        self.energy_history.append(float(energy))

        if self.iteration % 5 == 0:
            print(f"Iteration {self.iteration}: Energy = {energy:.6f} Ha")

        return float(energy)

    def _expand_hamiltonian(self, num_qubits_mapped: int) -> SparsePauliOp:
        """Expand Hamiltonian to match mapped circuit size by padding with identity"""
        if num_qubits_mapped == self.num_qubits:
            return self.hamiltonian

        expanded_paulis = []
        expanded_coeffs = []

        padding = "I" * (num_qubits_mapped - self.num_qubits)

        for pauli, coeff in zip(self.hamiltonian.paulis, self.hamiltonian.coeffs):
            expanded_pauli = pauli.to_label() + padding
            expanded_paulis.append(expanded_pauli)
            expanded_coeffs.append(coeff)

        return SparsePauliOp(expanded_paulis, coeffs=expanded_coeffs)


def run_vqe_h2():
    algorithm_registry = AlgorithmRegistry()

    available = algorithm_registry.list_algorithms()
    print(f"Available algorithms: {available}")

    h2_circuit = algorithm_registry.get_circuit(name="h2")

    if hasattr(h2_circuit, "metadata") and "observable" in h2_circuit.metadata:
        hamiltonian = h2_circuit.metadata["observable"]
    elif hasattr(h2_circuit, "observables"):
        hamiltonian = h2_circuit.observables[0]
    else:
        # Decompose circuit to extract Hamiltonian
        from qiskit.quantum_info import Operator

        op = Operator(h2_circuit)
        hamiltonian = SparsePauliOp.from_operator(op)

    real_coeffs = np.real(hamiltonian.coeffs)
    hamiltonian = SparsePauliOp(hamiltonian.paulis, coeffs=real_coeffs)

    num_qubits = hamiltonian.num_qubits

    backend_factory = BackendFactory()
    backend = backend_factory.get_backend("rigetti_novera_q9")
    print(f"Backend: {backend.name} ({backend.num_qubits} qubits)")

    mapper_registry = MapperRegistry()
    qubit_mapper = mapper_registry.get_mapper("lightSABRE")
    print(f"Mapper: {qubit_mapper.name}")

    num_layers = 2
    num_params = num_qubits * num_layers * 2
    print(f"Ansatz layers: {num_layers}")
    print(f"Number of parameters: {num_params}")

    np.random.seed(42)
    initial_params = np.random.randn(num_params) * 0.1

    cost_func = VQECostFunction(
        hamiltonian=hamiltonian,
        num_qubits=num_qubits,
        num_layers=num_layers,
        backend=backend,
        qubit_mapper=qubit_mapper,
    )

    result = minimize(
        cost_func,
        initial_params,
        method="COBYLA",
        options={"maxiter": 100, "rhobeg": 0.5, "tol": 1e-6, "disp": False},
    )

    print(f"Optimization success: {result.success}")
    print(f"Number of iterations: {result.nfev}")
    print(f"Final ground state energy: {result.fun:.8f} Ha")
    print(f"Optimal parameters (first 5): {result.x[:5]}")

    print("Energy convergence:")
    energies = cost_func.energy_history
    for i in [0, len(energies) // 4, len(energies) // 2, 3 * len(energies) // 4, -1]:
        if i < len(energies):
            print(f"  Iteration {i + 1:3d}: {energies[i]:.8f} Ha")

    exact_energy = -1.137  # This is approximate state energy at equilibrium
    print(f"\nExact ground state energy: {exact_energy:.8f} Ha (approximate)")
    print(f"VQE error: {abs(result.fun - exact_energy):.8f} Ha")

    return result, cost_func


if __name__ == "__main__":
    optimal_result, vqe_cost = run_vqe_h2()
