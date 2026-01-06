import networkx as nx
from qiskit import QuantumCircuit
from typing import List


class TopologyValidator:
    """Validates that circuits respect hardware topology constraints"""

    def __init__(self, coupling_map: List[List[int]]):
        """
        Args:
            coupling_map: List of [q1, q2] pairs representing connectivity
        """
        self.coupling_map = coupling_map
        self.coupling_graph = self._create_coupling_graph(coupling_map)

    def _create_coupling_graph(self, coupling_map: List[List[int]]) -> nx.Graph:
        G = nx.Graph()
        for q1, q2 in coupling_map:
            G.add_edge(q1, q2)
        return G

    def validate(self, circuit: QuantumCircuit) -> tuple[bool, str]:
        violations = []

        for instruction in circuit.data:
            if len(instruction.qubits) == 2:
                q1 = circuit.find_bit(instruction.qubits[0]).index
                q2 = circuit.find_bit(instruction.qubits[1]).index

                if not self.coupling_graph.has_edge(q1, q2):
                    violations.append(
                        f"{instruction.operation.name} on qubits ({q1}, {q2})"
                    )

        if violations:
            return False, f"Topology violations: {violations[:5]}"  # Limit output
        return True, "All gates respect topology"
