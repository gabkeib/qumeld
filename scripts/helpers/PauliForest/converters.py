from quantum_compiler.utils.parser import read_raw_pauli_file
import json

from quantum_compiler.utils.paths import get_project_root

def convert_to_hamiltonian_from_file(path: str, circuit_name: str):
    paulis = read_raw_pauli_file(path)

    pauli_strings = []
    for term in paulis:
        pauli_strings.append({
            "coeff": 0,
            "pauli": term
        })
    whole_hamiltonian = {}
    whole_hamiltonian["name"] = circuit_name
    whole_hamiltonian["pauli_strings"] = pauli_strings

    project_root = get_project_root()
    output_path = project_root / "hamiltonians" / f"{circuit_name}.json"
    with open(output_path, "w") as f:
        json.dump(whole_hamiltonian, f, indent=4)

    print(f"Hamiltonian saved to {output_path}")

