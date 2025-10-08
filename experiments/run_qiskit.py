from calendar import c
from typing import List
from qiskit.quantum_info import SparsePauliOp
from qiskit import QuantumCircuit
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from sympy import comp
from experiments.types import CircuitOptimisationResult
from time import time
from qiskit.providers import BackendV2, Options
import numpy as np
from qiskit.transpiler import Target, InstructionProperties, PassManager
from qiskit.circuit.library import XGate, SXGate, RZGate, CZGate, ECRGate, PauliEvolutionGate
from qiskit.circuit import Measure, Delay, Parameter, Reset

from routing_algorithms.utils import convert_array_to_coupling_map

class CustomBackend(BackendV2):
    def __init__(self, name: str, graph_list: List[List[int]]):
        super().__init__(name=f"{name} backend")
        graph = convert_array_to_coupling_map(graph_list)
        num_qubits = len(graph_list)
        rng = np.random.default_rng(seed=12345678942)
        rz_props = {}
        x_props = {}
        sx_props = {}
        measure_props = {}
        delay_props = {}
        self._target = Target("Target", num_qubits=num_qubits)
        # Add 1q gates. Globally use virtual rz, x, sx, and measure
        for i in range(num_qubits):
            qarg = (i,)
            rz_props[qarg] = InstructionProperties(error=0.0, duration=0.0)
            x_props[qarg] = InstructionProperties(
                error=rng.uniform(1e-6, 1e-4),
                duration=rng.uniform(1e-8, 9e-7),
            )
            sx_props[qarg] = InstructionProperties(
                error=rng.uniform(1e-6, 1e-4),
                duration=rng.uniform(1e-8, 9e-7),
            )
            measure_props[qarg] = InstructionProperties(
                error=rng.uniform(1e-3, 1e-1),
                duration=rng.uniform(1e-8, 9e-7),
            )
            delay_props[qarg] = None
        self._target.add_instruction(XGate(), x_props)
        self._target.add_instruction(SXGate(), sx_props)
        self._target.add_instruction(RZGate(Parameter("theta")), rz_props)
        self._target.add_instruction(Measure(), measure_props)
        self._target.add_instruction(Reset(), measure_props)
        self._target.add_instruction(Delay(Parameter("t")), delay_props)
        cz_props = {}
        for edge in graph_list:
            cz_props[(edge[0], edge[1])] = InstructionProperties(
                error=rng.uniform(7e-4, 5e-3),
                duration=rng.uniform(1e-8, 9e-7),
            )
        self._target.add_instruction(CZGate(), cz_props)
 
    @property
    def target(self):
        return self._target
 
    @property
    def max_circuits(self):
        return None
 
    @classmethod
    def _default_options(cls):
        return Options(shots=1024)
 
    def run(self, circuit, **kwargs):
        raise NotImplementedError("not implemented")


def get_non_identity_pauli_operator(pauli_string: List[str]):
    return [i for i in range(len(pauli_string)) if pauli_string[i] != 'I']

def convert_pauli_strings(pauli_strings: List[str]):
    return [((s, get_non_identity_pauli_operator(s), 1.0)) for s in pauli_strings]



def run_qiskit_hamiltonian(quantum_computer_backend: CustomBackend, num_qubits: int, pauli_strings: List[str], algorithm_name: str) -> CircuitOptimisationResult:
    time_start = time()
    converted_strings = convert_pauli_strings(pauli_strings)
    hamiltonian = SparsePauliOp.from_sparse_list(converted_strings, num_qubits)

    evo_gate = PauliEvolutionGate(hamiltonian, time=1.0)
    circuit = QuantumCircuit(hamiltonian.num_qubits)
    circuit.append(evo_gate, circuit.qubits)

    compiled_circuit = qiskit_optimise_circuit(circuit, quantum_computer_backend)

    return CircuitOptimisationResult(
        name=algorithm_name,
        swap_count=compiled_circuit.count_ops().get('swap', 0),
        depth=compiled_circuit.depth(),
        optimisation_time=time() - time_start
    )

def run_qiskit_circuit(circuit: QuantumCircuit, backend: CustomBackend, algorithm_name: str) -> CircuitOptimisationResult:
    time_start = time()
    compiled_circuit = qiskit_optimise_circuit(circuit, backend)
    return CircuitOptimisationResult(
        name=algorithm_name,
        swap_count=compiled_circuit.count_ops().get('swap', 0),
        depth=compiled_circuit.depth(),
        optimisation_time=time() - time_start
    )

def qiskit_optimise_circuit(circuit: QuantumCircuit, backend: CustomBackend) -> QuantumCircuit:
    pm: PassManager = generate_preset_pass_manager(optimization_level=3, backend=backend)
    compiled_circuit = pm.run(circuit)
    return compiled_circuit