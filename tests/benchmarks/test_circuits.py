import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import QFT


def get_test_circuits() -> list[QuantumCircuit]:
    circuits = []

    # 1. Bell pair
    qc = QuantumCircuit(2, name="bell_pair")
    qc.h(0)
    qc.cx(0, 1)
    circuits.append(qc)

    # 2. GHZ state
    qc = QuantumCircuit(4, name="ghz_4")
    qc.h(0)
    for i in range(3):
        qc.cx(i, i + 1)
    circuits.append(qc)

    # 3. Linear chain
    qc = QuantumCircuit(5, name="linear_chain")
    qc.h(range(5))
    for i in range(4):
        qc.cx(i, i + 1)
        qc.rz(np.pi / 4, i + 1)
    circuits.append(qc)

    # 4. QFT
    qc = QFT(4, do_swaps=False, name="qft_4")
    circuits.append(qc.decompose())

    # 5. Star topology
    qc = QuantumCircuit(5, name="star_topology")
    qc.h(range(5))
    for i in range(1, 5):
        qc.cx(0, i)
    circuits.append(qc)

    # 6. Fully connected
    qc = QuantumCircuit(4, name="fully_connected")
    qc.h(range(4))
    for i in range(4):
        for j in range(i + 1, 4):
            qc.cx(i, j)
    circuits.append(qc)

    for seed in [42, 123, 456]:
        np.random.seed(seed)
        qc = QuantumCircuit(5, name=f"random_{seed}")
        qc.h(range(5))
        for _ in range(10):
            q1, q2 = np.random.choice(5, 2, replace=False)
            qc.cx(int(q1), int(q2))
            qc.rz(np.random.uniform(0, 2 * np.pi), int(q2))
        circuits.append(qc)

    return circuits
