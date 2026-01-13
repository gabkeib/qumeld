from typing import Literal
from qiskit import QuantumCircuit

from quantum_compiler.converters.pauli_strings_to_circuit import (
    convert_pauli_strings_to_circuit,
)
from quantum_compiler.core.types import PauliString
from quantum_compiler.mappers.base_mapper import QubitMapper
from qiskit.providers import BackendV2

from tests.validators import blind_validator
from .validators.topology_validator import TopologyValidator
from .validators.functional_validator import FunctionalValidator
from .validators.blind_validator import BlindValidator


class CorrectnessTestSuite:
    """Test suite for qubit mapping algorithms"""

    def __init__(self, backend: BackendV2):
        """
        Args:
            backend: Backend/topology to test on
        """
        self.backend = backend
        self.topology_validator = TopologyValidator(backend.target.build_coupling_map())
        self.functional_validator = FunctionalValidator()
        self.blind_validator = BlindValidator()

    def _validate_with_fallback(
        self, original: QuantumCircuit, mapped: QuantumCircuit, preferred_method: str
    ) -> tuple[bool, str, str]:
        """
        Validate with automatic fallback to measurement if preferred method fails

        Returns:
            (is_correct, message, actual_method_used)
        """
        # Try preferred method first
        if preferred_method == "blind":
            is_valid, fidelity, inferred_layout = self.blind_validator.validate(
                original, mapped
            )
            return (
                is_valid,
                f"Fidelity: {fidelity}, First qubit mapped: {inferred_layout.get(0, 'unknown')}",
                "blind",
            )
        elif preferred_method == "statevector":
            correct, msg = self.functional_validator.validate_statevector(
                original, mapped
            )
            if "failed" not in msg.lower():
                return correct, msg, "statevector"

            # Fall back to measurement
            correct, msg = self.functional_validator.validate_measurement(
                original, mapped
            )
            return (
                correct,
                f"Statevector failed, used measurement: {msg}",
                "measurement",
            )

        elif preferred_method == "unitary":
            correct, msg = self.functional_validator.validate_unitary(original, mapped)
            if "failed" not in msg.lower() and "cannot compare" not in msg.lower():
                return correct, msg, "unitary"

            # Fall back to measurement
            correct, msg = self.functional_validator.validate_measurement(
                original, mapped
            )
            return correct, f"Unitary failed, used measurement: {msg}", "measurement"

        elif preferred_method == "measurement":
            correct, msg = self.functional_validator.validate_measurement(
                original, mapped
            )
            return correct, msg, "measurement"
        elif preferred_method == "skip":
            return True, "Functional test skipped", "skip"
        else:
            raise ValueError(f"Unknown method: {preferred_method}")

    def _choose_validation_method(self, circuit: QuantumCircuit) -> str:
        """Choose appropriate validation method based on circuit properties"""
        num_qubits = circuit.num_qubits
        has_measurements = circuit.num_clbits > 0

        # If circuit has measurements, must use measurement validation
        if has_measurements:
            return "measurement"

        if num_qubits <= 9:
            return "blind"
        else:
            return "skip"

        # # Choose based on size
        # if num_qubits <= 10:
        #     return 'statevector'
        # elif num_qubits <= 15:
        #     return 'unitary'
        # elif num_qubits <= 20:
        #     return 'measurement'
        # else:
        #     return 'skip'

    def test_circuit(
        self,
        original: QuantumCircuit,
        mapped: QuantumCircuit,
        method: Literal["auto", "statevector", "unitary", "measurement"] = "auto",
        verbose: bool = False,
    ) -> dict:
        """
        Test a single mapped circuit for correctness

        Args:
            original: Original circuit
            mapped: Mapped circuit
            method: Testing method ('auto' chooses based on circuit size)
            verbose: Print detailed output

        Returns:
            Dictionary with test results
        """
        results = {
            "circuit_name": getattr(original, "name", "unnamed"),
            "backend": self.backend.name,
            "num_qubits": original.num_qubits,
            "original_depth": original.depth(),
            "original_gate_count": len(original),
            "mapped_depth": mapped.depth(),
            "mapped_gate_count": len(mapped),
            "topology_compliant": False,
            "functionally_correct": False,
            "test_method": method,
            "messages": [],
        }

        # Test topology compliance
        compliant, msg = self.topology_validator.validate(mapped)
        results["topology_compliant"] = compliant
        results["messages"].append(("Topology", msg))

        # Choose functional test method
        if method == "auto":
            method = self._choose_validation_method(original)
            results["test_method"] = method

        correct, msg, actual_method = self._validate_with_fallback(
            original, mapped, method
        )

        results["functionally_correct"] = correct
        results["test_method"] = actual_method
        results["messages"].append(("Functional", msg))
        results["passed"] = compliant and correct

        if verbose:
            self._print_results(results)

        return results

    def test_algorithm(
        self,
        algorithm: QubitMapper,
        circuits: list[QuantumCircuit],
        pauli_strings_set: list[list[PauliString]] = [],
        method: str = "auto",
        verbose: bool = True,
    ) -> list[dict]:
        """
        Test an algorithm on multiple circuits

        Args:
            algorithm: Algorithm with run_x_circuit or run_x_hamiltonian
            circuits: List of test circuits
            method: Testing method
            verbose: Print results for each circuit

        Returns:
            List of result dictionaries
        """
        if verbose:
            print(f"\nTesting algorithm on backend: {self.backend.name}")
            print(f"Testing {len(circuits)} circuits...\n")

        results = []

        if algorithm.supports_circuit_mapping():
            for i, circuit in enumerate(circuits, 1):
                if verbose:
                    print(f"[{i}/{len(circuits)}] Testing {circuit.name}...", end=" ")

                # Apply algorithm
                mapped = algorithm.map_circuit(
                    circuit, backend=self.backend, circuit_name="test_mapping"
                )
                if mapped is None:
                    if verbose:
                        print("✗ ERROR: Mapping failed")
                    results.append(
                        {
                            "circuit_name": getattr(circuit, "name", "unnamed"),
                            "backend": self.backend.name,
                            "num_qubits": circuit.num_qubits,
                            "original_depth": circuit.depth(),
                            "original_gate_count": len(circuit),
                            "mapped_depth": None,
                            "mapped_gate_count": None,
                            "topology_compliant": False,
                            "functionally_correct": False,
                            "test_method": method,
                            "messages": [("Mapping", "Mapping failed")],
                            "passed": False,
                        }
                    )
                    continue
                # Test
                result = self.test_circuit(
                    circuit, mapped.optimised_circuit, method, verbose=False
                )
                print(result["messages"])
                results.append(result)

                if verbose:
                    status = "✓ PASS" if result["passed"] else "✗ FAIL"
                    print(status)

        if algorithm.supports_raw_pauli_string_mapping():
            for i, pauli_strings in enumerate(pauli_strings_set, 1):
                circuit = convert_pauli_strings_to_circuit(
                    pauli_strings, num_qubits=len(pauli_strings[0])
                )
                mapped = algorithm.map_pauli_strings(
                    pauli_strings, backend=self.backend, circuit_name="test_mapping"
                )

                if mapped is None:
                    if verbose:
                        print("✗ ERROR: Mapping failed")
                    results.append(
                        {
                            "circuit_name": getattr(circuit, "name", "unnamed"),
                            "backend": self.backend.name,
                            "num_qubits": circuit.num_qubits,
                            "original_depth": circuit.depth(),
                            "original_gate_count": len(circuit),
                            "mapped_depth": None,
                            "mapped_gate_count": None,
                            "topology_compliant": False,
                            "functionally_correct": False,
                            "test_method": method,
                            "messages": [("Mapping", "Mapping failed")],
                            "passed": False,
                        }
                    )
                    continue
                # Test
                result = self.test_circuit(
                    circuit, mapped.optimised_circuit, method, verbose=False
                )
                results.append(result)

                if verbose:
                    status = "✓ PASS" if result["passed"] else "✗ FAIL"
                    print(status)

        if verbose:
            self._print_summary(results, algorithm_name=algorithm.name())

        return results

    def _print_results(self, results: dict):
        """Pretty print single test result"""
        status = "✓ PASSED" if results["passed"] else "✗ FAILED"
        print(f"\n{'=' * 70}")
        print(f"Test: {status}")
        print(f"{'=' * 70}")
        print(f"Circuit: {results['circuit_name']}")
        print(f"Backend: {results['backend']}")
        print(f"Qubits: {results['num_qubits']}")
        print(f"Depth: {results['original_depth']} → {results['mapped_depth']}")
        print(
            f"Gates: {results['original_gate_count']} → {results['mapped_gate_count']}"
        )
        print(f"Method: {results['test_method']}")
        print(f"\nResults:")
        print(f"  Topology compliant: {'✓' if results['topology_compliant'] else '✗'}")
        print(
            f"  Functionally correct: {'✓' if results['functionally_correct'] else '✗'}"
        )
        print(f"\nDetails:")
        for category, msg in results["messages"]:
            print(f"  {category}: {msg}")
        print(f"{'=' * 70}\n")

    def _print_summary(self, results: list[dict], algorithm_name: str = ""):
        """Print summary of multiple tests"""
        passed = sum(1 for r in results if r["passed"])
        total = len(results)

        print(f"\n{'=' * 70}")
        print(f"TEST SUMMARY")
        print(f"{'=' * 70}")
        print(f"Backend: {self.backend.name}")
        print(f"Mapper: {algorithm_name}")
        print(f"Total tests: {total}")
        print(f"Passed: {passed} ✓")
        print(f"Failed: {total - passed} ✗")
        print(f"Success rate: {100 * passed / total:.1f}%")

        # Show failed tests
        failed = [r for r in results if not r["passed"]]
        if failed:
            print(f"\nFailed circuits:")
            for r in failed:
                reasons = []
                if not r["topology_compliant"]:
                    reasons.append("topology")
                if not r["functionally_correct"]:
                    reasons.append("functional")
                print(f"  • {r['circuit_name']} ({', '.join(reasons)})")

        print(f"{'=' * 70}\n")
