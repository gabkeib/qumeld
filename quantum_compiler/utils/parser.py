import re
from typing import List


def read_raw_pauli_file(path: str) -> List[str]:
    """Read a file containing raw Pauli strings and return them as a list."""
    with open(path, "r") as f:
        content = f.read()

    pauli_strings = re.findall(r"[IXYZ]+", content)

    return pauli_strings
