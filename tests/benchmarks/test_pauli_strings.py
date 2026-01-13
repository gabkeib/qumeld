from quantum_compiler.core.types import PauliString


def get_test_pauli_strings() -> list[list[PauliString]]:
    pauli_strings_set = []

    # 1. Simple Z strings
    pauli_strings_set.append([PauliString("ZZII", 1.0), PauliString("IIZZ", 1.0), PauliString("ZIZI", 1.0), PauliString("IZIZ", 1.0)])

    # 2. Mixed Pauli strings
    pauli_strings_set.append([PauliString("XZIY", 1.0), PauliString("YIXZ", 1.0), PauliString("ZZXX", 1.0), PauliString("IYZI", 1.0)])

    # 3. Identity and single qubit operators
    pauli_strings_set.append([PauliString("IIII", 1.0), PauliString("XIII", 1.0), PauliString("IYII", 1.0), PauliString("IIIZ", 1.0)])

    # 4. Longer strings for 5 qubits
    pauli_strings_set.append([PauliString("XYZII", 1.0), PauliString("IYZXI", 1.0), PauliString("ZZZZZ", 1.0), PauliString("XIXIX", 1.0)])

    return pauli_strings_set
