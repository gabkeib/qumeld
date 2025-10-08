# from topologies.topologies import get_topology_by_string
# from routing_algorithms.utils import convert_array_to_coupling_map
# from routing_algorithms.lightSABRE import sabre_layout
from dataclasses import asdict
import json
from pathlib import Path
from experiments import run_sabre, run_pauliforest
from experiments import run_qiskit
from experiments import run_doustra
from experiments.run_qiskit import CustomBackend
from experiments.types import CircuitOptimisationResult
from quantum_algorithms import hamiltonians, vqe
from topologies.topologies import get_topology_by_string

algorithms = {
    "vqe_demo": hamiltonians.get_demo_pauli_strings,
    "vqe_H2": hamiltonians.get_H2_hamiltonian,
    "vqe_ansatz": vqe.get_ansatz
    # "vqe_LiH": hamiltonians.get_LiH_hamiltonian
}

circuit_optimisation_algorithms = {
    "sabre": run_sabre.run_sabre_hamiltonian,
    "pauliforest": run_pauliforest.run_pauliforest_hamiltonian,
    "qiskit": run_qiskit.run_qiskit_hamiltonian,
    "doustra": run_doustra.run_doustra_hamiltonian
}

def get_algorithm_circuit(name: str):
    if name in algorithms:
        return algorithms[name]()
    else:
        raise ValueError(f"Algorithm not found: {name}")

def write_to_file(data: CircuitOptimisationResult, path: str):
    with open(path, "w") as f:
       json.dump(asdict(data), f, indent=4)

# when using pauli strings, please fill then with ones or show indexes where we have non I indexes
def run_experiments_paulistrings(
    quantum_computer: str,
    quantum_algorithm: str,
    circuit_optimisation_algorithm: str,
    path_to_save: str
):
    # run_sabre.run_sabre(quantum_computer)
    # run_pauliforest_old.run_pauliforest(quantum_computer)
    Path(path_to_save).mkdir(parents=True, exist_ok=True)

    topology, qubits = get_topology_by_string(quantum_computer)
    print(len(topology))

    pauli_strings = get_algorithm_circuit(quantum_algorithm)

    res = None
    if circuit_optimisation_algorithm == "qiskit":
        custom_backend = CustomBackend(quantum_computer, topology)
        res = run_qiskit.run_qiskit_hamiltonian(quantum_computer_backend=custom_backend, num_qubits=qubits, pauli_strings=pauli_strings, algorithm_name=quantum_algorithm)
    elif circuit_optimisation_algorithm == "doustra":
        res = run_doustra.run_doustra_hamiltonian(quantum_computer=topology, quantum_computer_name=quantum_computer, num_qubits=qubits, pauli_strings=pauli_strings, quantum_algorithm=quantum_algorithm)
    else:
        algorithm_exec = circuit_optimisation_algorithms[circuit_optimisation_algorithm]
        res = algorithm_exec(topology, num_qubits=qubits, pauli_strings=pauli_strings, quantum_algorithm=quantum_algorithm)

    if res is not None:
        write_to_file(res, f"./{path_to_save}/{circuit_optimisation_algorithm}.json")
