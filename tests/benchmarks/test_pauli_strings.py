def get_test_pauli_strings() -> list[list[str]]:
    pauli_strings_set = []

    # 1. Simple Z strings
    pauli_strings_set.append(["ZZII", "IIZZ", "ZIZI", "IZIZ"])

    # 2. Mixed Pauli strings
    pauli_strings_set.append(["XZIY", "YIXZ", "ZZXX", "IYZI"])

    # 3. Identity and single qubit operators
    pauli_strings_set.append(["IIII", "XIII", "IYII", "IIIZ"])

    # 4. Longer strings for 5 qubits
    pauli_strings_set.append(["XYZII", "IYZXI", "ZZZZZ", "XIXIX"])

    return pauli_strings_set
