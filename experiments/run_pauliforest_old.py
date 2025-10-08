import qiskit
from topologies.topologies import get_topology_by_string
from quantum_algorithms.vqe import get_pauli_strings
from routing_algorithms.PauliForest.mapping import mapping, get_distance_matrix
from routing_algorithms.PauliForest.construction import construction, traversal
from external_quantum_compilers.Paulihedral_new.parallel_bl import depth_oriented_scheduling
from external_quantum_compilers.Paulihedral_new.benchmark.mypauli import pauliString

def run_pauliforest_old(quantum_computer):
    topology, qubits = get_topology_by_string(quantum_computer)

    # pauli_strings = get_pauli_strings()

    demo_pauli_strings = [
        "YZZZZYYIY",
        "XYIXXIZYZ",
        "XXIIXXYXI",
        "ZIIIXYYYY",
        "XZYYXZXYI",
    ]

    qubit_mapping = mapping(topology, qubits, demo_pauli_strings)
    print(qubit_mapping)

    qubit_mapping[0] = 5
    qubit_mapping[1] = 4
    qubit_mapping[2] = 3
    qubit_mapping[3] = 7
    qubit_mapping[4] = 0
    qubit_mapping[5] = 6
    qubit_mapping[6] = 2
    qubit_mapping[7] = 1
    qubit_mapping[8] = 8

    distance_matrix_old = get_distance_matrix(topology, qubits)
    print(distance_matrix_old)
    remapped_topology = [
        (qubit_mapping[a], qubit_mapping[b]) for a, b in topology
    ]
    print(remapped_topology)
    distance_matrix = get_distance_matrix(remapped_topology, qubits)
    print(distance_matrix)

    parr = [
        [pauliString("YZZZZYYIY", 1.0), pauliString("XYIXXIZYZ", 1.0)],
        [pauliString("XXIIXXYXI", 1.0), pauliString("ZIIIXYYYY", 1.0)],
        [pauliString("XZYYXZXYI", 1.0)]
    ]
    nq = len(parr[0][0])
    length = (
        nq // 2
    )  # `length' is a hyperparameter, and can be adjusted for best performance
    a1 = depth_oriented_scheduling(parr, length=length, maxiter=30)

    qubit_trees = []
    qc = qiskit.QuantumCircuit(len(qubit_mapping))
    current_qubit_mapping = qubit_mapping.copy()
    for pauli_string in demo_pauli_strings:
        qubit_tree, central_node = construction(distance_matrix, pauli_string, qubit_mapping)
        qubit_trees.append(qubit_tree)
        qc_traversal, current_qubit_mapping = traversal(qubit_tree, central_node, pauli_string, current_qubit_mapping)
        qc = qc.compose(qc_traversal)
        print("tree:", qubit_tree)
        print("center", central_node)
        print(qc_traversal)
    qc2 = qiskit.transpile(qc, basis_gates=["u3", "cx"], optimization_level=3)
