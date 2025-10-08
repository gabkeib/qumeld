from calendar import c
from pathlib import Path
from time import time
import subprocess
import os

from typing import List

from qiskit import QuantumCircuit, qasm2

from experiments.run_qiskit import convert_pauli_strings
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp

from experiments.types import CircuitOptimisationResult

def convert_to_layout(name, quantum_computer: List[List[int]], num_qubits: int) -> List[int]:
    coupling_map = [[] for _ in range(num_qubits)]
    for i, edge in enumerate(quantum_computer):
        coupling_map[edge[0]].append(edge[1])
        coupling_map[edge[1]].append(edge[0])
    with open(f"./layouts/doustra/{name}.layout", "w") as f:
        f.write(f"NAME: {name}\n")
        f.write(f"QUBITNUM: {num_qubits}\n")
        f.write("GATESET: {x, rz, h, id, sx, cnot}\n")
        f.write(f"COUPLINGMAP: {coupling_map}\n")
        f.write(f"SGERROR: {[0 for _ in range(num_qubits)]}\n")
        f.write(f"SGTIME: {[0 for _ in range(num_qubits)]}\n")
        f.write(f"CNOTERROR: {coupling_map}\n")
        f.write(f"CNOTTIME: {coupling_map}")

    return coupling_map


def run_doustra_hamiltonian(quantum_computer: List[List[int]], quantum_computer_name: str, num_qubits: int,  pauli_strings: List[str], quantum_algorithm: str):
    time_start = time()

    converted_strings = convert_pauli_strings(pauli_strings)
    hamiltonian = SparsePauliOp.from_sparse_list(converted_strings, num_qubits)

    evo_gate = PauliEvolutionGate(hamiltonian, time=1.0)
    circuit = QuantumCircuit(hamiltonian.num_qubits)
    circuit.append(evo_gate, circuit.qubits)

    optimised_qc = doustra_optimise_circuit(circuit, quantum_computer, quantum_computer_name, quantum_algorithm)

    return CircuitOptimisationResult(
        name=quantum_algorithm,
        swap_count=optimised_qc.count_ops().get('swap', 0),
        depth=optimised_qc.depth(),
        optimisation_time=time() - time_start
    )

def run_doustra_circuit(circuit: QuantumCircuit, quantum_computer: List[List[int]], quantum_computer_name: str, quantum_algorithm: str) -> CircuitOptimisationResult:
    time_start = time()
    optimised_qc = doustra_optimise_circuit(circuit, quantum_computer, quantum_computer_name, quantum_algorithm)
    return CircuitOptimisationResult(
        name=quantum_algorithm,
        swap_count=optimised_qc.count_ops().get('swap', 0),
        depth=optimised_qc.depth(),
        optimisation_time=time() - time_start
    )

def doustra_optimise_circuit(circuit: QuantumCircuit, quantum_computer: List[List[int]], quantum_computer_name: str, quantum_algorithm: str) -> CircuitOptimisationResult:
    time_start = time()

    script_path = "./scripts/doustra/optimise_circuit.qsyn"
    in_path = f"./dumps/{quantum_algorithm}.qasm"
    out_path = f"./dumps/{quantum_algorithm}_output.qasm"
    layout_path = f"./layouts/doustra/{quantum_computer_name}.layout"

    qasm2.dump(circuit.decompose(), open(in_path, "w"))

    if not Path(layout_path).exists():
        convert_to_layout(quantum_computer_name, quantum_computer, circuit.num_qubits)

    # Get the path to the qsyn binary in the external_quantum_compilers directory
    qsyn_path = "./external_quantum_compilers/qsyn/qsyn"
    
    # Run qsyn with subprocess
    command = [
        qsyn_path,
        script_path,
        in_path,
        layout_path,
        out_path
    ]
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            cwd=os.getcwd()
        )
        print(f"qsyn stdout: {result.stdout}")
        if result.stderr:
            print(f"qsyn stderr: {result.stderr}")
    except subprocess.CalledProcessError as e:
        print(f"qsyn failed with return code {e.returncode}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        raise

    optimised_qc = QuantumCircuit.from_qasm_str(open(out_path, "r").read())

    return optimised_qc