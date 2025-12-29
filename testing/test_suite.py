from typing import Literal
from qiskit import QuantumCircuit

from .validators.topology_validator import TopologyValidator
from .validators.functional_validator import FunctionalValidator


class CorrectnessTestSuite:
    """Comprehensive test suite for qubit mapping algorithms"""
    
    def __init__(self, coupling_map):
        """
        Args:
            coupling_map: Hardware topology as list of [q1, q2] pairs
        """
        self.topology_validator = TopologyValidator(coupling_map)
        self.functional_validator = FunctionalValidator()
    
    def test_circuit(self,
                    original: QuantumCircuit,
                    mapped: QuantumCircuit,
                    method: Literal['auto', 'statevector', 'unitary', 'measurement'] = 'auto',
                    verbose: bool = False) -> dict:
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
            'circuit_name': getattr(original, 'name', 'unnamed'),
            'num_qubits': original.num_qubits,
            'original_depth': original.depth(),
            'mapped_depth': mapped.depth(),
            'topology_compliant': False,
            'functionally_correct': False,
            'test_method': method,
            'messages': []
        }
        
        # Test topology compliance
        compliant, msg = self.topology_validator.validate(mapped)
        results['topology_compliant'] = compliant
        results['messages'].append(('Topology', msg))
        
        # Choose functional test method
        if method == 'auto':
            num_qubits = original.num_qubits
            if num_qubits <= 10:
                method = 'statevector'
            elif num_qubits <= 15 and original.num_clbits == 0:
                method = 'unitary'
            else:
                method = 'measurement'
            results['test_method'] = method
        
        # Run functional test
        if method == 'statevector':
            correct, msg = self.functional_validator.validate_statevector(
                original, mapped
            )
        elif method == 'unitary':
            correct, msg = self.functional_validator.validate_unitary(
                original, mapped
            )
        elif method == 'measurement':
            correct, msg = self.functional_validator.validate_measurement(
                original, mapped
            )
        else:
            raise ValueError(f"Unknown method: {method}")
        
        results['functionally_correct'] = correct
        results['messages'].append(('Functional', msg))
        results['passed'] = compliant and correct
        
        if verbose:
            self._print_results(results)
        
        return results
    
    def test_algorithm(self,
                      algorithm,
                      circuits: list[QuantumCircuit],
                      method: str = 'auto',
                      verbose: bool = True) -> list[dict]:
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
        results = []
        
        for circuit in circuits:
            # Apply algorithm
            if hasattr(algorithm, 'run_x_circuit'):
                mapped = algorithm.run_x_circuit(circuit)
            elif hasattr(algorithm, 'run_x_hamiltonian'):
                mapped = algorithm.run_x_hamiltonian(circuit)
            else:
                raise ValueError(
                    "Algorithm must have run_x_circuit or run_x_hamiltonian"
                )
            
            # Test
            result = self.test_circuit(circuit, mapped, method, verbose)
            results.append(result)
        
        if verbose:
            self._print_summary(results)
        
        return results
    
    def _print_results(self, results: dict):
        """Pretty print single test result"""
        status = "✓ PASSED" if results['passed'] else "✗ FAILED"
        print(f"\n{'='*60}")
        print(f"Test: {status}")
        print(f"{'='*60}")
        print(f"Circuit: {results['circuit_name']}")
        print(f"Qubits: {results['num_qubits']}")
        print(f"Depth: {results['original_depth']} → {results['mapped_depth']}")
        print(f"Method: {results['test_method']}")
        print(f"\nResults:")
        print(f"  Topology compliant: {results['topology_compliant']}")
        print(f"  Functionally correct: {results['functionally_correct']}")
        for category, msg in results['messages']:
            print(f"  {category}: {msg}")
        print(f"{'='*60}\n")
    
    def _print_summary(self, results: list[dict]):
        """Print summary of multiple tests"""
        passed = sum(1 for r in results if r['passed'])
        total = len(results)
        print(f"\n{'='*60}")
        print(f"SUMMARY: {passed}/{total} tests passed")
        print(f"{'='*60}\n")
