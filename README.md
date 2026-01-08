# QuMeld

QuMeld is a qubit mapping and circuit optimization framework focused on optimizing quantum circuits for various quantum hardware backends. It provides a modular infrastructure to easily integrate different qubit mapping algorithms and topologies, allowing users to experiment with and evaluate the performance of various approaches in the context of optimization problems like QAOA and VQE.

## Main features

- Main focus on the optimising circuits and solving qubit mapping for the optimization problems (QAOA, VQE, etc.)
- Circuit optimization and qubit mapping for various quantum hardware backends (Rigetti, IBM, etc.)
- Ability to integrate custom qubit mappers and topologies into the framwork infrastructure easily
- Prepared experiments and tests for validating the performance of different qubit mappers and topologies

## Currently supported qubit mapping algorithms

- lightSABRE (from Qiskit)
- SABRE (from Qiskit)
- QiskitAI
- Doustra
- Rustiq (from Qiskit)
- PauliForest (for synthesizing Pauli strings)

## Prepared backends

- All newest IBM Quantum backends topologies (like Heron r1, r2)
- Google Willow (105 qubits)
- Riken Fujitsu (256 qubits)
- IonQ Harmony (9 qubits)
- Rigetti Novera (9 qubits)
- Older IBM Quantum backends (like Eagle, Cambridge, Almaden, Tokyo and others) 

## Requirements
- Python 3.8+
- Qiskit
- C++

1. Clone the repository:
   ```bash
   git clone https://github.com/gabkeib/qumeld.git
   ```

2. Download uv if you don't have it already:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source $HOME/.local/bin/env
    ```

3. Create a virtual environment and install dependencies:
    ```bash
    uv sync
    ```

## Usage example

### CLI

You can use the command-line interface (CLI) to optimize quantum circuits for specific backends. Here is a basic example of how to use it:

```bash
uv run python3 cli.py optimize -c ./examples/circuits/basic_5_qubit.qasm -t rigetti_novera_q9 -o auto
```

To have a verbose output, add the `-v` flag:

```bash
uv run python3 cli.py optimize -c ./examples/circuits/basic_5_qubit.qasm -t rigetti_novera_q9 -o auto -v
```

If algorithm is added to the AlgorithmProvider, you can run experiments with it:

```bash
uv run python3 cli.py experiment -a h2 -t rigetti_novera_q9 -o pauliforest
```

To run experiments with all available algorithms on all available topologies and qubit mappers, use:

```bash
uv run python3 cli.py experiment
```

### Python Script

Basic example of using it in a Python script:
```python3
from qiskit import QuantumCircuit
from qiskit_ibm_runtime import SamplerV2 as Sampler
from quantum_compiler.backends.factory import BackendFactory
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.mappers.base_mapper import QubitMapper
from qiskit_ibm_runtime.fake_provider import FakeNairobiV2
from qiskit_aer import AerSimulator

def run_real_backend_example():
    qc = QuantumCircuit(5)
    for i in range(5):
        qc.h(i)
    
    for i in range(4):
        qc.cx(i, i + 1)

    backend_factory = BackendFactory()
    backend = backend_factory.get_backend("rigetti_novera_q9")

    # For IBM supported devices:
    # backend = FakeNairobiV2()

    mapper_registry = MapperRegistry()
    mapper: QubitMapper = mapper_registry.get_mapper("doustra")

    mapped_circuit = mapper.map_circuit(qc, backend, circuit_name="Basic 5-Qubit Circuit")
    

if __name__ == "__main__":
    run_real_backend_example()
```

For more examples, see the [examples/](examples/) directory:
- `examples/run_basic_qml.py`: Basic example of running a quantum machine learning algorithm.
- `examples/run_ibm_fake_backend.py`: Example of using IBM fake backends for optimising and simulating the circuits.
- `examples/run_mapper_selector.py`: Example of using the mapper selector to choose the best qubit mapper for a given circuit and backend.
- `examples/run_vqe_h2.py`: Example of running VQE for the H2 molecule.
- `examples/run_with_error_mitigation.py`: Example of running circuit optimisation with error mitigation techniques.


## Preparations for Qiskit AI Local Transpiler

Due to an upstream dependency conflict (`networkx==2.8.5`),
the Qiskit AI local transpiler must be installed in a separate
Python environment.

### Setup

```bash
uv venv .venv-qiskit-ai --python 3.13
uv pip install qiskit-ibm-ai-local-transpiler qiskit_aer sympy qiskit_ibm_transpiler -p .venv-qiskit-ai
```

## Used algorithms citations



## Attribution

This framework is a part of the research work for the Master's thesis:
"Research of Quantum Computer Topologies for Optimization Algorithms"
