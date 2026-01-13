from qiskit import QuantumCircuit
from quantum_algorithms.registry import AlgorithmRegistry
from quantum_compiler.circuits.utils import extract_circuit_features
import json
from typing import Any

def extract_features(circuits: list[QuantumCircuit], save_path: str = None) -> dict:
    circuit_features = {}

    for idx, circuit in enumerate(circuits):
        circuit_name = circuit.name if circuit.name else f"circuit_{idx}"
        features = extract_circuit_features(circuit)
        circuit_features[circuit_name] = features

    return circuit_features

def extract_circuits_features():
    algorithm_registry = AlgorithmRegistry()
    
    circuits_to_analyse = []
    for alg_name in algorithm_registry.list_algorithms():
        algorithm_params: dict[str, Any] = {"name": alg_name}
        if alg_name == "qaoa" or alg_name == "qaoa_ansatz":
            algorithm_params["graph"] = [
                [0, 1, 1, 0, 1],
                [1, 0, 1, 0, 0],
                [1, 1, 0, 1, 0],
                [0, 0, 1, 0, 1],
                [1, 0, 0, 1, 0],
            ]
            algorithm_params["num_qubits"] = 5
        if alg_name == "efficient_su2":
            algorithm_params["num_qubits"] = 5
        circuit = algorithm_registry.get_circuit(**algorithm_params)

        if alg_name == "qaoa" or alg_name == "qaoa_ansatz" or alg_name == "efficient_su2":
            print(circuit)

        circuits_to_analyse.append(circuit)

    features = extract_features(
        circuits=circuits_to_analyse,
    )
    return features

if __name__ == "__main__":
    features = extract_circuits_features()

    with open("circuit_features.json", "w") as f:
        json.dump(features, f, indent=4)

