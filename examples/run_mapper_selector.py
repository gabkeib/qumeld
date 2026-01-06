from qiskit import QuantumCircuit
from quantum_compiler.backends.factory import BackendFactory
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.core.mapper_selector import MapperSelector


def add_measurements(circuit: QuantumCircuit) -> QuantumCircuit:
    qc_meas = circuit.copy()
    qc_meas.measure_all()
    return qc_meas


def create_basic_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(5)
    for i in range(5):
        qc.h(i)

    for i in range(4):
        qc.cx(i, i + 1)
    return qc


def run_mapper_selector():
    circuit = create_basic_circuit()
    circuit = add_measurements(circuit)

    mapper_registry = MapperRegistry()
    mapper_selector = MapperSelector(mapper_registry)

    backend_factory = BackendFactory()
    backend = backend_factory.get_backend("rigetti_novera_q9")

    circuit, mapper_name, score = mapper_selector.find_optimal_mapping(circuit, backend)

    print(f"Best mapper: {mapper_name} with score: {score}")
    print("Mapped Circuit:")
    print(circuit)


if __name__ == "__main__":
    run_mapper_selector()
