from qiskit.circuit.library import QAOAAnsatz


def get_ansatz(hamiltonian, reps=2):
    circuit = QAOAAnsatz(cost_operator=hamiltonian, reps=reps)
    return circuit
