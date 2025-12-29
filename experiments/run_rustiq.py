from calendar import c
from readline import backend
from typing import List
from qiskit.quantum_info import SparsePauliOp
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from sympy import comp
from experiments.run_qiskit import convert_pauli_strings
from experiments.types import CircuitOptimisationResult
from time import time
from qiskit.providers import BackendV2, Options
import numpy as np
from qiskit.transpiler import Target, InstructionProperties, PassManager
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.transpiler.passes.synthesis.high_level_synthesis import HLSConfig

from routing_algorithms.qiskit_ai.run_experiments import CustomBackend
from stats_utils.estimated_value import calculate_estimated_average_value_and_dispersion

def run_rustiq_hamiltonian(quantum_computer_backend: CustomBackend, num_qubits: int, pauli_strings: List[str], algorithm_name: str) -> CircuitOptimisationResult:
    time_start = time()
    converted_strings = convert_pauli_strings(pauli_strings)
    hamiltonian = SparsePauliOp.from_sparse_list(converted_strings, num_qubits)

    evo_gate = PauliEvolutionGate(hamiltonian, time=1.0)
    circuit = QuantumCircuit(hamiltonian.num_qubits)
    circuit.append(evo_gate, circuit.qubits)

    compiled_circuit = rustiq_optimise_circuit(circuit, quantum_computer_backend)

    calculated_statistics = calculate_estimated_average_value_and_dispersion(circuit, compiled_circuit, hamiltonian)
    return CircuitOptimisationResult(
        name=algorithm_name,
        swap_count=compiled_circuit.count_ops().get('swap', 0),
        cx_count=compiled_circuit.count_ops().get('cx', 0) + compiled_circuit.count_ops().get('swap', 0) * 3,
        depth=compiled_circuit.depth(),
        expected_value=calculated_statistics.expected_value_after,
        variance=calculated_statistics.variance_after,
        fidelity=calculated_statistics.fidelity,
        optimisation_time=time() - time_start
    )

def run_rustiq_circuit(circuit: QuantumCircuit, backend: CustomBackend, algorithm_name: str) -> CircuitOptimisationResult:
    time_start = time()
    compiled_circuit = rustiq_optimise_circuit(circuit, backend)
    calculated_statistics = calculate_estimated_average_value_and_dispersion(circuit, compiled_circuit, None)
    return CircuitOptimisationResult(
        name=algorithm_name,
        swap_count=compiled_circuit.count_ops().get('swap', 0),
        cx_count=compiled_circuit.count_ops().get('cx', 0) + compiled_circuit.count_ops().get('swap', 0) * 3,
        depth=compiled_circuit.depth(),
        optimisation_time=time() - time_start,
        expected_value=calculated_statistics.expected_value_after,
        variance=calculated_statistics.variance_after,
        fidelity=calculated_statistics.fidelity,
        optimised_circuit=compiled_circuit
    )

def rustiq_optimise_circuit(circuit: QuantumCircuit, backend: CustomBackend) -> QuantumCircuit:
    hls_config = HLSConfig(
        PauliEvolution=[
            (
                "rustiq",
                {
                    "nshuffles": 400,
                    "upto_phase": True,
                    "fix_clifford": True,
                    "preserve_order": False,
                    "metric": "depth",
                },
            )
        ]
    )
    pm: PassManager = generate_preset_pass_manager(
        optimization_level=3,
        backend=backend,
        hls_config=hls_config,
    )
    compiled_circuit = pm.run(circuit)
    return compiled_circuit
