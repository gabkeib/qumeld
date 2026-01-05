from qiskit import transpiler

def convert_array_to_coupling_map(arr):
    coupling_map = transpiler.CouplingMap(arr)
    return coupling_map
