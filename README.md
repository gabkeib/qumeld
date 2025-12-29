# Research of Quantum Computer Topologies for Optimization Algorithms

This repository contains code and experiments related to the research of quantum computer topologies for optimization algorithms

## Structure
- `experiments/`: Contains scripts to run experiments using different quantum computing frameworks and topologies.
- `quantum_algorithms/`: Contains implementations of quantum algorithms such as VQE.
- `topologies/`: Contains definitions and utilities for various quantum computer topologies.

## Requirements
- Python 3.8+
- Qiskit
- C++

## TODO
 - Allow to have random algorithm and topology
 - Add error correction algorithms and check results on different topologies

## Qiskit AI Local Transpiler (Optional)

Due to an upstream dependency conflict (`networkx==2.8.5`),
the Qiskit AI local transpiler must be installed in a separate
Python environment.

### Setup

```bash
uv venv .venv-qiskit-ai --python 3.13
uv pip install qiskit-ibm-ai-local-transpiler qiskit_aer sympy -p .venv-qiskit-ai
```
