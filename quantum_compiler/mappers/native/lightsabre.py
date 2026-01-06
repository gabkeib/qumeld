from quantum_compiler.mappers.base_mapper import QubitMapper
from qiskit.transpiler import PassManager
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit import QuantumCircuit
from time import time
from qiskit.providers import BackendV2
from typing import Optional, List

from quantum_compiler.core.types import CircuitOptimisationResult
from stats_utils.estimated_value import calculate_estimated_average_value_and_dispersion


class LightSABRE(QubitMapper):
    @property
    def name(self) -> str:
        return "lightSABRE"

    @property
    def supports_circuit_mapping(self) -> bool:
        return True

    @property
    def supports_raw_pauli_string_mapping(self) -> bool:
        return False

    def map_circuit(
        self,
        circuit: QuantumCircuit,
        backend: BackendV2,
        circuit_name: Optional[str] = None,
    ) -> CircuitOptimisationResult:
        time_start = time()

        pm: PassManager = generate_preset_pass_manager(
            optimization_level=3, backend=backend
        )
        compiled_circuit = pm.run(circuit)

        calculated_statistics = calculate_estimated_average_value_and_dispersion(
            circuit, compiled_circuit, None
        )
        return CircuitOptimisationResult(
            optimised_circuit=compiled_circuit,
            name=circuit_name,
            swap_count=compiled_circuit.count_ops().get("swap", 0),
            cx_count=compiled_circuit.count_ops().get("cx", 0)
            + compiled_circuit.count_ops().get("swap", 0) * 3,
            depth=compiled_circuit.depth(),
            expected_value=calculated_statistics.expected_value_after,
            variance=calculated_statistics.variance_after,
            fidelity=calculated_statistics.fidelity,
            optimisation_time=time() - time_start,
            mapper=self.name,
        )

    def map_pauli_strings(
        self, pauli_strings: List[str], backend
    ) -> CircuitOptimisationResult:
        pass
