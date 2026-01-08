import logging
from math import exp, log
from qiskit.quantum_info import Statevector, state_fidelity, SparsePauliOp
from qiskit import QuantumCircuit
from sympy import Ci

from stats_utils.types import CircuitOptimisationStatistics

log = logging.getLogger(__name__)

def pad_hamiltonian_to_size(
    hamiltonian: SparsePauliOp, target_num_qubits: int
) -> SparsePauliOp:
    """Pad Hamiltonian with identity operators to match larger circuit"""
    current_qubits = hamiltonian.num_qubits

    if current_qubits == target_num_qubits:
        return hamiltonian

    if current_qubits > target_num_qubits:
        raise ValueError(
            f"Cannot pad: Hamiltonian has more qubits ({current_qubits}) than target ({target_num_qubits})"
        )

    # Number of identities to add
    padding = target_num_qubits - current_qubits

    # Pad each Pauli string with identities on the right
    padded_paulis = []
    for pauli, coeff in zip(hamiltonian.paulis, hamiltonian.coeffs):
        pauli_str = str(pauli)
        padded_str = pauli_str + "I" * padding
        padded_paulis.append((padded_str, coeff))

    return SparsePauliOp.from_list(padded_paulis)


def calculate_estimated_average_value_and_dispersion(
    qc_before: QuantumCircuit,
    qc_after: QuantumCircuit,
    hamiltonian: SparsePauliOp = None,
) -> CircuitOptimisationStatistics:
    if qc_before.num_clbits > 0 or qc_after.num_clbits > 0:
        log.warning(
            "Warning: Circuits with classical bits are not supported for estimated value calculation."
        )
        return CircuitOptimisationStatistics(
            expected_value_before=0.0,
            variance_before=0.0,
            expected_value_after=0.0,
            variance_after=0.0,
            fidelity=0.0,
        )

    max_qubits = max(qc_before.num_qubits, qc_after.num_qubits)
    if max_qubits > 9:
        log.warning(
            "Warning: Circuits with more than 9 qubits are not supported for estimated value calculation."
        )
        return CircuitOptimisationStatistics(
            expected_value_before=0.0,
            variance_before=0.0,
            expected_value_after=0.0,
            variance_after=0.0,
            fidelity=0.0,
        )

    num_qubits_before = qc_before.num_qubits
    num_qubits_after = qc_after.num_qubits

    if hamiltonian is None:
        hamiltonian = SparsePauliOp.from_list(
            [("Z" + "I" * (num_qubits_before - 1), 1.0)]
        )

    # Pad Hamiltonians if circuit sizes differ
    if num_qubits_before != num_qubits_after:
        max_qubits = max(num_qubits_before, num_qubits_after)
        hamiltonian_before = pad_hamiltonian_to_size(hamiltonian, num_qubits_before)
        hamiltonian_after = pad_hamiltonian_to_size(hamiltonian, max_qubits)
    else:
        hamiltonian_before = hamiltonian
        hamiltonian_after = hamiltonian

    # Calculate for before circuit
    psi_before = Statevector.from_instruction(qc_before)
    expected_value_before = psi_before.expectation_value(hamiltonian_before).real
    hamiltonian_squared_before = hamiltonian_before @ hamiltonian_before
    variance_before = (
        psi_before.expectation_value(hamiltonian_squared_before).real
        - expected_value_before**2
    )

    # Calculate for after circuit
    psi_after = Statevector.from_instruction(qc_after)
    expected_value_after = psi_after.expectation_value(hamiltonian_after).real
    hamiltonian_squared_after = hamiltonian_after @ hamiltonian_after
    variance_after = (
        psi_after.expectation_value(hamiltonian_squared_after).real
        - expected_value_after**2
    )

    if num_qubits_before < num_qubits_after:
        # Pad psi_before with |0⟩ states for ancilla qubits
        padding_qubits = num_qubits_after - num_qubits_before
        psi_before_padded = psi_before.tensor(
            Statevector.from_label("0" * padding_qubits)
        )
        fidelity = state_fidelity(psi_before_padded, psi_after)
    elif num_qubits_before > num_qubits_after:
        padding_qubits = num_qubits_before - num_qubits_after
        psi_after_padded = psi_after.tensor(
            Statevector.from_label("0" * padding_qubits)
        )
        fidelity = state_fidelity(psi_before, psi_after_padded)
    else:
        fidelity = state_fidelity(psi_before, psi_after)

    return CircuitOptimisationStatistics(
        expected_value_before=expected_value_before,
        variance_before=variance_before,
        expected_value_after=expected_value_after,
        variance_after=variance_after,
        fidelity=fidelity,
    )
