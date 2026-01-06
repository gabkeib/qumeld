from typing import List
from qiskit.providers import BackendV2, Options, QubitProperties
import numpy as np
from qiskit.transpiler import Target, InstructionProperties
from qiskit.circuit.library import XGate, SXGate, RZGate, CZGate, CXGate, SwapGate
from qiskit.circuit import Measure, Delay, Parameter, Reset
from quantum_compiler.backends.utils import convert_array_to_coupling_map


class ResearchBackend(BackendV2):
    def __init__(self, name: str, graph_list: List[List[int]], num_qubits: int):
        super().__init__(name=f"{name}")
        graph = convert_array_to_coupling_map(graph_list)
        edge_properties = {(edge[0], edge[1]): None for edge in graph}
        num_qubits = num_qubits
        rng = np.random.default_rng(seed=12345678942)
        rz_props = {}
        x_props = {}
        sx_props = {}
        measure_props = {}
        delay_props = {}
        qubit_properties = [
            QubitProperties(
                t1=rng.uniform(50e-6, 100e-6),  # T1 time in seconds
                t2=rng.uniform(20e-6, 80e-6),  # T2 time in seconds
                frequency=rng.uniform(4.5e9, 5.5e9),  # Qubit frequency in Hz
            )
            for _ in range(num_qubits)
        ]

        self._target = Target(
            "Target", num_qubits=num_qubits, qubit_properties=qubit_properties
        )

        for i in range(num_qubits):
            qarg = (i,)
            rz_props[qarg] = InstructionProperties(error=0.0, duration=0.0)
            x_props[qarg] = InstructionProperties(
                error=rng.uniform(1e-6, 1e-4),
                duration=rng.uniform(1e-8, 9e-7),
            )
            sx_props[qarg] = InstructionProperties(
                error=rng.uniform(1e-6, 1e-4),
                duration=rng.uniform(1e-8, 9e-7),
            )
            measure_props[qarg] = InstructionProperties(
                error=rng.uniform(1e-3, 1e-1),
                duration=rng.uniform(1e-8, 9e-7),
            )
            delay_props[qarg] = None
        self._target.add_instruction(XGate(), x_props)
        self._target.add_instruction(SXGate(), sx_props)
        self._target.add_instruction(RZGate(Parameter("theta")), rz_props)
        self._target.add_instruction(Measure(), measure_props)
        self._target.add_instruction(Reset(), measure_props)
        self._target.add_instruction(Delay(Parameter("t")), delay_props)
        self._target.add_instruction(
            SwapGate(), edge_properties
        )  # add swap with no properties
        self._target.add_instruction(CXGate(), edge_properties)
        cz_props = {}
        for edge in graph_list:
            cz_props[(edge[0], edge[1])] = InstructionProperties(
                error=rng.uniform(7e-4, 5e-3),
                duration=rng.uniform(1e-8, 9e-7),
            )
        self._target.add_instruction(CZGate(), cz_props)

    @property
    def target(self):
        return self._target

    @property
    def max_circuits(self):
        return None

    @classmethod
    def _default_options(cls):
        return Options(shots=1024)

    def run(self, circuit, **kwargs):
        raise NotImplementedError("not implemented")
