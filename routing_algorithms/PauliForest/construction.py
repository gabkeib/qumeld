from routing_algorithms.PauliForest.traversal import traversal

def get_central_qubit(distance_matrix, core_qubits):
    min_dist = float('inf')
    central_qubit = None
    for qubit in core_qubits:
        dist = 0
        for another_qubit in core_qubits:
            if qubit != another_qubit:
                dist += distance_matrix[qubit][another_qubit]
        if dist < min_dist:
            min_dist = dist
            central_qubit = qubit
    return central_qubit

def edges_to_add(distance_matrix, tree_qubits, unjoined_qubits):
    dist = 0
    for qubit in unjoined_qubits:
        shortest_dist = float('inf')
        for tree_qubit in tree_qubits:
            curr_dist = distance_matrix[qubit][tree_qubit]
            if curr_dist < shortest_dist:
                shortest_dist = curr_dist
        dist += shortest_dist
    return dist

def get_core_qubits(pauli_string):
    return [i for i, char in enumerate(pauli_string) if char != 'I']

def map_core_qubits(init_core_qubits, qubit_mapping):
    return [qubit_mapping[qubit] for qubit in init_core_qubits] 

#TODO: add qubit mapping 
def construction(distance_matrix, pauli_string, qubit_mapping):
    qubit_tree = {}
    init_core_qubits = get_core_qubits(pauli_string)
    core_qubits = init_core_qubits
    # core_qubits = map_core_qubits(init_core_qubits, qubit_mapping)
    tree_qubits = set()
    unjoined_qubits = set(core_qubits)
    central_qubit = get_central_qubit(distance_matrix, core_qubits)
    qubit_tree[central_qubit] = []
    tree_qubits.add(central_qubit)
    unjoined_qubits.remove(central_qubit)

    possible_qubits_to_add = set()
    for qubit in range(len(distance_matrix)):
        if distance_matrix[central_qubit][qubit] == 1:
            possible_qubits_to_add.add(qubit)

    while unjoined_qubits:
        candidate = None
        min_edges = float('inf')
        candidates_set = []
        for qubit in possible_qubits_to_add:
            tree_qubits.add(qubit)
            if qubit in unjoined_qubits:
                unjoined_qubits.remove(qubit)
            edges = edges_to_add(distance_matrix, tree_qubits, unjoined_qubits)
            if edges == min_edges:
                candidates_set.append(qubit)
            if edges < min_edges:
                min_edges = edges
                candidates_set = [qubit]
            tree_qubits.remove(qubit)
            if qubit in init_core_qubits:
                unjoined_qubits.add(qubit)
        # print("same:", all_same)

        min_depth = float('inf')
        edge_to_add = (None, None)
        for qubit in candidates_set:
            for tree_qubit in tree_qubits:
                # print("dist", qubit, tree_qubit, distance_matrix[qubit][tree_qubit])
                if distance_matrix[qubit][tree_qubit] == 1:
                    if tree_qubit not in qubit_tree:
                        qubit_tree[tree_qubit] = []
                    qubit_tree[tree_qubit].append(qubit)
                    qubit_tree[qubit] = []
                    

                    qc, _ = traversal(qubit_tree, central_qubit, pauli_string, qubit_mapping)
                    depth = qc.depth()
                    if depth < min_depth:
                        min_depth = depth
                        edge_to_add = (qubit, tree_qubit)
                    qubit_tree[tree_qubit].remove(qubit)
                    qubit_tree.pop(qubit)

        (min_depth_qubit, tree_qubit) = edge_to_add
        if tree_qubit not in qubit_tree:
            qubit_tree[tree_qubit] = []
        qubit_tree[tree_qubit].append(min_depth_qubit)
        qubit_tree[min_depth_qubit] = []
        tree_qubits.add(min_depth_qubit)
        if min_depth_qubit in unjoined_qubits:
            unjoined_qubits.remove(min_depth_qubit)
        candidates_set.remove(min_depth_qubit)
        for qubit in range(len(distance_matrix)):
            if distance_matrix[min_depth_qubit][qubit] == 1 and qubit not in tree_qubits:
                possible_qubits_to_add.add(qubit)
        possible_qubits_to_add.remove(min_depth_qubit)
    return qubit_tree, central_qubit