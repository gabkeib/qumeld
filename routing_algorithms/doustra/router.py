from typing import List, Tuple, Any
from queue import PriorityQueue
from networkx import shortest_path
from doustra.router import MinMaxOptionType, Device
from qiskit.circuit import Instruction
import sys

# Placeholder types for external dependencies

class PhysicalQubit:
    pass

class QCirGate:
    pass

GateInfo = Tuple[Instruction, Tuple[int, int]]  # same as your earlier definition
QubitIdType = int

max_qubit_id = sys.maxsize

# Placeholder enums
class RouterType:
    shortest_path = 0
    doustra = 1

class MinMaxOptionType:
    min = "min"
    max = "max"

class CostStrategyType:
    start = 0
    end = 1

class Router:
    def __init__(
        self,
        device: Device,
        router_type: RouterType,
        cost_strategy: CostStrategyType,
        tie_breaking_strategy: MinMaxOptionType,
    ):
        self._tie_breaking_strategy = tie_breaking_strategy
        self._device = device
        self._logical_to_physical: List[QubitIdType] = []
        self._apsp: bool = router_type == RouterType.shortest_path or cost_strategy == CostStrategyType.end
        self._duostra: bool = router_type == RouterType.doustra

        self._initialize()

    def clone(self) -> "Router":
        # In C++, this is a deep copy using unique_ptr
        # Python shallow copy, adjust if deep copy is needed
        import copy
        return copy.deepcopy(self)

    @property
    def device(self) -> Device:
        return self._device

    # Gate cost and executability
    def get_gate_cost(self, gate: Instruction, min_max: MinMaxOptionType, apsp_coeff: int) -> int:
        q0_id, q1_id = self._get_physical_qubits(gate)

        if gate.get_num_qubits() == 1:
            # In C++: assert(q1_id == max_qubit_id)
            assert q1_id == max_qubit_id  # You need to define max_qubit_id somewhere
            return self._device.get_physical_qubit(q0_id).get_occupied_time()

        q0 = self._device.get_physical_qubit(q0_id)
        q1 = self._device.get_physical_qubit(q1_id)

        apsp_cost = 0
        if self._apsp:
            path = self._device.get_path(q0_id, q1_id)
            apsp_cost = len(path)

        if min_max == MinMaxOptionType.max:
            avail = max(q0.get_occupied_time(), q1.get_occupied_time())
        else:
            avail = min(q0.get_occupied_time(), q1.get_occupied_time())

        return avail + apsp_cost // apsp_coeff 

    def is_executable(self, gate: QCirGate) -> bool:
        # TODO: implement logic
        return False

    # Main Router functions
    def execute_single(self, gate: QCirGate, q: QubitIdType) -> GateInfo:
        qubit = self._device.get_physical_qubit(q)
        start_time = qubit.get_occupied_time()
        end_time = start_time + self._device.get_delay(gate)
        qubit.set_occupied_time(end_time)
        qubit.reset()
        # Construct the operation (adapt as needed for your QCirGate/Instruction types)
        op = QCirGate(0, gate.get_operation(), [q, max_qubit_id])
        return (op, (start_time, end_time))

    def duostra_routing(
        self,
        gate: QCirGate,
        qubit_pair: Tuple[QubitIdType, QubitIdType],
        tie_breaking_strategy: MinMaxOptionType,
    ) -> List[GateInfo]:
        assert gate.get_num_qubits() == 2

        q0_id, q1_id = qubit_pair
        swap_ids = False

        # Compare occupied time
        q0_time = self._device.get_physical_qubit(q0_id).get_occupied_time()
        q1_time = self._device.get_physical_qubit(q1_id).get_occupied_time()

        if q0_time > q1_time:
            q0_id, q1_id = q1_id, q0_id
            swap_ids = True
        elif q0_time == q1_time:
            # Tie-breaking by logical qubit index
            q0_logical = self._device.get_physical_qubit(q0_id).get_logical_qubit()
            q1_logical = self._device.get_physical_qubit(q1_id).get_logical_qubit()
            if tie_breaking_strategy == MinMaxOptionType.min and q0_logical > q1_logical:
                q0_id, q1_id = q1_id, q0_id
                swap_ids = True

        t0 = self._device.get_physical_qubit(q0_id)
        t1 = self._device.get_physical_qubit(q1_id)

        # Priority queue for propagation
        pq: PriorityQueue = PriorityQueue()

        # Initialize source qubits
        t0.mark(False, t0.get_id())
        t0.take_route(t0.get_cost(), 0)
        t1.mark(True, t1.get_id())
        t1.take_route(t1.get_cost(), 0)

        is_adjacent, *_ = self._touch_adjacency(t0, pq, False)
        self._touch_adjacency(t1, pq, True)

        swap_delay = self._device.get_delay(QCirGate(SwapGate(), [0, 1]))

        # Propagate paths until they meet
        while not is_adjacent:
            next_node = pq.get()  # equivalent to priority_queue.top() + pop()
            q_next_id = next_node.get_id()
            q_next = self._device.get_physical_qubit(q_next_id)

            # Ensure correct source
            assert q_next.get_source() == next_node.get_source()

            cost = next_node.get_cost()
            assert cost >= swap_delay
            operation_time = cost - swap_delay
            q_next.take_route(cost, operation_time)

            touch_result = self._touch_adjacency(q_next, pq, next_node.get_source())
            is_adjacent = touch_result[0]

            if is_adjacent:
                if next_node.get_source():
                    q0_id = touch_result[1]
                    q1_id = q_next_id
                else:
                    q0_id = q_next_id
                    q1_id = touch_result[1]

        # Traceback to get operation list
        operation_list = self._traceback(
            gate,
            self._device.get_physical_qubit(q0_id),
            self._device.get_physical_qubit(q1_id),
            t0,
            t1,
            swap_ids,
        )

        # Reset all qubits
        for i in range(self._device.get_num_qubits()):
            qubit = self._device.get_physical_qubit(i)
            qubit.reset()
            assert qubit.get_logical_qubit() < self._device.get_num_qubits()

        return operation_list

    def apsp_routing(
        self,
        gate: QCirGate,
        qs: Tuple[QubitIdType, QubitIdType],
        tie_breaking_strategy: MinMaxOptionType,
    ) -> List[GateInfo]:
        operation_list: List[GateInfo] = []

        s0_id, s1_id = qs
        q0_id, q1_id = s0_id, s1_id

        while not self._device.get_physical_qubit(q0_id).is_adjacency(
            self._device.get_physical_qubit(q1_id)
        ):
            q0_next, q0_cost = self._device.get_next_swap_cost(q0_id, s1_id)
            q1_next, q1_cost = self._device.get_next_swap_cost(q1_id, s0_id)

            if (
                q0_cost < q1_cost
                or (
                    q0_cost == q1_cost
                    and tie_breaking_strategy == MinMaxOptionType.min
                    and self._device.get_physical_qubit(q0_id).get_logical_qubit()
                    < self._device.get_physical_qubit(q1_id).get_logical_qubit()
                )
            ):
                op = QCirGate(0, SwapGate(), [q0_id, q0_next])
                self._device.apply_gate(op, q0_cost)
                gate_info: GateInfo = (op, (q0_cost, q0_cost + self._device.get_delay(op)))
                operation_list.append(gate_info)
                q0_id = q0_next
            else:
                op = QCirGate(0, SwapGate(), [q1_id, q1_next])
                self._device.apply_gate(op, q1_cost)
                gate_info: GateInfo = (op, (q1_cost, q1_cost + self._device.get_delay(op)))
                operation_list.append(gate_info)
                q1_id = q1_next

        # Ensure qubits are adjacent
        assert self._device.get_physical_qubit(q1_id).is_adjacency(
            self._device.get_physical_qubit(q0_id)
        )

        gate_cost = max(
            self._device.get_physical_qubit(q0_id).get_occupied_time(),
            self._device.get_physical_qubit(q1_id).get_occupied_time(),
        )

        cx_gate = QCirGate(0, gate.get_operation(), [q0_id, q1_id])
        self._device.apply_gate(cx_gate, gate_cost)
        gate_info: GateInfo = (cx_gate, (gate_cost, gate_cost + self._device.get_delay(gate)))
        operation_list.append(gate_info)

        return operation_list

    def assign_gate(self, gate: QCirGate) -> List[GateInfo]:
        # TODO: implement logic
        return []

    # Internal helpers
    def _initialize(self):
        if self._apsp:
            self._device.calculate_path()

        num_qubits = self._device.get_num_qubits()
        self._logical_to_physical = list(range(num_qubits)) #TODO: mapping array

        pass

    def _get_physical_qubits(self, gate: Instruction) -> Tuple[QubitIdType, QubitIdType]:
        if gate[0].name == 'cx':
            control_qubit = self._logical_to_physical[gate[1][0].index]
            target_qubit = self._logical_to_physical[gate[1][1].index]
            return (control_qubit, target_qubit)
        if gate[0].name == 'measure':
            return (self._logical_to_physical[gate[1][0].index], self._logical_to_physical[gate[1][1].index])
        if gate[0].name == 'swap':
            qubit1 = self._logical_to_physical[gate[1][0].index]
            qubit2 = self._logical_to_physical[gate[1][1].index]
            return (qubit1, qubit2)

        logical_qubit = gate.index
        physical_qubit = self._logical_to_physical[logical_qubit]
        return (physical_qubit, physical_qubit) #TODO: nusetint i didesni

    def _touch_adjacency(
        self,
        qubit: PhysicalQubit,
        pq: "PriorityQueue",
        source: bool
    ) -> Tuple[bool, QubitIdType]:
        """
        Mark all adjacent qubits as seen and push them into the priority queue.
        Returns (touch_occurred, target_qubit_id)
        """
        for adj_id in qubit.get_adjacencies():
            adj = self._device.get_physical_qubit(adj_id)

            if adj.is_marked():
                # If already taken and from a different path, paths meet
                if adj.is_taken() and adj.get_source() != source:
                    assert adj.get_id() == adj_id
                    return True, adj.get_id()
                continue

            # Push into the priority queue
            cost = max(qubit.get_cost(), adj.get_occupied_time()) + self._device.get_delay(QCirGate(SwapGate(), [0, 1]))
            adj.mark(source, qubit.get_id())
            pq.put(AStarNode(cost, adj.get_id(), source))  # Python PriorityQueue uses put()

        return False, max_qubit_id 

    def _traceback(
        self,
        gate: QCirGate,
        q0: PhysicalQubit,
        q1: PhysicalQubit,
        t0: PhysicalQubit,
        t1: PhysicalQubit,
        swap_ids: bool,
    ) -> List[GateInfo]:
        # TODO: implement traceback routing logic
        return []

