from qiskit import QuantumCircuit
from quantum_algorithms.base_provider import AlgorithmProvider
from quantum_algorithms.providers import hamiltonian_provider
from typing import List
from qiskit.quantum_info import SparsePauliOp
from qiskit.circuit.library import EfficientSU2, QAOAAnsatz
import numpy as np

class AnsatzProvider(AlgorithmProvider):
    """
    A provider for quantum ansatz circuits used in variational quantum algorithms.
    """

    def __init__(self):
        self._available_algorithms = ["qaoa_ansatz", "efficient_su2"]

    
    @property
    def available_algorithms(self) -> list[str]:
        return self._available_algorithms.copy()
    
    @property
    def supports_circuits(self) -> bool:
        return True
    
    @property
    def supports_pauli_strings(self) -> bool:
        return False
    
    def get_circuit(self, **kwargs):
        algorithm = kwargs.get("name", None)
        num_qubits = kwargs.get("num_qubits", 4)
        reps = kwargs.get("reps", 1)
        bind_parameters = kwargs.get("bind_parameters", True)

        if algorithm == "qaoa_ansatz":
            hamiltonian = self._generate_qaoa_max_cut(
                kwargs.get("graph", None),
            )

            ansatz = QAOAAnsatz(cost_operator=hamiltonian, reps=reps)
            qc = QuantumCircuit(num_qubits)
            qc.append(ansatz.decompose(), qc.qubits)
            
            if bind_parameters and qc.num_parameters > 0:
                param_values = kwargs.get("parameter_values", None)
                if param_values is None:
                    param_values = np.random.uniform(0, 2 * np.pi, qc.num_parameters)
                qc = qc.assign_parameters(param_values)
            
            return qc.decompose().decompose()
        
        elif algorithm == "efficient_su2":
            ansatz = EfficientSU2(num_qubits=num_qubits, reps=reps, entanglement="linear")
            qc = QuantumCircuit(num_qubits)
            qc.append(ansatz.decompose(), qc.qubits)
            
            if bind_parameters and qc.num_parameters > 0:
                param_values = kwargs.get("parameter_values", None)
                if param_values is None:
                    param_values = np.random.uniform(0, 2 * np.pi, qc.num_parameters)
                qc = qc.assign_parameters(param_values)
            
            return qc.decompose()
        else:
            raise ValueError(f"Unsupported ansatz algorithm: {algorithm}")
        
    def _generate_qaoa_max_cut(self, graph: List[List[int]]) -> SparsePauliOp:
        pauli_list = []
        coeffs = []
        n = len(graph)

        for i in range(n):
            for j in range(i + 1, n):
                if graph[i][j] == 1:
                    s = ["I"] * n
                    s[i] = "Z"
                    s[j] = "Z"
                    # Qiskit uses little-endian (q0 is rightmost)
                    pauli_list.append("".join(s)[::-1])
                    coeffs.append(0.5)

        return SparsePauliOp(pauli_list, coeffs=coeffs)

    def get_pauli_strings(self, **kwargs):
        raise NotImplementedError("Pauli strings are not supported by AnsatzProvider.")
    
    def is_supported_algorithm(self, name):
        return name in self.available_algorithms
    
