from typing import List
from doustra.circuit_topology import CircuitTopology
from doustra.router import Router
from doustra.scheduler import get_scheduler, get_scheduler_type_str
import logging

class Duostra:
    def __init__(self, cir: "QCir", dev: Device, config: "DuostraConfig", exe_opts: "DuostraExecutionOptions"):
        self._device = dev
        self._config = config
        self._check = exe_opts.verify_result
        self._tqdm = not exe_opts.silent and exe_opts.use_tqdm
        self._silent = exe_opts.silent
        self._logical_circuit = cir.copy()  # assuming QCir has a copy method
        self._physical_circuit = QCir()
        self._result: List[QCirGate] = []

    def map(self, use_device_as_placement: bool = False) -> bool:
        topo = CircuitTopology(self._logical_circuit)
        check_topo = topo.clone()
        check_device = self._device.copy()  # assumes Device has copy

        logging.info("Creating device...")
        if topo.get_num_qubits() > self._device.get_num_qubits():
            logging.error("Number of logical qubits are larger than the device!!")
            return False

        assign: List[int] = []
        if not use_device_as_placement:
            logging.info("Calculating Initial Placement...")
            placer = get_placer(self._config.placer_type)
            assign = placer.place_and_assign(self._device)

        logging.info("Creating Scheduler...")
        scheduler = get_scheduler(self._config, topo, self._tqdm)

        logging.info("Creating Router...")
        cost_strategy = (
            "end" if self._config.scheduler_type == "greedy" else "start"
        )
        router = Router(
            self._device,
            self._config.router_type,
            cost_strategy,
            self._config.tie_breaking_strategy,
        )

        if not self._silent:
            print("Routing...")
        self._device = scheduler.assign_gates_and_sort(router)
        if stop_requested():
            logging.warning("Warning: mapping interrupted")
            return False

        assert scheduler.is_sorted()

        for gate, _ in scheduler.get_operations():
            self._result.append(gate)

        self.build_circuit_by_result()

    
        # if self._check:
        #     if not self._silent:
        #         print("Checking...\n")
        #     checker = MappingEquivalenceChecker(
        #         self._physical_circuit,
        #         self._logical_circuit,
        #         check_device,
        #         self._config.placer_type,
        #     )
        #     if not checker.check():
        #         return False

        if not self._silent:
            print("Duostra Result:\n")
            print(f"Scheduler:      {get_scheduler_type_str(self._config.scheduler_type)}")
            print(f"Router:         {get_router_type_str(self._config.router_type)}")
            print(f"Placer:         {get_placer_type_str(self._config.placer_type)}\n")
            print(f"Mapping Depth:  {scheduler.get_final_cost()}")
            print(f"Total Time:     {scheduler.get_total_time()}")
            print(f"#SWAP:          {scheduler.get_num_swaps()}\n")

        return True

    def build_circuit_by_result(self):
        self._physical_circuit.add_qubits(self._device.get_num_qubits())
        for operation in self._result:
            qubits = operation.get_qubits()
            qu = [qubits[0]]
            if qubits[1] != max_qubit_id:
                qu.append(qubits[1])

            if isinstance(operation.get_operation(), SwapGate):
                # Decompose SWAP into three CX gates
                qu_reverse = [qubits[1], qubits[0]]
                self._physical_circuit.append(CXGate(), qu)
                self._physical_circuit.append(CXGate(), qu_reverse)
                self._physical_circuit.append(CXGate(), qu)
            else:
                self._physical_circuit.append(operation.get_operation(), qu)
