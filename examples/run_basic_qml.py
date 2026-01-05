from readline import backend
from qiskit import QuantumCircuit
from qiskit.circuit import Parameter, ParameterVector
from qiskit.primitives import StatevectorEstimator
from qiskit.quantum_info import SparsePauliOp
from qiskit.providers import BackendV2
from scipy.optimize import minimize, OptimizeResult
import numpy as np
from typing import Dict, Optional, List, Tuple
from numpy.typing import NDArray

from quantum_compiler.backends.factory import BackendFactory
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.mappers.base_mapper import QubitMapper


def create_feature_map(num_qubits: int, features: NDArray[np.float64]) -> QuantumCircuit:
    """Create a feature map circuit to encode classical data"""
    qc = QuantumCircuit(num_qubits)
    
    for i in range(num_qubits):
        qc.h(i)
    
    for i in range(min(num_qubits, len(features))):
        qc.rz(2 * features[i], i)
    
    for i in range(num_qubits - 1):
        qc.cx(i, i + 1)
    
    return qc

def create_ansatz(num_qubits: int, num_layers: int = 2) -> Tuple[QuantumCircuit, ParameterVector]:
    """Create a variational ansatz with trainable parameters"""
    params = ParameterVector('θ', num_qubits * num_layers * 3)
    qc = QuantumCircuit(num_qubits)
    
    param_idx = 0
    for layer in range(num_layers):
        for i in range(num_qubits):
            qc.rx(params[param_idx], i)
            param_idx += 1
            qc.ry(params[param_idx], i)
            param_idx += 1
            qc.rz(params[param_idx], i)
            param_idx += 1
        
        for i in range(num_qubits - 1):
            qc.cx(i, i + 1)
        if num_qubits > 2:
            qc.cx(num_qubits - 1, 0)
    
    return qc, params

# Complete QML Circuit
def create_qml_circuit(
    num_qubits: int, 
    features: NDArray[np.float64], 
    params_values: NDArray[np.float64], 
    num_layers: int = 2
) -> QuantumCircuit:
    """Combine feature map and ansatz"""
    qc = create_feature_map(num_qubits, features)
    
    ansatz, params = create_ansatz(num_qubits, num_layers)
    
    param_dict = {params[i]: params_values[i] for i in range(len(params))}
    bound_ansatz = ansatz.assign_parameters(param_dict)
    
    qc = qc.compose(bound_ansatz)
    
    return qc

# Cost Function
class QMLCostFunction:
    """Cost function for QML optimization"""
    def __init__(
            self,
            X_train: NDArray[np.float64], 
            y_train: NDArray[np.float64], 
            num_qubits: int,
            num_layers: int, 
            observable: SparsePauliOp,
            backend: BackendV2,
            qubit_mapper: QubitMapper
        ):
        self.X_train = X_train
        self.y_train = y_train
        self.num_qubits = num_qubits
        self.num_layers = num_layers
        self.observable = observable
        self.backend = backend
        self.qubit_mapper = qubit_mapper
        self.estimator = StatevectorEstimator()
        self.iteration = 0
    
    def __call__(self, params):
        """Compute the cost for given parameters"""
        total_cost = 0
        
        for x, y in zip(self.X_train, self.y_train):
            qc = create_qml_circuit(self.num_qubits, x, params, self.num_layers)
            
            mapped_result = self.qubit_mapper.map_circuit(qc, self.backend)
            mapped_qc = mapped_result.optimised_circuit
            
            expanded_observable = self._expand_observable(mapped_qc.num_qubits)
            
            job = self.estimator.run([(mapped_qc, expanded_observable)])
            result = job.result()
            expectation = result[0].data.evs
            
            total_cost += (expectation - y) ** 2
        
        avg_cost = total_cost / len(self.X_train)
        
        self.iteration += 1
        if self.iteration % 1 == 0:
            print(f"Iteration {self.iteration}: Cost = {avg_cost:.6f}, Params[0:3] = {params[:3]}")
        
        return float(avg_cost)  

    def _expand_observable(self, num_qubits_mapped: int) -> SparsePauliOp:
        """Expand observable to match mapped circuit size by padding with identity"""
        original_pauli = self.observable.paulis.to_labels()[0]
        
        padding = 'I' * (num_qubits_mapped - self.num_qubits)
        expanded_pauli = original_pauli + padding
        
        return SparsePauliOp.from_list([(expanded_pauli, 1.0)])

# Example Usage
def run_qml_example():
    """Run a complete QML example with COBYLA optimizer"""
    
    np.random.seed(42)
    X_train = np.random.randn(20, 3)  # 20 samples, 3 features
    y_train = np.sin(X_train[:, 0]) * np.cos(X_train[:, 1])  # Target function
    y_train = (y_train - y_train.min()) / (y_train.max() - y_train.min())  # Normalize to [0,1]
    y_train = 2 * y_train - 1  # Scale to [-1, 1]
    
    # Setup
    num_qubits = 3
    num_layers = 2
    num_params = num_qubits * num_layers * 3
    
    observable = SparsePauliOp.from_list([("Z" + "I" * (num_qubits - 1), 1.0)])
    
    # using the backend and mappers from the framework
    backned_factory = BackendFactory()
    backend = backned_factory.get_backend("rigetti_novera_q9")

    mapper_registry = MapperRegistry()
    qubit_mapper: QubitMapper = mapper_registry.get_mapper("lightSABRE")

    
    print(f"QML Training with COBYLA Optimizer")
    print(f"Number of qubits: {num_qubits}")
    print(f"Number of layers: {num_layers}")
    print(f"Number of parameters: {num_params}")
    print(f"Qubit mapping: {qubit_mapper.name}")
    print(f"Backend: {backend.name}")
    print(f"Training samples: {len(X_train)}\n")
    
    # Initialize parameters
    initial_params = np.random.randn(num_params) * 0.5
    
    # Create cost function
    cost_func = QMLCostFunction(
        X_train, y_train, num_qubits, num_layers, 
        observable, backend, qubit_mapper
    )
    
    # Optimize with COBYLA
    result = minimize(
        cost_func,
        initial_params,
        method='COBYLA',
        options={
            'maxiter': 50,  # Reduced for debugging
            'rhobeg': 1.0,  # Increased step size
            'tol': 1e-4,
            'disp': True  # Show optimization progress
        }
    )
    
    print(f"Optimization completed!")
    print(f"Final cost: {result.fun:.6f}")
    print(f"Success: {result.success}")
    print(f"Number of iterations: {result.nfev}")
    print(f"Optimal parameters (first 5): {result.x[:5]}")
    
    # Test on training data
    # Test on training data
    print("Predictions on training data (first 5 samples):")
    for i in range(min(5, len(X_train))):
        qc = create_qml_circuit(num_qubits, X_train[i], result.x, num_layers)
        mapped_result = qubit_mapper.map_circuit(qc, backend)
        mapped_qc = mapped_result.optimised_circuit
        
        # Expand observable
        padding = 'I' * (mapped_qc.num_qubits - num_qubits)
        expanded_pauli = "Z" + "I" * (num_qubits - 1) + padding
        expanded_observable = SparsePauliOp.from_list([(expanded_pauli, 1.0)])
        
        estimator = StatevectorEstimator()
        job = estimator.run([(mapped_qc, expanded_observable)])
        prediction = job.result()[0].data.evs
        
        print(f"  Sample {i}: Prediction = {prediction:.4f}, True = {y_train[i]:.4f}")
        
    return result

# Run the example
if __name__ == "__main__":
    optimal_params = run_qml_example()
