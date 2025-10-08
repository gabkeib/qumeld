from typing import List, Dict
class CircuitTopology:
    def __init__(self, dependency_graph):
        self._dependency_graph = dependency_graph 
        self._available_gates: List[int] = []
        self._executed_gates: Dict[int, int] = {}  # counts of executed predecessors

        # Initialize available gates
        for i, gate in enumerate(self._dependency_graph.get_gates()):
            if self._is_available(gate.get_id()):
                self._available_gates.append(i)

    def _is_available(self, gate_idx: int) -> bool:
        """Check if all predecessor gates have been executed."""
        preds = self._dependency_graph.get_predecessors(gate_idx)  # List[Optional[int]]
        # Only consider predecessors that are not None
        valid_preds = [p for p in preds if p is not None]
        return all(prev in self._executed_gates for prev in valid_preds)

    def clone(self) -> "CircuitTopology":
        # shallow copy; could use deepcopy if needed
        new_topo = CircuitTopology(self._dependency_graph)
        new_topo._available_gates = self._available_gates.copy()
        new_topo._executed_gates = self._executed_gates.copy()
        return new_topo

    def get_gate(self, gate_idx: int):
        return self._dependency_graph.get_gate(gate_idx)

    def get_available_gates(self) -> List[int]:
        return self._available_gates

    def update_available_gates(self, executed: int):
        gate_executed = self.get_gate(executed)
        # Remove executed gate from available gates
        if executed in self._available_gates:
            self._available_gates.remove(executed)
        assert gate_executed.get_id() == executed

        # Mark gate as executed
        self._executed_gates[executed] = 0

        # Add newly available successors
        for next_gate in self._dependency_graph.get_successors(executed):
            if next_gate is None:
                continue
            if self._is_available(self._dependency_graph.get_gate(next_gate).get_id()):
                self._available_gates.append(next_gate)

        # Trim executed predecessor counts
        gates_to_trim: List[int] = []
        for prev_id in self._dependency_graph.get_predecessors(executed):
            if prev_id is None:
                continue
            self._executed_gates[prev_id] = self._executed_gates.get(prev_id, 0) + 1
            prev_successors = [
                s for s in self._dependency_graph.get_successors(prev_id) if s is not None
            ]
            if self._executed_gates[prev_id] >= len(prev_successors):
                gates_to_trim.append(prev_id)

        for gate_id in gates_to_trim:
            self._executed_gates.pop(gate_id, None)