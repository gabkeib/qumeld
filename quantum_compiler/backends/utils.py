from qiskit import transpiler
from qiskit.providers import BackendV2
import networkx as nx


def convert_array_to_coupling_map(arr):
    coupling_map = transpiler.CouplingMap(arr)
    return coupling_map

def extract_topology_features(backend: BackendV2) -> dict:
    """Extract topology features from a Qiskit BackendV2 object."""
    graph_list = backend.coupling_map.get_edges()
    num_qubits = backend.num_qubits
    
    G = nx.Graph()
    G.add_nodes_from(range(num_qubits))
    G.add_edges_from(graph_list)
    
    average_degree = sum(dict(G.degree()).values()) / num_qubits if num_qubits > 0 else 0

    try:
        diameter = nx.diameter(G) if nx.is_connected(G) else 0
    except:
        diameter = 0
    
    max_edges = num_qubits * (num_qubits - 1) / 2
    edge_density = G.number_of_edges() / max_edges if max_edges > 0 else 0

    return {
        "num_qubits": num_qubits,
        "average_degree": average_degree,
        "diameter": diameter,
        "edge_density": edge_density,
    }
