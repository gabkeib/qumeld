import io
from requests import get
from quantum_compiler.mappers.base_mapper import QubitMapper
from qiskit.transpiler import PassManager
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit import QuantumCircuit, transpile
from time import time
from qiskit.providers import BackendV2
from typing import Optional, List, Tuple
from qiskit import QuantumCircuit, qasm2
import subprocess
import os
from pathlib import Path
import re
import numpy as np

from quantum_compiler.core.types import CircuitOptimisationResult
from quantum_compiler.utils.paths import get_project_root
from stats_utils.estimated_value import calculate_estimated_average_value_and_dispersion


class Doustra(QubitMapper):

    @property
    def name(self) -> str:
        return "doustra"
    
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
        circuit_name: Optional[str] = None
    ) -> CircuitOptimisationResult:
        time_start = time()

        optimised_qc, swap_value = self.doustra_optimise_circuit(circuit, backend, circuit_name)

        calculated_statistics = calculate_estimated_average_value_and_dispersion(circuit, optimised_qc, None)
        return CircuitOptimisationResult(
            optimised_circuit=optimised_qc,
            name=circuit_name,
            swap_count=swap_value,
            cx_count=optimised_qc.count_ops().get('cx', 0),
            depth=optimised_qc.depth(),
            expected_value=calculated_statistics.expected_value_after,
            variance=calculated_statistics.variance_after,
            fidelity=calculated_statistics.fidelity,
            optimisation_time=time() - time_start,
            mapper=self.name
        )

    def map_pauli_strings(self, pauli_strings: List[str], backend) -> CircuitOptimisationResult:
        pass 
        
    def transpile_circuit(self, circuit: QuantumCircuit, backend: BackendV2) -> QuantumCircuit:
        basis = [
            "cx",
            "sx",
            "sxdg",
            "h",
            "rz",
            "x",
            "y",
            "z"
        ]
        transpiled_circuit = transpile(
            circuit,
            basis_gates=basis,
            coupling_map=backend.coupling_map,
            optimization_level=0
        )
        return transpiled_circuit

    def doustra_optimise_circuit(self, circuit: QuantumCircuit, backend: BackendV2, quantum_algorithm: str) -> Tuple[QuantumCircuit, int]:
        time_start = time()

        project_root = get_project_root()

        backend_name_normalized = backend.name.replace(" ", "_").lower()
        quantum_algorithm_normalized = backend.name.replace(" ", "_").lower()

        script_path = project_root / "configs" / "doustra" / "scripts" / "optimise_circuit.qsyn"
        in_path = project_root / "dumps" / f"{quantum_algorithm_normalized}.qasm"
        out_path = project_root / "dumps" / f"{quantum_algorithm_normalized}_output.qasm"
        layout_path = project_root / "configs" / "doustra" / "layouts" / f"{backend_name_normalized}.layout"

        if circuit.parameters:
            print(f"Circuit has {len(circuit.parameters)} unbound parameters. Binding with random values...")
            # Bind parameters with random values (or zeros)
            parameter_values = {param: np.random.uniform(0, 2*np.pi) for param in circuit.parameters}
            # Or
            # parameter_values = {param: 0.0 for param in circuit.parameters}
            
            bound_circuit = circuit.assign_parameters(parameter_values)
            qasm2.dump(self.transpile_circuit(bound_circuit, backend), open(in_path, "w"))
        else:
            qasm2.dump(self.transpile_circuit(circuit, backend), open(in_path, "w"))

        if not Path(layout_path).exists():
            edge_list_ll = [list(edge) for edge in backend.coupling_map.get_edges()]
            self.convert_to_layout(backend_name_normalized, edge_list_ll, backend.num_qubits)

        # Get the path to the qsyn binary in the external_quantum_compilers directory
        qsyn_path = str(project_root / "external_quantum_compilers" / "qsyn" / "qsyn")
        
        # Run qsyn with subprocess
        command = [
            qsyn_path,
            script_path,
            in_path,
            layout_path,
            out_path
        ]
        
        swap_value = 0
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
                cwd=os.getcwd()
            )
            print(f"qsyn stdout: {result.stdout}")
            swap_match = re.search(r'#SWAP:\s*(\d+)', result.stdout)
            if swap_match:
                swap_value = int(swap_match.group(1))
            if result.stderr:
                print(f"qsyn stderr: {result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"qsyn failed with return code {e.returncode}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            raise

        optimised_qc = QuantumCircuit.from_qasm_str(open(out_path, "r").read())
        return optimised_qc, swap_value
    
    def convert_to_layout(self, name, quantum_computer: List[List[int]], num_qubits: int) -> List[int]:
        project_root = get_project_root()
        layout_path = project_root / "configs" / "doustra" / "layouts" / f"{name}.layout"
        
        coupling_map = [[] for _ in range(num_qubits)]
        for i, edge in enumerate(quantum_computer):
            coupling_map[edge[0]].append(edge[1])
            coupling_map[edge[1]].append(edge[0])
        with open(layout_path, "w") as f:
            f.write(f"NAME: {name}\n")
            f.write(f"QUBITNUM: {num_qubits}\n")
            f.write("GATESET: {x, rz, h, id, sx, cnot, swap}\n")
            f.write(f"COUPLINGMAP: {coupling_map}\n")
            f.write(f"SGERROR: {[0 for _ in range(num_qubits)]}\n")
            f.write(f"SGTIME: {[0 for _ in range(num_qubits)]}\n")
            f.write(f"CNOTERROR: {coupling_map}\n")
            f.write(f"CNOTTIME: {coupling_map}")

        return coupling_map
