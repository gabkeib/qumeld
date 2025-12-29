# from topologies.topologies import get_topology_by_string
# from routing_algorithms.utils import convert_array_to_coupling_map
# from routing_algorithms.lightSABRE import sabre_layout
from calendar import c
from dataclasses import asdict
import json
from pathlib import Path
from executing_algorithms.run_circuit import run_circuit_simulation
from experiments import run_qiskit_ai_transpiler, run_rustiq, run_sabre, run_pauliforest
from experiments import run_qiskit
from experiments import run_doustra
from experiments.run_qiskit import CustomBackend
from experiments.types import CircuitOptimisationResult
from quantum_algorithms import hamiltonians, vqe
from topologies.topologies import get_topology_by_string
from typing import List
from qiskit import QuantumCircuit, qasm2

pauli_algorithms = {
    "vqe_demo": hamiltonians.get_demo_pauli_strings,
    "vqe_H2": hamiltonians.get_H2_hamiltonian,
    "qaoa_max_cut": hamiltonians.get_qaoa_max_cut_hamiltonian,
    # "vqe_LiH": hamiltonians.get_LiH_hamiltonian
}

circuits = {
    # "vqe_ansatz": vqe.get_ansatz TODO: find a way to pass entanglement and decompose parameters
}

circuit_optimisation_algorithms = {
    "sabre": run_sabre.run_sabre_hamiltonian,
    "pauliforest": run_pauliforest.run_pauliforest_hamiltonian,
    "qiskit": run_qiskit.run_qiskit_hamiltonian,
    "doustra": run_doustra.run_doustra_hamiltonian,
    "qiskit_ai": run_qiskit_ai_transpiler.run_qiskit_ai_hamiltonian,
    "rustiq": run_rustiq.run_rustiq_hamiltonian,
}

def get_pauli_strings_by_algorithm(name: str, num_qubits: int) -> List[str]:
    if name in pauli_algorithms:
        if name == "qaoa_max_cut":
            # Example graph for max cut
            graph = [
                [0, 1, 1, 0, 1],
                [1, 0, 1, 0, 0],
                [1, 1, 0, 1, 0],
                [0, 0, 1, 0, 1],
                [1, 0, 0, 1, 0]
            ]
            return pauli_algorithms[name](graph)
        if name == "vqe_ansatz":
            return pauli_algorithms[name](num_qubits, entanglement="linear", decompose=True)
        return pauli_algorithms[name]()
    else:
        raise ValueError(f"Algorithm not found: {name}")

def get_circuit_by_algorithm(name: str, num_qubits: int) -> QuantumCircuit:
    if name in circuits:
        if name == "vqe_ansatz":
            return circuits[name](num_qubits, entanglement="linear")
        return circuits[name]()
    raise ValueError(f"Circuit not found: {name}")

def write_to_file(data: CircuitOptimisationResult, path: str):
    print(asdict(data))
    with open(path, "w") as f:
       json.dump(data.to_dict(), f, indent=4)

# when using pauli strings, please fill then with ones or show indexes where we have non I indexes
def run_experiments(
    quantum_computer: str,
    quantum_algorithm: str,
    circuit_optimisation_algorithm: str,
    path_to_save: str,
    simulate_circuit: bool=False,
    error_mitigation_techniques: List[str]=[]
):
    # run_sabre.run_sabre(quantum_computer)
    # run_pauliforest_old.run_pauliforest(quantum_computer)
    Path(path_to_save).mkdir(parents=True, exist_ok=True)

    topology, qubits = get_topology_by_string(quantum_computer)
    print(len(topology))

    print("HEREEEEEE", )

    if quantum_algorithm in circuits:
        circuit = get_circuit_by_algorithm(quantum_algorithm, qubits)
        res = None
        if circuit_optimisation_algorithm == "qiskit":
            custom_backend = CustomBackend(quantum_computer, topology)
            res = run_qiskit.run_qiskit_circuit(circuit=circuit, backend=custom_backend, algorithm_name=quantum_algorithm)
        elif circuit_optimisation_algorithm == "qiskit_ai":
            custom_backend = CustomBackend(quantum_computer, topology)
            res = run_qiskit_ai_transpiler.run_qiskit_ai_circuit(circuit=circuit, backend=custom_backend, algorithm_name=quantum_algorithm)
        elif circuit_optimisation_algorithm == "rustiq":
            custom_backend = CustomBackend(quantum_computer, topology)
            res = run_rustiq.run_rustiq_circuit(circuit=circuit, backend=custom_backend, algorithm_name=quantum_algorithm)
        elif circuit_optimisation_algorithm == "doustra":
            res = run_doustra.run_doustra_circuit(circuit=circuit, quantum_computer=topology, quantum_computer_name=quantum_computer, quantum_algorithm=quantum_algorithm)
        elif circuit_optimisation_algorithm == "pauliforest":
            res = run_pauliforest.run_pauliforest_circuit(circuit=circuit,quantum_computer=quantum_computer, quantum_computer_name=quantum_computer)
        else:
            algorithm_exec = circuit_optimisation_algorithms[circuit_optimisation_algorithm]
            res = algorithm_exec(topology, num_qubits=qubits, pauli_strings=[], quantum_algorithm=quantum_algorithm)

        if simulate_circuit:
            result = run_circuit_simulation(quantum_computer, error_mitigation_techniques)
            print(result)

        if res is not None:
            write_to_file(res, f"./{path_to_save}/{circuit_optimisation_algorithm}.json")
        return

    elif quantum_algorithm in pauli_algorithms:
        pauli_strings = get_pauli_strings_by_algorithm(quantum_algorithm, qubits)
        res = None
        if circuit_optimisation_algorithm == "qiskit" :
            custom_backend = CustomBackend(quantum_computer, topology)
            res = run_qiskit.run_qiskit_hamiltonian(quantum_computer_backend=custom_backend, num_qubits=qubits, pauli_strings=pauli_strings, algorithm_name=quantum_algorithm)
        elif circuit_optimisation_algorithm == "qiskit_ai":
            custom_backend = CustomBackend(quantum_computer, topology)
            res = run_qiskit_ai_transpiler.run_qiskit_ai_hamiltonian(quantum_computer_backend=custom_backend, num_qubits=qubits, pauli_strings=pauli_strings, algorithm_name=quantum_algorithm)
        elif circuit_optimisation_algorithm == "rustiq":
            custom_backend = CustomBackend(quantum_computer, topology)
            res = run_rustiq.run_rustiq_hamiltonian(quantum_computer_backend=custom_backend, num_qubits=qubits, pauli_strings=pauli_strings, algorithm_name=quantum_algorithm)
        elif circuit_optimisation_algorithm == "doustra":
            res = run_doustra.run_doustra_hamiltonian(quantum_computer=topology, quantum_computer_name=quantum_computer, num_qubits=qubits, pauli_strings=pauli_strings, quantum_algorithm=quantum_algorithm)
        elif circuit_optimisation_algorithm == "pauliforest":
            res = run_pauliforest.run_pauliforest_hamiltonian(quantum_computer=quantum_computer, num_qubits=qubits, pauli_strings=pauli_strings, quantum_algorithm=quantum_algorithm)
        else:
            algorithm_exec = circuit_optimisation_algorithms[circuit_optimisation_algorithm]
            res = algorithm_exec(topology, num_qubits=qubits, pauli_strings=pauli_strings, quantum_algorithm=quantum_algorithm)

        if simulate_circuit:
            result = run_circuit_simulation(quantum_computer, error_mitigation_techniques)
            print(result)

        if res is not None:
            write_to_file(res, f"./{path_to_save}/{circuit_optimisation_algorithm}.json")
    else:
        print("Algorithm not found: ", quantum_algorithm)
        return

def run_circuit_optimisation(
        circuit : QuantumCircuit,
        quantum_computer: str,
        circuit_optimisation_algorithm: str,
        path_to_save: str
):
    Path(path_to_save).mkdir(parents=True, exist_ok=True)

    topology, qubits = get_topology_by_string(quantum_computer)
    print(len(topology))

    res = None
    if circuit_optimisation_algorithm == "qiskit":
        custom_backend = CustomBackend(quantum_computer, topology)
        res = run_qiskit.run_qiskit_circuit(circuit=circuit, backend=custom_backend, algorithm_name='custom_circuit')
    elif circuit_optimisation_algorithm == "qiskit_ai":
        custom_backend = CustomBackend(quantum_computer, topology)
        res = run_qiskit_ai_transpiler.run_qiskit_ai_circuit(circuit=circuit, backend=custom_backend, algorithm_name='custom_circuit')
    elif circuit_optimisation_algorithm == "rustiq":
        custom_backend = CustomBackend(quantum_computer, topology)
        res = run_rustiq.run_rustiq_circuit(circuit=circuit, backend=custom_backend, algorithm_name='custom_circuit')
    elif circuit_optimisation_algorithm == "doustra":
        res = run_doustra.run_doustra_circuit(circuit=circuit,quantum_computer=topology, quantum_computer_name=quantum_computer, algorithm_name='custom_circuit')
    elif circuit_optimisation_algorithm == "pauliforest":
        res = run_pauliforest.run_pauliforest_circuit(quantum_computer=quantum_computer, num_qubits=qubits)
    else:
        print("Not found optimiser: ", circuit_optimisation_algorithm)
        return 

    if res.optimised_circuit is not None:
        write_circuit_to_file(res.optimised_circuit, f"./{path_to_save}/{circuit_optimisation_algorithm}.qasm")
    else:
        print("No compiled circuit found.")

def write_circuit_to_file(circuit: QuantumCircuit, path: str):
    qasm2.dump(circuit.decompose(), open(path, "w"))
