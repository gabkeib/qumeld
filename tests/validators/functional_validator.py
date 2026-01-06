import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, Operator, partial_trace
from qiskit_aer import AerSimulator
from scipy.stats import chisquare


class FunctionalValidator:
    """Validates functional equivalence between original and mapped circuits"""

    @staticmethod
    def validate_statevector(
        original: QuantumCircuit, mapped: QuantumCircuit, atol: float = 1e-7
    ) -> tuple[bool, str]:
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
            # Remove any measurements for statevector simulation
            original_no_meas = original.remove_final_measurements(inplace=False)
            mapped_no_meas = mapped.remove_final_measurements(inplace=False)

            sv_original = Statevector.from_instruction(original_no_meas)
            sv_mapped = Statevector.from_instruction(mapped_no_meas)

            # Handle different qubit counts
            num_qubits_orig = original_no_meas.num_qubits
            num_qubits_mapped = mapped_no_meas.num_qubits

            if num_qubits_mapped > num_qubits_orig:
                qubits_to_trace = list(range(num_qubits_orig, num_qubits_mapped))
                sv_mapped = partial_trace(sv_mapped, qubits_to_trace)
            elif num_qubits_orig > num_qubits_mapped:
                return (
                    False,
                    f"Mapped circuit has fewer qubits ({num_qubits_mapped}) than original ({num_qubits_orig})",
                )

            equivalent = sv_original.equiv(sv_mapped, atol=atol)

            if equivalent:
                return True, "Statevectors equivalent"
            else:
                fidelity = np.abs(sv_original.inner(sv_mapped)) ** 2
                return False, f"Statevectors differ (fidelity: {fidelity:.6f})"

        except Exception as e:
            return False, f"Statevector simulation failed: {str(e)}"

    @staticmethod
    def validate_unitary(
        original: QuantumCircuit, mapped: QuantumCircuit, atol: float = 1e-7
    ) -> tuple[bool, str]:
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
            # Remove measurements
            original_no_meas = original.remove_final_measurements(inplace=False)
            mapped_no_meas = mapped.remove_final_measurements(inplace=False)

            num_qubits_orig = original_no_meas.num_qubits
            num_qubits_mapped = mapped_no_meas.num_qubits

            if num_qubits_mapped != num_qubits_orig:
                return (
                    False,
                    f"Cannot compare unitaries: different qubit counts ({num_qubits_orig} vs {num_qubits_mapped})",
                )

            U_original = Operator(original_no_meas)
            U_mapped = Operator(mapped_no_meas)

            equivalent = U_original.equiv(U_mapped, atol=atol)

            if equivalent:
                return True, "Unitaries equivalent"
            else:
                fidelity = (
                    np.abs(np.trace(U_original.data.conj().T @ U_mapped.data)) ** 2
                    / (2**original_no_meas.num_qubits) ** 2
                )
                return False, f"Unitaries differ (fidelity: {fidelity:.6f})"

        except Exception as e:
            return False, f"Unitary comparison failed: {str(e)}"

    @staticmethod
    def _extract_initial_layout(mapped: QuantumCircuit) -> dict[int, int] | None:
        """
        Extract the initial layout from mapped circuit metadata
        Returns mapping from logical qubit index to physical qubit index
        """
        if hasattr(mapped, "_layout") and mapped._layout is not None:
            # Qiskit transpiler stores layout information
            layout = mapped._layout.initial_layout
            if layout is not None:
                # Layout maps Qubit -> int (physical position)
                # Convert to logical index -> physical index
                return {
                    qubit.index: physical_idx
                    for qubit, physical_idx in layout.get_physical_bits().items()
                    if hasattr(qubit, "index")
                }
        return None

    @staticmethod
    def validate_measurement(
        original: QuantumCircuit,
        mapped: QuantumCircuit,
        shots: int = 10000,
        p_threshold: float = 0.01,
    ) -> tuple[bool, str]:
        """
        Compare using measurement statistics
        Handles qubit reordering by checking layout metadata

        Args:
            original: Original circuit
            mapped: Mapped circuit
            shots: Number of measurements
            p_threshold: P-value threshold for acceptance

        Returns:
            (is_equivalent, message)
        """
        original_meas = original.copy()
        mapped_meas = mapped.copy()

        original_meas = original_meas.remove_final_measurements(inplace=False)
        mapped_meas = mapped_meas.remove_final_measurements(inplace=False)

        original_meas.measure_all()
        mapped_meas.measure_all()

        simulator = AerSimulator()
        result_orig = simulator.run(original_meas, shots=shots).result()
        result_mapped = simulator.run(mapped_meas, shots=shots).result()

        counts_orig = result_orig.get_counts()
        counts_mapped = result_mapped.get_counts()

        num_qubits_orig = original.num_qubits
        num_qubits_mapped = mapped.num_qubits

        layout = FunctionalValidator._extract_initial_layout(mapped)

        if num_qubits_mapped >= num_qubits_orig:
            processed_counts = {}

            for bitstring, count in counts_mapped.items():
                bits = list(bitstring)

                if layout is not None:
                    # Use layout information to reorder
                    reordered_bits = ["0"] * num_qubits_orig
                    for logical_idx in range(num_qubits_orig):
                        physical_idx = layout.get(logical_idx, logical_idx)
                        if physical_idx < len(bits):
                            # Bitstring is reversed
                            reordered_bits[logical_idx] = bits[-(physical_idx + 1)]
                    new_bitstring = "".join(reordered_bits)
                else:
                    # Assume first num_qubits_orig physical qubits correspond to logical qubits
                    # Qiskit bitstrings are reversed
                    new_bitstring = bitstring[-num_qubits_orig:]

                processed_counts[new_bitstring] = (
                    processed_counts.get(new_bitstring, 0) + count
                )

            counts_mapped = processed_counts

        # Convert to probability distributions
        all_outcomes = sorted(set(counts_orig.keys()) | set(counts_mapped.keys()))

        if not all_outcomes:
            return False, "No measurement outcomes"

        probs_orig = np.array([counts_orig.get(outcome, 0) for outcome in all_outcomes])
        probs_mapped = np.array(
            [counts_mapped.get(outcome, 0) for outcome in all_outcomes]
        )

        # Normalize
        probs_orig = probs_orig / probs_orig.sum()
        probs_mapped = probs_mapped / probs_mapped.sum()

        # Total Variation Distance
        tvd = 0.5 * np.sum(np.abs(probs_orig - probs_mapped))

        # Use TVD as primary metric
        if tvd < 0.05:  # 5% threshold
            return True, f"Statistics match (TVD={tvd:.4f})"
        elif tvd < 0.15:  # 15% warning threshold
            # Also try chi-squared test
            expected_counts = probs_orig * shots
            observed_counts = probs_mapped * shots

            mask = expected_counts >= 5
            if mask.any():
                try:
                    chi2, p_value = chisquare(
                        observed_counts[mask], expected_counts[mask]
                    )
                    if p_value >= p_threshold:
                        return (
                            True,
                            f"Statistics match (TVD={tvd:.4f}, p={p_value:.4f})",
                        )
                except:
                    pass

            return False, f"Statistics differ (TVD={tvd:.4f})"
        else:
            return False, f"Statistics differ significantly (TVD={tvd:.4f})"
