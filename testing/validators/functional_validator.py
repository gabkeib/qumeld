import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator
from qiskit_aer import AerSimulator
from scipy.stats import chisquare


class FunctionalValidator:
    """Validates functional equivalence between original and mapped circuits"""
    
    @staticmethod
    def validate_statevector(original: QuantumCircuit, 
                            mapped: QuantumCircuit,
                            atol: float = 1e-7) -> tuple[bool, str]:
        """
        Compare circuits using statevector simulation
        Best for circuits with <= 20 qubits
        
        Args:
            original: Original circuit
            mapped: Mapped circuit
            atol: Absolute tolerance for comparison
            
        Returns:
            (is_equivalent, message)
        """
        try:
            sv_original = Statevector.from_instruction(original)
            sv_mapped = Statevector.from_instruction(mapped)
            
            equivalent = sv_original.equiv(sv_mapped, atol=atol)
            
            if equivalent:
                return True, "Statevectors equivalent"
            else:
                fidelity = np.abs(sv_original.inner(sv_mapped))**2
                return False, f"Statevectors differ (fidelity: {fidelity:.6f})"
                
        except Exception as e:
            return False, f"Statevector simulation failed: {str(e)}"
    
    @staticmethod
    def validate_unitary(original: QuantumCircuit,
                        mapped: QuantumCircuit,
                        atol: float = 1e-7) -> tuple[bool, str]:
        """
        Compare circuits using unitary matrices
        Best for circuits without measurements, <= 15 qubits
        
        Args:
            original: Original circuit
            mapped: Mapped circuit
            atol: Absolute tolerance
            
        Returns:
            (is_equivalent, message)
        """
        try:
            U_original = Operator(original)
            U_mapped = Operator(mapped)
            
            equivalent = U_original.equiv(U_mapped, atol=atol)
            
            if equivalent:
                return True, "Unitaries equivalent"
            else:
                fidelity = np.abs(
                    np.trace(U_original.data.conj().T @ U_mapped.data)
                )**2 / (2**original.num_qubits)**2
                return False, f"Unitaries differ (fidelity: {fidelity:.6f})"
                
        except Exception as e:
            return False, f"Unitary comparison failed: {str(e)}"
    
    @staticmethod
    def validate_measurement(original: QuantumCircuit,
                           mapped: QuantumCircuit,
                           shots: int = 10000,
                           p_threshold: float = 0.01) -> tuple[bool, str]:
        """
        Compare using measurement statistics (chi-squared test)
        Good for larger circuits
        
        Args:
            original: Original circuit
            mapped: Mapped circuit
            shots: Number of measurements
            p_threshold: P-value threshold for acceptance
            
        Returns:
            (is_equivalent, message)
        """
        # Add measurements if needed
        original_meas = original.copy()
        mapped_meas = mapped.copy()
        
        if original_meas.num_clbits == 0:
            original_meas.measure_all()
        if mapped_meas.num_clbits == 0:
            mapped_meas.measure_all()
        
        # Simulate
        simulator = AerSimulator()
        result_orig = simulator.run(original_meas, shots=shots).result()
        result_mapped = simulator.run(mapped_meas, shots=shots).result()
        
        counts_orig = result_orig.get_counts()
        counts_mapped = result_mapped.get_counts()
        
        # Chi-squared test
        all_outcomes = set(counts_orig.keys()) | set(counts_mapped.keys())
        observed = [counts_orig.get(outcome, 0) for outcome in all_outcomes]
        expected = [counts_mapped.get(outcome, 0) for outcome in all_outcomes]
        
        filtered_pairs = [(o, e) for o, e in zip(observed, expected) if e > 0]
        if not filtered_pairs:
            return False, "No common measurement outcomes"
        
        obs_filtered, exp_filtered = zip(*filtered_pairs)
        chi2, p_value = chisquare(obs_filtered, exp_filtered)
        
        if p_value >= p_threshold:
            return True, f"Statistics match (p={p_value:.4f})"
        else:
            return False, f"Statistics differ (p={p_value:.4f})"
