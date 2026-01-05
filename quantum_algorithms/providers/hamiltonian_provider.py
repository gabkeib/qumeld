import json
from typing import List, Optional, Dict
from pathlib import Path

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp

from quantum_algorithms.base_provider import AlgorithmProvider
from quantum_compiler.utils.paths import get_project_root
from qiskit.circuit.library import PauliEvolutionGate


class HamiltonianProvider(AlgorithmProvider):
    """
    A provider for Hamiltonian operators used in quantum algorithms.
    """

    def __init__(self, hamiltonian_dir: str = None, default_name: str = "demo"):
        if hamiltonian_dir is None:
            project_root = get_project_root()
            hamiltonian_dir = project_root / "quantum_algorithms" / "hamiltonian"

        self.hamiltonian_dir = Path(hamiltonian_dir)
        self.default_name = default_name
        self._cache: Dict[str, SparsePauliOp] = {}
    
        self._available_algorithms = self._collect_algorithms()

    def _collect_algorithms(self) -> List[str]:
        if not self.hamiltonian_dir.exists():
            return []
        from_json = [f.stem for f in self.hamiltonian_dir.glob("*.json")]
        from_json.append("qaoa")  # Include dynamic QAOA

        return from_json

    @property
    def available_algorithms(self) -> List[str]:
        return self._available_algorithms.copy()

    @property
    def supports_circuits(self) -> bool:
        return True

    @property
    def supports_pauli_strings(self) -> bool:
        return True

    def get_circuit(self, **kwargs) -> QuantumCircuit:
        op = self._generate_operator(**kwargs)
        evo_gate = PauliEvolutionGate(op, time=1.0)
        circuit = QuantumCircuit(op.num_qubits)
        circuit.append(evo_gate, circuit.qubits)

        return circuit.decompose()

    def get_pauli_strings(self, **kwargs) -> List[str]:
        op = self._generate_operator(**kwargs)

        return op.paulis.to_labels()

    def _generate_operator(self, **kwargs) -> SparsePauliOp:
        """
        Generates a SparsePauliOp based on provided kwargs.

        Args:
            **kwargs: 
                - name (str): name of the JSON file to load.
                - graph (List[List[int]]): adjacency matrix for dynamic QAOA generation.
        """

        op: Optional[SparsePauliOp] = None
        target_name = kwargs.get("name", None)

        if target_name != "qaoa":
            op = self._load_from_json(target_name)
        elif "graph" in kwargs:
            op = self._generate_qaoa_max_cut(kwargs["graph"])
        else:
             raise ValueError("HamiltonianProvider requires 'name' (or default_name) or 'graph'")

        return op

    def _load_from_json(self, name: str) -> SparsePauliOp:
        if name in self._cache:
            return self._cache[name]

        file_path = self.hamiltonian_dir / f"{name}.json"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Benchmark {name} not found at {file_path}")

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Assuming JSON structure: {'pauli_strings': [{'pauli': 'ZZ', 'coeff': 1.0}, ...]}
            paulis = [op['pauli'] for op in data['pauli_strings']]
            coeffs = [op.get('coeff', 1.0) for op in data['pauli_strings']]
            
            op = SparsePauliOp(paulis, coeffs=coeffs)
            self._cache[name] = op
            return op
            
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in {file_path}")

    def _generate_qaoa_max_cut(self, graph: List[List[int]]) -> SparsePauliOp:
        pauli_list = []
        coeffs = []
        n = len(graph)
        
        for i in range(n):
            for j in range(i + 1, n):
                if graph[i][j] == 1:
                    s = ['I'] * n
                    s[i] = 'Z'
                    s[j] = 'Z'
                    # Qiskit uses little-endian (q0 is rightmost)
                    pauli_list.append("".join(s)[::-1]) 
                    coeffs.append(0.5)

        return SparsePauliOp(pauli_list, coeffs=coeffs)

    def is_supported_algorithm(self, name: str) -> bool:
        return name in self.available_algorithms
