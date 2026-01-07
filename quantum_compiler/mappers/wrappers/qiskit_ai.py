import os
import pickle
from quantum_compiler.mappers.base_mapper import QubitMapper
from qiskit.transpiler import PassManager
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit import QuantumCircuit
from time import time
from qiskit.providers import BackendV2
from typing import Optional, List
import subprocess
from pathlib import Path

from quantum_compiler.backends.custom_qiskit import ResearchBackend
from quantum_compiler.core.types import CircuitOptimisationResult, PauliString
from quantum_compiler.utils.paths import get_project_root
from stats_utils.estimated_value import calculate_estimated_average_value_and_dispersion


ISKIT_AI_PYTHON = ".venv-qiskit-ai/bin/python"


def serialize_backend(backend: ResearchBackend) -> dict:
    """Convert CustomBackend to a serializable dictionary"""
    # Extract the graph from the target's CZ gate properties
    graph_list = []

    # Get CZ gate to extract the coupling map
    cz_gate_name = "cz"
    if cz_gate_name in backend.target:
        cz_qargs = backend.target[cz_gate_name].keys()
        for qarg in cz_qargs:
            if len(qarg) == 2:  # It's a 2-qubit gate
                graph_list.append([qarg[0], qarg[1]])

    # If no CZ gates, try CX gates
    if not graph_list:
        cx_gate_name = "cx"
        if cx_gate_name in backend.target:
            cx_qargs = backend.target[cx_gate_name].keys()
            for qarg in cx_qargs:
                if len(qarg) == 2:
                    graph_list.append([qarg[0], qarg[1]])

    return {
        "name": backend.name.replace(" backend", ""),  # Remove ' backend' suffix
        "graph_list": graph_list,
        "num_qubits": backend.num_qubits,
    }


def call_qiskit_ai_function(function_name: str, *args, **kwargs):
    """Call a function in the separate qiskit environment"""
    input_data = {"function": function_name, "args": args, "kwargs": kwargs}

    pickled_input = pickle.dumps(input_data)
    project_root = get_project_root()

    print("Project root:", project_root)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    worker_script = (
        project_root / "external_quantum_compilers" / "qiskit_ai" / "run_experiments.py"
    )
    qiskit_ai_python = project_root / ".venv-qiskit-ai" / "bin" / "python"

    import tempfile

    with tempfile.NamedTemporaryFile(mode="wb", delete=False) as result_file:
        result_path = result_file.name

    process = subprocess.Popen(
        [str(qiskit_ai_python), str(worker_script), result_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        env=env,
        cwd=str(project_root),
        bufsize=1,  # Line buffered
        universal_newlines=False,
    )

    process.stdin.write(pickled_input)
    process.stdin.close()

    print(f"Worker output for {function_name}:")

    for line in iter(process.stdout.readline, b""):
        print(line.decode("utf-8", errors="replace"), end="")

    process.wait()

    print("=" * 60)

    if process.returncode != 0:
        try:
            os.unlink(result_path)
        except:
            pass
        raise RuntimeError(
            f"Worker process failed with return code {process.returncode}"
        )

    # Read result from file
    try:
        with open(result_path, "rb") as f:
            result = pickle.load(f)
        os.unlink(result_path)
    except Exception as e:
        raise RuntimeError(f"Failed to read result: {e}")

    # Check if result is an error
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"Worker error: {result['error']}\n{result['traceback']}")

    return result


class QiskitAI(QubitMapper):
    @property
    def name(self) -> str:
        return "qiskit_ai"

    @property
    def supports_circuit_mapping(self) -> bool:
        return True

    @property
    def supports_raw_pauli_string_mapping(self) -> bool:
        return False

    def map_circuit(
        self,
        circuit: QuantumCircuit,
        backend: BackendV2,
        circuit_name: Optional[str] = None,
    ) -> CircuitOptimisationResult:
        backend_config = serialize_backend(backend)
        return call_qiskit_ai_function(
            "run_qiskit_ai_circuit", circuit, backend_config, circuit_name
        )

    def map_pauli_strings(
        self, pauli_strings: List[PauliString], backend
    ) -> CircuitOptimisationResult:
        pass
