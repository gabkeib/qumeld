from calendar import c
from math import exp
from typing import List
from xml.etree.ElementInclude import include
import qiskit
from experiments.run_qiskit import convert_pauli_strings
from stats_utils.estimated_value import calculate_estimated_average_value_and_dispersion
from topologies.topologies import get_topology_by_string
from routing_algorithms.utils import convert_array_to_coupling_map
from qiskit.transpiler.passes import SabreLayout, SabreSwap
from qiskit import QuantumCircuit, visualization, transpile
from qiskit.quantum_info import SparsePauliOp
from experiments.types import CircuitOptimisationResult
from qiskit.transpiler import PassManager
from qiskit.circuit.library import PauliEvolutionGate
from time import time

# Run SABRE algorithm with selected algorithm and quantum computer
def run_sabre_hamiltonian(quantum_computer: List[List[int]], num_qubits: int, pauli_strings: List[str], quantum_algorithm: str) -> CircuitOptimisationResult:
    start_time = time()
    coupling_map = convert_array_to_coupling_map(quantum_computer)

    print(coupling_map.size())

    converted_strings = convert_pauli_strings(pauli_strings)
    print(converted_strings)
    print("AAA", num_qubits)
    hamiltonian = SparsePauliOp.from_sparse_list(converted_strings, num_qubits)
    evo_gate = PauliEvolutionGate(hamiltonian, time=1.0)
    circuit = QuantumCircuit(hamiltonian.num_qubits)
    circuit.append(evo_gate, circuit.qubits)

    # circuit = circuit.decompose()  # You may need multiple decompose() calls
    circuit = transpile(circuit, basis_gates=['cx', 'rz', 'sx', 'x', 'swap'], optimization_level=0)

    qc_swapped = sabre_optimise_circuit(circuit, coupling_map)
    calculatedStatistics = calculate_estimated_average_value_and_dispersion(circuit, qc_swapped, hamiltonian)
    return CircuitOptimisationResult(
        name=quantum_algorithm,
        swap_count=qc_swapped.count_ops().get('swap', 0),
        cx_count=qc_swapped.count_ops().get('cx', 0) + qc_swapped.count_ops().get('swap', 0) * 3,
        depth=qc_swapped.depth(),
        expected_value=calculatedStatistics.expected_value_after,
        variance=calculatedStatistics.variance_after,
        fidelity=calculatedStatistics.fidelity,
        optimisation_time=time() - start_time
    )

def run_sabre_circuit(circuit: QuantumCircuit, quantum_computer: List[List[int]], quantum_algorithm: str) -> CircuitOptimisationResult:
    start_time = time()
    coupling_map = convert_array_to_coupling_map(quantum_computer)

    qc_swapped = sabre_optimise_circuit(circuit, coupling_map)
    calculatedStatistics = calculate_estimated_average_value_and_dispersion(circuit, qc_swapped, None)

    return CircuitOptimisationResult(
        name=quantum_algorithm,
        swap_count=qc_swapped.count_ops().get('swap', 0),
        cx_count=qc_swapped.count_ops().get('cx', 0) + qc_swapped.count_ops().get('swap', 0) * 3,
        depth=qc_swapped.depth(),
        expected_value=calculatedStatistics.expected_value_after,
        variance=calculatedStatistics.variance_after,
        fidelity=calculatedStatistics.fidelity,
        optimisation_time=time() - start_time
    )

def sabre_optimise_circuit(circuit: QuantumCircuit, coupling_map) -> QuantumCircuit:
    seed = 54  # random seed for reproducibility
    swap_trials = 200

    sr_default = SabreSwap(
        coupling_map=coupling_map, heuristic="decay", trials=swap_trials, seed=seed
    )
    sl = SabreLayout(
        coupling_map=coupling_map,
        seed=seed,
        max_iterations=4,
        layout_trials=200,
        swap_trials=200,
    )

    pm_layout = PassManager(sl)
    qc_optimised = pm_layout.run(circuit)

    pw_swap = PassManager(sr_default)
    qc_swapped = pw_swap.run(qc_optimised)

    return qc_swapped
