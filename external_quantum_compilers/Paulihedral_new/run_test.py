from benchmark.mypauli import *
from parallel_bl import *
from tools import *
from qiskit import transpile
import time
import synthesis_SC

def rigetti_novera_q9():
    qubits = 9
    graph = []
    graph.append([0, 1])
    graph.append([1, 2])
    graph.append([0, 3])
    graph.append([1, 4])
    graph.append([2, 5])
    graph.append([3, 4])
    graph.append([4, 5])
    graph.append([3, 6])
    graph.append([4, 7])
    graph.append([5, 8])
    graph.append([6, 7])
    graph.append([7, 8])

    return (graph, qubits)

def get_distance_matrix(graph, qubits):
    dist_matrix = np.full((qubits, qubits), np.inf)
    for i in range(qubits):
        dist_matrix[i][i] = 0
    for (a, b) in graph:
        dist_matrix[a][b] = 1
        dist_matrix[b][a] = 1
    for k in range(qubits):
        for i in range(qubits):
            for j in range(qubits):
                if dist_matrix[i][k] + dist_matrix[k][j] < dist_matrix[i][j]:
                    dist_matrix[i][j] = dist_matrix[i][k] + dist_matrix[k][j]
    return dist_matrix

ctime = time.time
parr = [
    [pauliString("XXXII", 1.0), pauliString("XXIII", 1.0)],
    [pauliString("XXIXI", 1.0), pauliString("XXIIX", 1.0)],
]
parr = [
    [pauliString("YZZZZYYIY", 1.0), pauliString("XYIXXIZYZ", 1.0)],
    [pauliString("XXIIXXYXI", 1.0), pauliString("ZIIIXYYYY", 1.0)],
    [pauliString("XZYYXZXYI", 1.0)]
]
nq = len(parr[0][0])
length = (
    nq // 2
)  # `length' is a hyperparameter, and can be adjusted for best performance
t0 = ctime()
a1 = depth_oriented_scheduling(parr, length=length, maxiter=30)

topology, qubits = rigetti_novera_q9()
G = np.zeros((qubits, qubits))
for i, j in topology:
    G[i, j] = 1
    G[j, i] = 1

C = get_distance_matrix(topology, qubits)

graph = synthesis_SC.pGraph(G, C)

qc = synthesis_SC.block_opt_SC(a1, graph=graph)
print("PH, Time costed:", ctime() - t0, flush=True)
t0 = ctime()
qc2 = transpile(qc, basis_gates=["u3", "cx"], optimization_level=3)
# print_qc(qc2)
print(qc.draw())
# qc = synthesis_FT.qiskit_synthesis(a1)
# print("Qiskit, Time costed:", ctime() - t0, flush=True)
# t0 = ctime()
# qc2 = transpile(qc, basis_gates=["u3", "cx"], optimization_level=3)
# print_qc(qc2)