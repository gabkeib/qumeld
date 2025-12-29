from calendar import c
from readline import backend
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
from qiskit.circuit.library import XGate, SXGate, RZGate, CZGate, CXGate, PauliEvolutionGate, SwapGate
from qiskit.circuit import Measure, Delay, Parameter, Reset
from quantum_algorithms import hamiltonians, qaoa, vqe
from scipy.optimize import minimize
from qiskit_ibm_runtime import Session, EstimatorV2 as Estimator
from qiskit_aer import AerSimulator
from qiskit.primitives import BackendEstimatorV2

from routing_algorithms.utils import convert_array_to_coupling_map
import statistics

from stats_utils.estimated_value import calculate_estimated_average_value_and_dispersion

class CustomBackend(BackendV2):
    def __init__(self, name: str, graph_list: List[List[int]]):
        super().__init__(name=f"{name} backend")
        graph = convert_array_to_coupling_map(graph_list)
        edge_properties = {
            (edge[0], edge[1]): None for edge in graph
        }
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
        self._target.add_instruction(SwapGate(), edge_properties)  # add swap with no properties
        self._target.add_instruction(CXGate(), edge_properties)
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

def run_qiskit_circuit(circuit: QuantumCircuit, backend: CustomBackend, algorithm_name: str) -> CircuitOptimisationResult:
    time_start = time()
    compiled_circuit = qiskit_optimise_circuit(circuit, backend)
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

def qiskit_optimise_circuit(circuit: QuantumCircuit, backend: CustomBackend) -> QuantumCircuit:
    pm: PassManager = generate_preset_pass_manager(optimization_level=3, backend=backend)
    compiled_circuit = pm.run(circuit)
    return compiled_circuit

def cost_func_estimator(params, ansatz, hamiltonian, estimator):
    # transform the observable defined on virtual qubits to
    # an observable defined on all physical qubits
    isa_hamiltonian = hamiltonian.apply_layout(ansatz.layout)
 
    pub = (ansatz, isa_hamiltonian, params)
    job = estimator.run([pub])
 
    results = job.result()[0]
    cost = results.data.evs
 
    objective_func_vals.append(cost)
 
    return cost

def run_qiskit_qaoa_max_cut(quantum_computer_backend: CustomBackend, num_qubits: int, graph: List[List[int]]) -> CircuitOptimisationResult:
    time_start = time()
    max_cut_hamiltonian = hamiltonians.get_qaoa_max_cut_hamiltonian(graph)
    converted_strings = convert_pauli_strings(max_cut_hamiltonian)
    hamiltonian = SparsePauliOp.from_sparse_list(converted_strings, num_qubits)

    circuit = qaoa.get_ansatz(hamiltonian, reps=2)

    compiled_circuit = qiskit_optimise_circuit(circuit, quantum_computer_backend)

    backend_sim = AerSimulator.from_backend(backend)
    estimator = BackendEstimatorV2(backend=backend_sim)
    estimator.options.default_shots = 1000

    # Set simple error suppression/mitigation options
    estimator.options.dynamical_decoupling.enable = True
    estimator.options.dynamical_decoupling.sequence_type = "XY4"
    estimator.options.twirling.enable_gates = True
    estimator.options.twirling.num_randomizations = "auto"

    initial_gamma = np.pi
    initial_beta = np.pi / 2
    init_params = [initial_beta, initial_beta, initial_gamma, initial_gamma]

    result = minimize(
        cost_func_estimator,
        init_params,
        args=(compiled_circuit, hamiltonian, estimator),
        method="COBYLA",
        tol=1e-2,
    )
    print(result)
