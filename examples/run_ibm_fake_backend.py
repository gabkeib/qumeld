from dotenv import load_dotenv
from qiskit import QuantumCircuit, generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
import os
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.mappers.base_mapper import QubitMapper
from qiskit.primitives import StatevectorEstimator
from qiskit_ibm_runtime.fake_provider import FakeNairobiV2
from qiskit_aer import AerSimulator
from qiskit.transpiler import PassManager

load_dotenv()

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

# Make sure that the credentials for qiskit runtime service are set up
def run_real_backend_example():
    circuit = create_basic_circuit()

    service = QiskitRuntimeService(
        token=os.getenv("QISKIT_API_KEY"),
        plans_preference=["open"]
    )
    # For real device:
    # backend = service.least_busy(simulator=False, operational=True)

    # For fake IBM provided backend:
    backend = FakeNairobiV2()
    aer = AerSimulator.from_backend(backend)

    mapper_registry = MapperRegistry()
    mapper: QubitMapper = mapper_registry.get_mapper("doustra")

    mapped_circuit = mapper.map_circuit(circuit, backend, circuit_name="Basic 5-Qubit Circuit")
    mapped_circuit_with_measurements = add_measurements(mapped_circuit.optimised_circuit)
    
    # Run this to map gates to the ones supported by the IBM QC
    pm: PassManager = generate_preset_pass_manager(backend=aer, optimization_level=1)    
    qc = pm.run(mapped_circuit_with_measurements)

    # Will not fit in RAM on smaller machines
    sampler = Sampler(mode=aer)
    result = sampler.run([qc]).result()
    print(f"Mapped circuit executed on backend: {backend.name}")
    print(f"Result: {result}")

    pub_result = result[0]
    counts = pub_result.data.meas.get_counts()
    print(f"\nMeasurement counts:")
    for bitstring, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {bitstring}: {count}")


if __name__ == "__main__":
    run_real_backend_example()

