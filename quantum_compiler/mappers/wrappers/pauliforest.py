from quantum_compiler.mappers.base_mapper import QubitMapper
from qiskit.transpiler import PassManager
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit import QuantumCircuit
from time import time
from qiskit.providers import BackendV2
from typing import Optional, List
from external_quantum_compilers.PauliGo.compiler import Compiler
from external_quantum_compilers.PauliGo.benchmark.mypauli import pauliString

from quantum_compiler.core.types import CircuitOptimisationResult
from stats_utils.estimated_value import calculate_estimated_average_value_and_dispersion


class PauliForest(QubitMapper):
    @property
    def name(self) -> str:
        return "pauliforest"

    @property
    def supports_circuit_mapping(self) -> bool:
        return False

    @property
    def supports_raw_pauli_string_mapping(self) -> bool:
        return True

    def map_circuit(
        self,
        circuit: QuantumCircuit,
        backend: BackendV2,
        circuit_name: Optional[str] = None,
    ) -> CircuitOptimisationResult:
        pass

    def map_pauli_strings(
        self,
        pauli_strings: List[str],
        backend: BackendV2,
        circuit_name: Optional[str] = None,
    ) -> CircuitOptimisationResult:
        time_start = time()
        op_list = [self.convert_string_to_pauli_string(ps) for ps in pauli_strings]
        blocks = self.program_prep(op_list)
        compiler = Compiler(blocks, backend.name)
        qc = compiler.start("ucc")
        calculated_statistics = calculate_estimated_average_value_and_dispersion(
            qc, qc, None
        )
        return CircuitOptimisationResult(
            name=circuit_name,
            swap_count=qc.count_ops().get("swap", 0),
            cx_count=qc.count_ops().get("cx", 0) + qc.count_ops().get("swap", 0) * 3,
            depth=qc.depth(),
            expected_value=calculated_statistics.expected_value_after,
            variance=calculated_statistics.variance_after,
            fidelity=calculated_statistics.fidelity,
            optimisation_time=time() - time_start,
            optimised_circuit=qc,
            mapper=self.name,
        )

    def program_prep(self, origin_blocks):
        bn = pn = 0
        blocks = []
        for bk in origin_blocks:
            blocks.append([pauliString(ps[0], ps[1]) for ps in bk])
        bn = len(origin_blocks)
        return blocks

    def convert_string_to_pauli_string(self, pauli_string):
        return [[pauli_string, 1.0]]  # current rotation is 0
