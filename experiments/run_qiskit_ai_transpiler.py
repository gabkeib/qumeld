from experiments.run_qiskit import CustomBackend
from typing import List
from qiskit import QuantumCircuit
from experiments.types import CircuitOptimisationResult
import subprocess
import pickle
from pathlib import Path
import os

QISKIT_AI_PYTHON = ".venv-qiskit-ai/bin/python"

def serialize_backend(backend: CustomBackend) -> dict:
    """Convert CustomBackend to a serializable dictionary"""
    # Extract the graph from the target's CZ gate properties
    graph_list = []
    
    # Get CZ gate to extract the coupling map
    cz_gate_name = 'cz'
    if cz_gate_name in backend.target:
        cz_qargs = backend.target[cz_gate_name].keys()
        for qarg in cz_qargs:
            if len(qarg) == 2:  # It's a 2-qubit gate
                graph_list.append([qarg[0], qarg[1]])
    
    # If no CZ gates, try CX gates
    if not graph_list:
        cx_gate_name = 'cx'
        if cx_gate_name in backend.target:
            cx_qargs = backend.target[cx_gate_name].keys()
            for qarg in cx_qargs:
                if len(qarg) == 2:
                    graph_list.append([qarg[0], qarg[1]])
    
    return {
        'name': backend.name.replace(' backend', ''),  # Remove ' backend' suffix
        'graph_list': graph_list,
        'num_qubits': backend.num_qubits
    }

def call_qiskit_ai_function(function_name: str, *args, **kwargs):
    """Call a function in the separate qiskit environment"""
    # Path to the Python interpreter in your other environment
    
    input_data = {
        'function': function_name,
        'args': args,
        'kwargs': kwargs
    }
    
    # Serialize input
    pickled_input = pickle.dumps(input_data)

    project_root = Path(__file__).parent.parent.absolute()

    print("Project root:", project_root)

    # Set PYTHONPATH to include project root
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    
    worker_script = project_root / "routing_algorithms/qiskit_ai/run_experiments.py"
    qiskit_ai_python = project_root / ".venv-qiskit-ai" / "bin" / "python"
    
    import tempfile
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as result_file:
        result_path = result_file.name
    
    process = subprocess.Popen(
        [str(qiskit_ai_python), str(worker_script), result_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        env=env,
        cwd=str(project_root),
        bufsize=1,  # Line buffered
        universal_newlines=False
    )
    
    # Send input
    process.stdin.write(pickled_input)
    process.stdin.close()
    
    # Read and print output in real-time
    print("=" * 60)
    print(f"Worker output for {function_name}:")
    print("=" * 60)
    
    for line in iter(process.stdout.readline, b''):
        print(line.decode('utf-8', errors='replace'), end='')
    
    process.wait()
    
    print("=" * 60)
    
    if process.returncode != 0:
        try:
            os.unlink(result_path)
        except:
            pass
        raise RuntimeError(f"Worker process failed with return code {process.returncode}")
    
    # Read result from file
    try:
        with open(result_path, 'rb') as f:
            result = pickle.load(f)
        os.unlink(result_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read result: {e}")
    
    # Check if result is an error
    if isinstance(result, dict) and 'error' in result:
        raise RuntimeError(f"Worker error: {result['error']}\n{result['traceback']}")
    
    return result


def run_qiskit_ai_hamiltonian(
    quantum_computer_backend: CustomBackend,
    num_qubits: int,
    pauli_strings: List[str],
    algorithm_name: str
) -> CircuitOptimisationResult:
    backend_config = serialize_backend(quantum_computer_backend)

    return call_qiskit_ai_function(
        'run_qiskit_ai_hamiltonian',
        backend_config,
        num_qubits,
        pauli_strings,
        algorithm_name
    )

def run_qiskit_ai_circuit(
    circuit: QuantumCircuit,
    backend: CustomBackend,
    algorithm_name: str
) -> CircuitOptimisationResult:
    backend_config = serialize_backend(backend)
    return call_qiskit_ai_function(
        'run_qiskit_ai_circuit',
        circuit,
        backend_config,
        algorithm_name
    )
