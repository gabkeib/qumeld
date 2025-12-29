import ast
from typing import List
from qiskit.circuit.library import EfficientSU2
from qiskit.quantum_info import SparsePauliOp
from pathlib import Path


# From qiskit VQE tutorial, move to more advanced later
def get_pauli_strings():
    return [
        "IIII",
        "IIIZ",
        "IZII",
        "IIZI",
        "ZIII",
        "IZIZ",
        "IIZZ",
        "ZIIZ",
        "IZZI",
        "ZZII",
        "ZIZI",
    ]


def get_H2_hamiltonian_sparse():
    H = SparsePauliOp(
        [
            "IIII",
            "IIIZ",
            "IZII",
            "IIZI",
            "ZIII",
            "IZIZ",
            "IIZZ",
            "ZIIZ",
            "IZZI",
            "ZZII",
            "ZIZI",
            "YYYY",
            "XXYY",
            "YYXX",
            "XXXX",
        ],
        coeffs=[
            -0.09820182 + 0.0j,
            -0.1740751 + 0.0j,
            -0.1740751 + 0.0j,
            0.2242933 + 0.0j,
            0.2242933 + 0.0j,
            0.16891402 + 0.0j,
            0.1210099 + 0.0j,
            0.16631441 + 0.0j,
            0.16631441 + 0.0j,
            0.1210099 + 0.0j,
            0.17504456 + 0.0j,
            0.04530451 + 0.0j,
            0.04530451 + 0.0j,
            0.04530451 + 0.0j,
            0.04530451 + 0.0j,
        ],
    )
    return H

def read_pauli_strings_from_file(path: str) -> List[str]:
    try:
        with open(path, "r") as f:
            content = f.read().strip()
            pauli_array = ast.literal_eval(content)
            pauli_strings = [pauli[0] for pauli in pauli_array]
            return pauli_strings
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Pauli strings file not found: {path}")
    except Exception as e:
        raise ValueError(f"Error parsing Pauli strings from {path}: {e}")


# Use LiH from PauliHedral benchmarks
def get_LiH_hamiltonian() -> list[str]:
    path = f"{Path.cwd()}/external_quantum_compilers/PauliGo/benchmark/text/LiH.txt"
    return read_pauli_strings_from_file(path)

def get_demo_pauli_strings() -> list[str]:
    return [
        "YZZZZYYIY",
        "XYIXXIZYZ",
        "XXIIXXYXI",
        "ZIIIXYYYY",
        "XZYYXZXYI",
    ]

def get_H2_hamiltonian() -> list[str]:
    return [
            "IIII",
            "IIIZ",
            "IZII",
            "IIZI",
            "ZIII",
            "IZIZ",
            "IIZZ",
            "ZIIZ",
            "IZZI",
            "ZZII",
            "ZIZI",
            "YYYY",
            "XXYY",
            "YYXX",
            "XXXX",
        ]

def get_qaoa_max_cut_hamiltonian(graph: list[list[int]]) -> list[str]:
    pauli_strings = []
    for i in range(len(graph)):
        for j in range(i + 1, len(graph)):
            if graph[i][j] == 1:
                pauli_list = ['I'] * len(graph)
                pauli_list[i] = 'Z'
                pauli_list[j] = 'Z'
                pauli_string = ''.join(pauli_list)
                pauli_strings.append(pauli_string)
    return pauli_strings

hamiltonian_functions = {
    "H2": get_H2_hamiltonian,
    "LiH": get_LiH_hamiltonian,
    "demo": get_demo_pauli_strings
}

def get_hamiltonian_by_name(name: str) -> List[str]:
    if name in hamiltonian_functions:
        return hamiltonian_functions[name]()
    else:
        raise ValueError(f"Hamiltonian not found: {name}")
