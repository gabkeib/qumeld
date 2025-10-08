from typing import List, Optional, Any, Tuple
from abc import ABC, abstractmethod
from qiskit.circuit import Instruction
import random

def get_scheduler(config, topo, tqdm):
    # 0:base 1:naive 2:random 3:greedy 4:search
    if config.scheduler_type == 0:  # base
        return BaseScheduler(topo, tqdm)
    elif config.scheduler_type == 1:  # naive
        return NaiveScheduler(topo, tqdm)
    elif config.scheduler_type == 2:  # random
        return RandomScheduler(topo, tqdm)
    elif config.scheduler_type == 3:  # greedy
        return GreedyScheduler(topo, config, tqdm)
    # elif config.scheduler_type == 4:  # search
    #     return SearchScheduler(topo, config, tqdm)
    else:
        return None

# Stubs for external types (replace with real implementations)
class CircuitTopology:
    def get_available_gates(self) -> List[int]:
        return []


class Router:
    pass


# represents a gate and its metadata (time and time + delay)
GateInfo = Tuple[Instruction, Tuple[int, int]]

class Device:
    pass


class BaseScheduler(ABC):
    def __init__(self, topo: CircuitTopology, tqdm: bool):
        self._circuit_topology = topo
        self._operations: List[GateInfo] = []
        self._sorted: bool = False
        self._tqdm: bool = tqdm

    @abstractmethod
    def clone(self) -> "BaseScheduler":
        pass

    def circuit_topology(self) -> CircuitTopology:
        return self._circuit_topology

    def get_final_cost(self) -> int:
        return self._operations[len(self._operations) - 1][1][1]

    def get_total_time(self) -> int:
        return sum(op[1][1] - op[1][0] for op in self._operations)

    def get_num_swaps(self) -> int:
        return sum(1 for gate, _ in self._operations if gate.name == "swap")

    def get_executable_gate(self, router: Router) -> Optional[int]:
        for gate in self._circuit_topology.get_available_gates():
            if router.is_executable(gate):
                return gate
        return None

    def get_operations_cost(self) -> int:
        return self._operations[len(self._operations) - 1][1][1]

    def is_sorted(self) -> bool:
        return self._sorted

    def get_available_gates(self) -> List[int]:
        return self._circuit_topology.get_available_gates()

    def get_operations(self) -> List[GateInfo]:
        return self._operations

    def assign_gates_and_sort(self, router: Router) -> Device:
        device = self._assign_gates(router)
        self._sort()
        return device

    def route_one_gate(self, router: "Router", gate_id: int, forget: bool = False) -> int:
        gate = self._circuit_topology.get_gate(gate_id)
        ops = router.assign_gate(gate)

        max_cost = max((end for _, (_, end) in ops), default=0)

        if not forget:
            self._operations.extend(ops)

        self._circuit_topology.update_available_gates(gate_id)
        return max_cost

    @abstractmethod
    def _assign_gates(self, router: Router) -> Device:
        pass

    def _sort(self) -> None:
        self._operations.sort(key=lambda x: x[1][0])
        self._sorted = True


class RandomScheduler(BaseScheduler):
    def __init__(self, topo: CircuitTopology, tqdm: bool):
        super().__init__(topo, tqdm)

    def clone(self) -> "RandomScheduler":
        return RandomScheduler(self._circuit_topology, self._tqdm)

    def _assign_gates(self, router: Router) -> Device:
        count = 0
        num_gates = self._circuit_topology.get_num_gates()

        for _ in range(num_gates):
            if self.stop_requested():
                return router.get_device()

            waitlist = self._circuit_topology.get_available_gates()
            assert waitlist, "No available gates to schedule"

            choice = random.randrange(len(waitlist))  # random index
            self.route_one_gate(router, waitlist[choice])

            count += 1

        assert count == num_gates
        return router.get_device()


class NaiveScheduler(BaseScheduler):
    def __init__(self, topo: CircuitTopology, tqdm: bool):
        super().__init__(topo, tqdm)

    def clone(self) -> "NaiveScheduler":
        return NaiveScheduler(self._circuit_topology, self._tqdm)

    def _assign_gates(self, router: "Router") -> "Device":
        count = 0
        num_gates = self._circuit_topology.get_num_gates()

        for _ in range(num_gates):
            if self.stop_requested():
                return router.get_device()

            waitlist = self._circuit_topology.get_available_gates()
            assert waitlist

            gate_idx = self.get_executable_gate(router) or waitlist[0]
            self.route_one_gate(router, gate_idx)
            count += 1

        assert count == self._circuit_topology.get_num_gates()
        return router.get_device()


class TopologyCandidate:
    def __init__(self, topo: CircuitTopology, num_candidates: int):
        self._circuit_topology = topo
        self._num_candidates = num_candidates

    def get_available_gates(self) -> List[int]:
        gates = self._circuit_topology.get_available_gates()
        if len(gates) < self._num_candidates:
            return gates
        return gates[:self._num_candidates]  # equivalent to C++ iterator::next


class GreedyConf:
    def __init__(self, available_time_strategy: Any, cost_type: Any, num_candidates: int, apsp_coeff: int):
        self.available_time_strategy = available_time_strategy
        self.cost_type = cost_type
        self.num_candidates = num_candidates
        self.apsp_coeff = apsp_coeff

    def __init__(self, topo: CircuitTopology, num_candidates: int):
        self._circuit_topology = topo
        self._num_candidates = num_candidates

class MinMaxOptionType:
    max = "max"
    min = "min"

class GreedyScheduler(BaseScheduler):
    def __init__(self, topo: CircuitTopology, config: Any, tqdm: bool):
        super().__init__(topo, tqdm)
        self._conf = GreedyConf(
            config.available_time_strategy,
            config.cost_selection_strategy,
            config.num_candidates,
            config.apsp_coeff,
        )

    def clone(self) -> "GreedyScheduler":
        return GreedyScheduler(self._circuit_topology, self._conf, self._tqdm)

    def _assign_gates(self, router: Router):
        count = 0
        topo_wrap = TopologyCandidate(self._circuit_topology, self._conf.num_candidates)

        while topo_wrap.get_available_gates():
            if stop_requested():
                return router.get_device()

            waitlist = topo_wrap.get_available_gates()
            assert waitlist, "waitlist should not be empty"

            gate_idx: Optional[int] = self.get_executable_gate(router)
            if gate_idx is None:
                gate_idx = self.greedy_fallback(router, waitlist)

            assert gate_idx is not None
            self.route_one_gate(router, gate_idx)

            # logger.debug("waitlist: [%s] %d", ", ".join(map(str, waitlist)), gate_idx)

            count += 1

        assert count == self._circuit_topology.get_num_gates()
        return router.get_device()

    def greedy_fallback(self, router: Router, waitlist: List[int]) -> int:
        cost_list = []
        for gate_id in waitlist:
            gate = self._circuit_topology.get_gate(gate_id)
            cost = router.get_gate_cost(
                gate, self._conf.available_time_strategy, self._conf.apsp_coeff
            )
            cost_list.append(cost)

        if self._conf.cost_type == MinMaxOptionType.max:
            list_idx = cost_list.index(max(cost_list))
        else:
            list_idx = cost_list.index(min(cost_list))

        return waitlist[list_idx]

    # Placeholder for methods defined elsewhere
    def get_executable_gate(self, router: Router) -> Optional[int]:
        return None

    def route_one_gate(self, router: Router, gate_idx: int):
        pass

def stop_requested() -> bool:
    return False