import numpy as np
import networkx as nx


def get_feature_matrix(pauli_layers):
    if len(pauli_layers) == 0:
        return np.zeros((0, 0))
    rows = len(pauli_layers)
    columns = len(pauli_layers[0])
    matrix = np.zeros((rows, columns))
    for i in range(rows):
        for j in range(columns):
            if pauli_layers[i][j] != "I":
                matrix[i][j] = 1
    return matrix


def get_distance_matrix(graph, qubits):
    dist_matrix = np.full((qubits, qubits), np.inf)
    for i in range(qubits):
        dist_matrix[i][i] = 0
    for (a, b) in graph:
        dist_matrix[a][b] = 1
        dist_matrix[b][a] = 1
    for k in range(qubits):
        for i in range(qubits):
            for j in range(qubits):
                if dist_matrix[i][k] + dist_matrix[k][j] < dist_matrix[i][j]:
                    dist_matrix[i][j] = dist_matrix[i][k] + dist_matrix[k][j]
    return dist_matrix
    


def correlation_between_qubits(feature_matrix, q1, q2):
    if feature_matrix.shape[0] == 0:
        return 0
    return np.dot(feature_matrix[:, q1], feature_matrix[:, q2])


def get_initial_qubit_mapping(graph):
    qubit_mapping = {}
    for [a, b] in graph:
        qubit_mapping[a] = a
        qubit_mapping[b] = b
    return qubit_mapping


def get_next_qubit(feature_matrix, used_qubits):
    correlations = []
    for i in range(feature_matrix.shape[1]):
        if i not in used_qubits:
            sum_corr = 0
            for j in used_qubits:
                corr = correlation_between_qubits(feature_matrix, j, i)
                sum_corr += corr
            correlations.append((i, sum_corr))
    if not correlations:
        return None
    return max(correlations, key=lambda x: x[1])[0]


def get_center_nodes(graph):
    graph_netx = nx.Graph(graph)
    return list(nx.center(graph_netx))


def get_physical_qubit_to_map(
    distance_matrix,
    qubit_mapping,
    pauli_strings,
    qubit_to_map,
    used_qubits,
    available_qubits,
):
    min_dist = np.inf
    min_qubit_index = None

    for available_qubit in available_qubits:
        dist = 0
        for pauli_string in pauli_strings:
            pauli_operator = pauli_string[qubit_to_map]
            if pauli_operator != "I":
                min_curr_dist = np.inf
                for j, op in enumerate(pauli_string):
                    if op != "I" and j != available_qubit:
                        curr_dist = distance_matrix[available_qubit][qubit_mapping[j]]
                        if curr_dist == 0:
                            print("INCORRECT STATE")
                        min_curr_dist = min(min_curr_dist, curr_dist)
                dist += min_curr_dist
        if dist < min_dist:
            min_dist = dist
            min_qubit_index = available_qubit

    print()
    return min_qubit_index


def mapping(graph, qubits, pauli_layers):
    feature_matrix = get_feature_matrix(pauli_layers)
    most_used_qubit = np.argmax(np.sum(feature_matrix, axis=0))
    map_order = [most_used_qubit]
    used_qubits = {most_used_qubit}
    qubit_mapping = get_initial_qubit_mapping(graph)
    available_qubits = set(range(len(qubit_mapping)))
    distance_matrix = get_distance_matrix(graph, qubits)

    center_qubits = get_center_nodes(graph)
    if len(center_qubits) == 0:
        raise Exception("Graph has no center nodes.")

    center_node = center_qubits[0]
    qubit_mapping[most_used_qubit] = center_node
    available_qubits.remove(center_node)
    used_physical_qubits = {center_node}
    while True:
        next_qubit = get_next_qubit(feature_matrix, used_qubits)
        if next_qubit is None:
            break
        qubit_to_map = get_physical_qubit_to_map(
            distance_matrix,
            qubit_mapping,
            pauli_layers,
            next_qubit,
            used_physical_qubits,
            available_qubits,
        )
        qubit_mapping[next_qubit] = qubit_to_map
        map_order.append(next_qubit)
        used_qubits.add(next_qubit)
        used_physical_qubits.add(qubit_to_map)
        available_qubits.remove(qubit_to_map)
    return qubit_mapping
