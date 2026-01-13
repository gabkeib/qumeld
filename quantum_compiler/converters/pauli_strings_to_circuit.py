from typing import List
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import PauliEvolutionGate

from quantum_compiler.core.types import PauliString


def get_non_identity_pauli_operator(pauli_string: List[str]):
    return [i for i in range(len(pauli_string)) if pauli_string[i] != "I"]


def convert_pauli_strings(pauli_strings: List[PauliString]):
    return [((s.pauli_string, get_non_identity_pauli_operator(s.pauli_string), s.coeff)) for s in pauli_strings]


def convert_pauli_strings_to_circuit(pauli_strings: List[PauliString], num_qubits: int) -> QuantumCircuit:
    converted_strings = convert_pauli_strings(pauli_strings)
    hamiltonian = SparsePauliOp.from_sparse_list(converted_strings, num_qubits)

    evo_gate = PauliEvolutionGate(hamiltonian, time=1.0)
    circuit = QuantumCircuit(hamiltonian.num_qubits)
    circuit.append(evo_gate, circuit.qubits)

    return circuit.decompose()
