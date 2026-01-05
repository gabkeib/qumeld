from qiskit import QuantumCircuit

from qiskit.quantum_info import SparsePauliOp
from quantum_compiler.backends.factory import BackendFactory
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.error_mitigation.error_mitigation_registry import ErrorMitigationRegistry
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import EstimatorV2 as Estimator

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

def run_with_error_mitigation():
    circuit = create_basic_circuit()
    circuit_with_measurements = add_measurements(circuit)
    
    backend_factory = BackendFactory()
    backend = backend_factory.get_backend("rigetti_novera_q9")

    mapper_registry = MapperRegistry()
    qubit_mapper = mapper_registry.get_mapper("lightSABRE")

    mapped_circuit = qubit_mapper.map_circuit(
        circuit_with_measurements, 
        backend, 
        circuit_name="Basic 5-Qubit Circuit with Error Mitigation",
    )

    error_mitigation_registry = ErrorMitigationRegistry()     
    error_mitigation_techniques = ["DynamicalDecoupling", "Trex"]

    aer = AerSimulator.from_backend(backend)
    estimator = Estimator(mode=aer)

    optimised_circuit = mapped_circuit.optimised_circuit
    for technique in error_mitigation_techniques:
        em_technique = error_mitigation_registry.get_technique(technique)
        estimator = em_technique.apply_on_estimator(estimator)

    observable = SparsePauliOp("Z" * optimised_circuit.num_qubits)
    
    job = estimator.run([(optimised_circuit, observable)])
    result = job.result()
    print("Result with error mitigation:", result)
    
if __name__ == "__main__":
    run_with_error_mitigation()
