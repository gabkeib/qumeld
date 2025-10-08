import qiskit
from typing import Tuple, List

def core(pauli_string):
    list = []
    for i in range(len(pauli_string)):
        if pauli_string[i] != 'I':
            list.append(i)
    return list

def traversal(tree, root, pauli_string, qubit_mapping) -> Tuple[qiskit.QuantumCircuit, List[int]]:
    depth_of_qubits = []
    curr_qubit_mapping = qubit_mapping.copy()
    for x in tree[root]:
        qc, curr_qubit_mapping = traversal(tree, x, pauli_string, curr_qubit_mapping)
        depth_of_qubits.append({
            "qc": qc,
            "depth": qc.depth(),
            "node": x,
        })
    depth_of_qubits.sort(key=lambda item: item["depth"])
    qc = qiskit.QuantumCircuit(len(qubit_mapping))
    core_qubits = core(pauli_string)
    if len(depth_of_qubits) == 0:
        return qc, curr_qubit_mapping
    map_value = -1
    # for qubit in range(len(curr_qubit_mapping)):
    #     if curr_qubit_mapping[qubit] == root:
    #         map_value = qubit
    #         break
    qc = qc.compose(depth_of_qubits[0]["qc"])
    #TODO: sus sitoj vietoj
    if root not in core_qubits:
        print("swapping: ", map_value, root, depth_of_qubits[0]["node"],  core_qubits, curr_qubit_mapping)
        qc.swap(root, depth_of_qubits[0]["node"])
        curr_qubit_mapping[depth_of_qubits[0]["node"]], curr_qubit_mapping[map_value] = curr_qubit_mapping[map_value], curr_qubit_mapping[depth_of_qubits[0]["node"]]
        root = depth_of_qubits[0]["node"]
    else:
        qc.cx(depth_of_qubits[0]["node"], root)

    for item in depth_of_qubits[1:]:
        qc = qc.compose(item["qc"])
        qc.cx(item["node"], root)

    return qc, curr_qubit_mapping
