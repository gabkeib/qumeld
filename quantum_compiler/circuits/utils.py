import networkx as nx
from qiskit import QuantumCircuit
from collections import Counter

def extract_circuit_features(circuit: QuantumCircuit) -> dict:
    """
    Extract topology and gate features from a quantum circuit.
    
    Returns:
        Dictionary containing circuit features
    """
    features = {}
    
    features['num_qubits'] = circuit.num_qubits
    
    two_qubit_gates = [
        instr for instr in circuit.data 
        if len(instr.qubits) == 2
    ]
    features['two_qubit_gate_count'] = len(two_qubit_gates)
    features['circuit_depth'] = circuit.depth()
    
    interaction_graph = nx.Graph()
    interaction_graph.add_nodes_from(range(circuit.num_qubits))
    
    for instr in two_qubit_gates:
        q1 = circuit.find_bit(instr.qubits[0]).index
        q2 = circuit.find_bit(instr.qubits[1]).index
        if interaction_graph.has_edge(q1, q2):
            interaction_graph[q1][q2]['weight'] += 1
        else:
            interaction_graph.add_edge(q1, q2, weight=1)
    
    # Interaction graph properties
    if interaction_graph.number_of_edges() > 0:
        features['graph_diameter'] = nx.diameter(interaction_graph) if nx.is_connected(interaction_graph) else -1
        features['average_degree'] = sum(dict(interaction_graph.degree()).values()) / circuit.num_qubits
        features['graph_density'] = nx.density(interaction_graph)
    else:
        features['graph_diameter'] = 0
        features['average_degree'] = 0
        features['graph_density'] = 0
    
    # Gate distribution - measure clustering
    qubit_interactions = Counter()
    for instr in two_qubit_gates:
        q1 = circuit.find_bit(instr.qubits[0]).index
        q2 = circuit.find_bit(instr.qubits[1]).index
        qubit_interactions[(min(q1, q2), max(q1, q2))] += 1
    
    if qubit_interactions:
        interaction_counts = list(qubit_interactions.values())
        avg_interactions = sum(interaction_counts) / len(interaction_counts)
        variance = sum((x - avg_interactions) ** 2 for x in interaction_counts) / len(interaction_counts)
        features['interaction_variance'] = variance
        features['max_interactions_per_edge'] = max(interaction_counts)
    else:
        features['interaction_variance'] = 0
        features['max_interactions_per_edge'] = 0
    
    return features
