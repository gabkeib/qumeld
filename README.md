# Research of Quantum Computer Topologies for Optimization Algorithms

This repository contains code and experiments related to the research of quantum computer topologies for optimization algorithms

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
   git clone https://github.com/gabkeib/RQCTOA
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


## Qiskit AI Local Transpiler (Optional)

Due to an upstream dependency conflict (`networkx==2.8.5`),
the Qiskit AI local transpiler must be installed in a separate
Python environment.

### Setup

```bash
uv venv .venv-qiskit-ai --python 3.13
uv pip install qiskit-ibm-ai-local-transpiler qiskit_aer sympy qiskit_ibm_transpiler -p .venv-qiskit-ai
```
