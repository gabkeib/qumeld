import numpy as np
from scipy.optimize import linear_sum_assignment
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit.quantum_info import hellinger_fidelity
from typing import Dict

class BlindValidator:
    def __init__(self, shots: int = 10000) -> None:
        self.shots = shots
        self.sim = AerSimulator()

    def _get_counts(self, circuit: QuantumCircuit) -> Dict[str, int]:
        """Prepares circuit and runs simulation."""
        # Work on a copy to avoid modifying user objects
        qc = circuit.copy()
        
        # Remove existing measurements to ensure we measure everything cleanly
        qc.remove_final_measurements()
        qc.measure_all()
        
        # Run simulation
        result = self.sim.run(qc, shots=self.shots).result()
        return result.get_counts()

    def _calculate_marginals(self, counts: Dict[str, int], num_qubits: int) -> np.ndarray:
        """
        Calculates the probability of each qubit being '1'.
        Returns array of shape (num_qubits,)
        """
        marginals = np.zeros(num_qubits)
        total_shots = sum(counts.values())
        
        for bitstring, count in counts.items():
            prob = count / total_shots
            # Iterate bits. Qiskit string is Reversed (Rightmost is q0)
            for i in range(num_qubits):
                str_idx = len(bitstring) - 1 - i
                if str_idx >= 0 and bitstring[str_idx] == '1':
                    marginals[i] += prob
        return marginals

    def _infer_layout(self, counts_orig: Dict[str, int], n_orig: int, counts_map: Dict[str, int], n_map: int) -> Dict[int, int]:
        """
        Uses Hungarian Algorithm to match Logical Qubits to Physical Qubits
        based on marginal probabilities.
        """
        marg_orig = self._calculate_marginals(counts_orig, n_orig)
        marg_map = self._calculate_marginals(counts_map, n_map)

        # Creating cost matrix
        # Rows = logical qubits, columns = physical qubits
        cost_matrix = np.zeros((n_orig, n_map))
        for r in range(n_orig):
            for c in range(n_map):
                cost_matrix[r, c] = abs(marg_orig[r] - marg_map[c])

        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        # logical_idx -> physical_idx
        layout_map = {r: c for r, c in zip(row_ind, col_ind)}
        return layout_map

    def _remap_counts(self, counts_map: Dict[str, int], layout_map: Dict[int, int], n_orig: int) -> Dict[str, int]:
        """
        Transforms physical counts (example: '00101') into logical counts (example: '11')
        using the inferred layout.
        """
        new_counts = {}
        for bitstring, count in counts_map.items():
            logical_bits = ['0'] * n_orig
            
            for logical_idx in range(n_orig):
                physical_idx = layout_map.get(logical_idx)
                
                # Extract bit from physical string
                phys_str_idx = len(bitstring) - 1 - physical_idx
                
                if 0 <= phys_str_idx < len(bitstring):
                    logical_bits[logical_idx] = bitstring[phys_str_idx]
            
            new_key = "".join(reversed(logical_bits))
            
            new_counts[new_key] = new_counts.get(new_key, 0) + count
            
        return new_counts

    def validate(self, original: QuantumCircuit, mapped: QuantumCircuit) -> tuple[bool, float, Dict[int, int]]:
        """
        Validates that the mapped circuit is functionally equivalent to the original
        """
        counts_orig = self._get_counts(original)
        counts_map = self._get_counts(mapped)
        
        layout = self._infer_layout(
            counts_orig, original.num_qubits,
            counts_map, mapped.num_qubits
        )
        
        counts_map_aligned = self._remap_counts(counts_map, layout, original.num_qubits)
        
        fidelity = hellinger_fidelity(counts_orig, counts_map_aligned)
        
        is_valid = fidelity > 0.9  # Adjust if needed
        
        return is_valid, fidelity, layout
