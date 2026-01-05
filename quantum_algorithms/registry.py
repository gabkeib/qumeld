from typing import Dict, List

from qiskit import QuantumCircuit
from quantum_algorithms.base_provider import AlgorithmProvider
from quantum_algorithms.providers.hamiltonian_provider import HamiltonianProvider

class AlgorithmRegistry:
    """
    Central hub for retrieving quantum circuits and operators.
    """
    
    def __init__(self, load_defaults: bool = True):
        self._providers: Dict[str, AlgorithmProvider] = {}
        self._available_algorithms: List[str] = []
        if load_defaults:
            self._discover_default_algorithms()

    def register(self, name: str, provider: AlgorithmProvider):
        """Manually register a provider under a specific name."""
        self._providers[name] = provider

    def _discover_default_algorithms(self):
        """Auto-discover known providers and files."""
        ham_provider = HamiltonianProvider()
        self.register("hamiltonian", ham_provider) 

        self._available_algorithms.extend(ham_provider.available_algorithms)

    def get_circuit(self, **kwargs) -> QuantumCircuit:
        """
        Directly get a circuit by algorithm name.
        """
        name = kwargs.get("name", None)
        provider = self._get_provider_or_error(name)
        
        if not provider.supports_circuits:
            raise ValueError(f"Algorithm '{name}' does not support circuit generation.")
            
        return provider.get_circuit(**kwargs)

    def get_pauli_strings(self, **kwargs) -> List[str]:
        """
        Directly get Pauli strings by algorithm name.
        """
        provider = self._get_provider_or_error(kwargs.get("name", None))
        
        if not provider.supports_pauli_strings:
            raise ValueError(f"Algorithm '{kwargs.get('name', None)}' does not support Pauli string generation.")
            
        return provider.get_pauli_strings(**kwargs)

    def list_algorithms(self) -> List[str]:
        """
        List all available algorithms.
        """
        return self._available_algorithms.copy()
    
    def _get_provider_or_error(self, name: str) -> AlgorithmProvider:
        for provider_name in self._providers:
            if self._providers[provider_name].is_supported_algorithm(name):
                return self._providers[provider_name]

        raise ValueError(f"Algorithm '{name}' not found. Available: {self.list_algorithms()}")
