import importlib
import inspect
from typing import Dict, List, Tuple, Any

from qiskit.providers import BackendV2

from quantum_compiler.backends.custom_qiskit import ResearchBackend
from quantum_compiler.topologies.base_topology import Topology
from topologies.topologies import topology_functions


class BackendFactory:
    """
    A factory that discovers topologies and builds Qiskit BackendV2 objects.
    """
    
    def __init__(self):
        self._definitions: Dict[str, Topology] = {}

        self._register_from_dict(topology_functions)

    def _register_from_dict(self, topology_dict: Dict) -> None:
        for name, func in topology_dict.items():
            try:
                # Assuming that dict functions return (coupling_map, num_qubits)
                coupling_map, n_qubits = func()
                print(f"Registering legacy backend: {name} with {n_qubits} qubits")
                
                # Creating a dynamic anonymous class to wrap this data
                def _make_wrapper(bound_name=name, bound_coupling=coupling_map, bound_n_qubits=n_qubits):
                    class LegacyWrapper(Topology):
                        @property
                        def name(self_inner): return bound_name
                        @property
                        def num_qubits(self_inner): return bound_n_qubits
                        def get_coupling_map(self_inner): return bound_coupling
                    return LegacyWrapper()
                
                self._definitions[name] = _make_wrapper()
                print(f"Registered legacy backend: {name}")
            except Exception as e:
                print(f"Failed to register legacy backend {name}: {e}")

    def get_backend(self, name: str) -> BackendV2:
        if name not in self._definitions:
            available = list(self._definitions.keys())
            raise ValueError(f"Backend '{name}' not found. Available: {available}")
        
        definition = self._definitions[name]
        
        return ResearchBackend(
            name=definition.name,
            graph_list=definition.get_coupling_map(),
            num_qubits=definition.num_qubits,
        )

    def get_topology_data(self, name: str) -> Tuple[List[List[int]], int]:
        """Returns (coupling_map, num_qubits)"""
        if name not in self._definitions:
            raise ValueError(f"Backend '{name}' not found.")
        
        def_ = self._definitions[name]
        return def_.get_coupling_map(), def_.num_qubits

    def list_available(self) -> List[str]:
        return list(self._definitions.keys())

    def get_all_backends(self) -> Dict[str, BackendV2]:
        """Instantiates and returns all available backends."""
        return {name: self.get_backend(name) for name in self._definitions}
