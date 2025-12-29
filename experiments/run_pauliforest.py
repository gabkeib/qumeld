from typing import List
from qiskit import transpile
from external_quantum_compilers.PauliGo.functions import compute_block_cover
from external_quantum_compilers.PauliGo.compiler import Compiler
from external_quantum_compilers.PauliGo.benchmark.mypauli import pauliString
from stats_utils.estimated_value import calculate_estimated_average_value_and_dispersion
from topologies.topologies import get_topology_by_string
from time import time
from experiments.types import CircuitOptimisationResult

def program_prep(origin_blocks):
    bn = pn = 0
    blocks = []
    for bk in origin_blocks:
        blocks.append([pauliString(ps[0], ps[1]) for ps in bk])
    bn = len(origin_blocks)
    return blocks

def convert_string_to_pauli_string(pauli_string):
    return [[pauli_string, 1.0]] # current rotation is 0

def run_pauliforest_circuit(circuit, quantum_computer, quantum_computer_name, run_qiskit_transpile=False):
    print("PauliForest arbitrary circuit optimisation is not supported")
    pass

def run_pauliforest_hamiltonian(
        quantum_computer,
        num_qubits: int,
        pauli_strings: List[str],
        run_qiskit_transpile=False,
        quantum_algorithm: str="") -> CircuitOptimisationResult:
    time_start = time()
    op_list = [convert_string_to_pauli_string(ps) for ps in pauli_strings]
    blocks = program_prep(op_list)
    compiler = Compiler(blocks, quantum_computer)
    qc = compiler.start("ucc")
    # count_res = {}
    # count_res['swap'] = qc.count_ops()['swap']
    if run_qiskit_transpile:
        qc = transpile(qc, basis_gates=['cx', 'u3'], optimization_level=3)
    calculated_statistics = calculate_estimated_average_value_and_dispersion(qc, qc, None)
    return CircuitOptimisationResult(
        name=quantum_algorithm,
        swap_count=qc.count_ops().get('swap', 0),
        cx_count=qc.count_ops().get('cx', 0) + qc.count_ops().get('swap', 0) * 3,
        depth=qc.depth(),
        expected_value=calculated_statistics.expected_value_after,
        variance=calculated_statistics.variance_after,
        fidelity=calculated_statistics.fidelity,
        optimisation_time=time() - time_start,
        optimised_circuit=qc
    )
