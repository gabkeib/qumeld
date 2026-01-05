# qiskit_ai_worker.py (runs in separate environment)
import sys
import pickle
from typing import List
from qiskit.quantum_info import SparsePauliOp
from qiskit import QuantumCircuit, generate_preset_pass_manager
from qiskit.circuit.library import PauliEvolutionGate 
from qiskit_ibm_transpiler import generate_ai_pass_manager
from qiskit.transpiler import PassManager
from stats_utils.estimated_value import calculate_estimated_average_value_and_dispersion
from quantum_compiler.core.types import CircuitOptimisationResult
from time import time
import numpy as np
from qiskit_ibm_transpiler.ai.routing import AIRouting


from qiskit.providers import BackendV2, Options
from qiskit.transpiler import Target, InstructionProperties, PassManager
from qiskit.circuit.library import XGate, SXGate, RZGate, CZGate, CXGate, PauliEvolutionGate, SwapGate
from qiskit.circuit import Measure, Delay, Parameter, Reset
from qiskit_ibm_transpiler.ai.synthesis import AILinearFunctionSynthesis
from qiskit_ibm_transpiler.ai.collection import CollectLinearFunctions
from qiskit_ibm_transpiler.ai.synthesis import AIPauliNetworkSynthesis
from qiskit_ibm_transpiler.ai.collection import CollectPauliNetworks

class CustomBackend(BackendV2):
    """Reconstructed CustomBackend in the worker environment"""
    def __init__(self, name: str, graph_list: List[List[int]]):
        super().__init__(name=f"{name} backend")
        
        # Convert graph_list to edge set
        edges = [(edge[0], edge[1]) for edge in graph_list]
        edge_properties = {edge: None for edge in edges}
        
        # Determine num_qubits from graph
        num_qubits = max(max(edge) for edge in graph_list) + 1 if graph_list else 0
        
        rng = np.random.default_rng(seed=12345678942)
        rz_props = {}
        x_props = {}
        sx_props = {}
        measure_props = {}
        delay_props = {}
        
        self._target = Target("Target", num_qubits=num_qubits)
        
        # Add 1q gates
        for i in range(num_qubits):
            qarg = (i,)
            rz_props[qarg] = InstructionProperties(error=0.0, duration=0.0)
            x_props[qarg] = InstructionProperties(
                error=rng.uniform(1e-6, 1e-4),
                duration=rng.uniform(1e-8, 9e-7),
            )
            sx_props[qarg] = InstructionProperties(
                error=rng.uniform(1e-6, 1e-4),
                duration=rng.uniform(1e-8, 9e-7),
            )
            measure_props[qarg] = InstructionProperties(
                error=rng.uniform(1e-3, 1e-1),
                duration=rng.uniform(1e-8, 9e-7),
            )
            delay_props[qarg] = None
        
        self._target.add_instruction(XGate(), x_props)
        self._target.add_instruction(SXGate(), sx_props)
        self._target.add_instruction(RZGate(Parameter("theta")), rz_props)
        self._target.add_instruction(Measure(), measure_props)
        self._target.add_instruction(Reset(), measure_props)
        self._target.add_instruction(Delay(Parameter("t")), delay_props)
        self._target.add_instruction(SwapGate(), edge_properties)
        self._target.add_instruction(CXGate(), edge_properties)
        
        # Add CZ with properties
        cz_props = {}
        for edge in graph_list:
            cz_props[(edge[0], edge[1])] = InstructionProperties(
                error=rng.uniform(7e-4, 5e-3),
                duration=rng.uniform(1e-8, 9e-7),
            )
        self._target.add_instruction(CZGate(), cz_props)
 
    @property
    def target(self):
        return self._target
 
    @property
    def max_circuits(self):
        return None
 
    @classmethod
    def _default_options(cls):
        return Options(shots=1024)
 
    def run(self, circuit, **kwargs):
        raise NotImplementedError("not implemented")

def reconstruct_backend(backend_config: dict) -> CustomBackend:
    """Reconstruct CustomBackend from serialized configuration"""
    print(f"Reconstructing CustomBackend: '{backend_config['name']}'")
    print(f"  Qubits: {backend_config['num_qubits']}")
    print(f"  Edges: {len(backend_config['graph_list'])}")
    
    backend = CustomBackend(
        name=backend_config['name'],
        graph_list=backend_config['graph_list']
    )
    
    print(f"Backend reconstructed successfully with {backend.num_qubits} qubits")
    return backend

def qiskit_ai_optimise_circuit(circuit: QuantumCircuit, backend: CustomBackend) -> QuantumCircuit:
    synthesis_pm = generate_preset_pass_manager(
        optimization_level=0,  # Just synthesis, no optimization
        backend=backend,
        initial_layout=None
    )
    synthesized = synthesis_pm.run(circuit)
    ai_passmanager = PassManager(
        [
            AIRouting(
                backend=backend,
                optimization_level=3,
                layout_mode="optimize",
                local_mode=True,
            ),
            # CollectLinearFunctions(),  # Collect Linear Function blocks
            # AILinearFunctionSynthesis(
            #     backend=backend, local_mode=True
            # ),  # Re-synthesize Linear Function blocks
            # CollectPauliNetworks(),  # Collect Pauli Networks blocks
            # AIPauliNetworkSynthesis(
            #     backend=backend, local_mode=True
            # ),
        ]
    )
 
    # ai_transpiler_pass_manager: PassManager = generate_preset_pass_manager(optimization_level=3, backend=backend)
    circuit = ai_passmanager.run(synthesized)
    return circuit

def run_qiskit_ai_circuit(circuit, backend, algorithm_name):
    time_start = time()

    # print("NOT HERE")

    backend = reconstruct_backend(backend)

    compiled_circuit = qiskit_ai_optimise_circuit(circuit, backend)
    calculated_statistics = calculate_estimated_average_value_and_dispersion(circuit, compiled_circuit, None)
    return CircuitOptimisationResult(
        name=algorithm_name,
        swap_count=compiled_circuit.count_ops().get('swap', 0),
        cx_count=compiled_circuit.count_ops().get('cx', 0) + compiled_circuit.count_ops().get('swap', 0) * 3,
        depth=compiled_circuit.depth(),
        optimisation_time=time() - time_start,
        expected_value=calculated_statistics.expected_value_after,
        variance=calculated_statistics.variance_after,
        fidelity=calculated_statistics.fidelity,
        optimised_circuit=compiled_circuit,
        mapper="qiskit_ai"
    )

if __name__ == "__main__":
    result_path = None
    try:
        result_path = sys.argv[1] if len(sys.argv) > 1 else None
        
        print("Worker started, reading input...")
        sys.stdout.flush()  # Flush output immediately
        
        input_data = pickle.load(sys.stdin.buffer)
        
        function_name = input_data['function']
        args = input_data['args']
        kwargs = input_data['kwargs']
        
        print(f"Calling function: {function_name}")
        sys.stdout.flush()
        
        if function_name == 'run_qiskit_ai_circuit':
            result = run_qiskit_ai_circuit(*args, **kwargs)
        else:
            raise ValueError(f"Unknown function: {function_name}")
        
        print("Function completed, writing result...")
        sys.stdout.flush()
        
        # Write result to file
        if result_path:
            with open(result_path, 'wb') as f:
                pickle.dump(result, f)
            print(f"Result written successfully to {result_path}")
            sys.stdout.flush()
        else:
            # Fallback to stdout
            pickle.dump(result, sys.stdout.buffer)
            sys.stdout.buffer.flush()
        
    except Exception as e:
        import traceback
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        print(f"\n{'='*60}")
        print("ERROR in worker:")
        print(error_info['traceback'])
        print(f"{'='*60}\n")
        sys.stdout.flush()
        
        if result_path:
            try:
                with open(result_path, 'wb') as f:
                    pickle.dump(error_info, f)
            except Exception as write_error:
                print(f"Failed to write error to file: {write_error}")
        else:
            pickle.dump(error_info, sys.stdout.buffer)
            sys.stdout.buffer.flush()
        
        sys.exit(1)
