# QuMeld

QuMeld is a qubit mapping and circuit optimization framework focused on optimizing quantum circuits for various quantum hardware backends. It provides a modular infrastructure to easily integrate different qubit mapping algorithms and topologies, allowing users to experiment with and evaluate the performance of various approaches in the context of optimization problems like QAOA and VQE.

## Main features

- Main focus on the optimising circuits and solving qubit mapping for the optimization problems (QAOA, VQE, etc.)
- Circuit optimization and qubit mapping for various quantum hardware backends (Rigetti, IBM, etc.)
- Ability to integrate custom qubit mappers and topologies into the framwork infrastructure easily
- Prepared experiments and tests for validating the performance of different qubit mappers and topologies

## Currently supported qubit mapping algorithms

- Doustra [1]
- PauliForest (for synthesizing Pauli strings) [2]
- lightSABRE (from Qiskit) (lookahead and decay) [3]
- Rustiq (from Qiskit) [4]
- QiskitAI [5][6]

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

4. Build the C++ components (qsyn):
    
    For Linux users:
    ```bash
    # Install required libraries
    sudo apt install libopenblas-dev liblapack-dev
    
    # Navigate to qsyn directory and build
    cd external_quantum_compilers/qsyn
    make -j8
    cd ../..
    ```
    
    For macOS users:
    ```bash
    # Install LLVM and OpenBLAS
    brew install llvm openblas
    
    # Navigate to qsyn directory and build
    cd external_quantum_compilers/qsyn
    make -j8
    cd ../..
    ```
    
    **Note:** When deploying to a remote server (rsync/tar), you must rebuild the C++ components on the target machine. Exclude the binary when transferring:
    ```bash
    # Example rsync excluding the binary
    rsync -avz --exclude='build/' --exclude='__pycache__/' --exclude='external_quantum_compilers/qsyn/qsyn' \
      /path/to/local/project/ user@remote:/path/to/remote/project/
    ```
    
    Then SSH into the remote machine and rebuild:
    ```bash
    ssh user@remote
    cd /path/to/remote/project/external_quantum_compilers/qsyn
    make -j8
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

## References

[1] Cheng et al., "Robust Qubit Mapping Algorithm via Double-Source Optimal Routing on Large Quantum Circuits," *ACM Transactions on Quantum Computing*, vol. 5, no. 3, 2024. DOI: 10.1145/3680291

[2] Li et al., "PauliForest: Connectivity-Aware Synthesis and Pauli-Oriented Qubit Mapping for Near Term Quantum Simulation," *IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems*, 2024. DOI: 10.1109/TCAD.2024.3509794

[3] Zou et al., "LightSABRE: A Lightweight and Enhanced SABRE Algorithm," *arXiv preprint*, 2024. arXiv: 2409.08368

[4] Goubault de Brugière & Martiel, "Faster and Shorter Synthesis of Hamiltonian Simulation Circuits," *arXiv preprint*, 2024. arXiv: 2404.03280

[5] Dubal et al., "Pauli Network Circuit Synthesis with Reinforcement Learning," *arXiv preprint*, 2025. arXiv: 2503.14448

[6] Kremer et al., "Practical and Efficient Quantum Circuit Synthesis and Transpiling with Reinforcement Learning," *arXiv preprint*, 2024. arXiv: 2405.13196


## Attribution

This framework is described in:

Keibas, G., & Petkevičius, L. (2026). "QuMeld: A Modular Framework for Benchmarking Qubit Mapping Algorithms." *arXiv preprint* arXiv:2603.01578. https://arxiv.org/abs/2603.01578

It is a part of the research work for the Master's thesis:
"Research of Quantum Computer Topologies for Optimization Algorithms"
