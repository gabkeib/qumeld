
# Usage of mapping
# /**
#  * @brief Place logical qubit
#  *
#  * @param assign
#  */
# void Device::place(std::vector<QubitIdType> const& assignment) {
#     for (size_t i = 0; i < assignment.size(); ++i) {
#         assert(_qubit_list[assignment[i]].get_logical_qubit() == std::nullopt);
#         _qubit_list[assignment[i]].set_logical_qubit(i);
#     }
# }

def dfs_mapping(quantum_computer):
    visited = [False] * len(quantum_computer)
    assignList = []
    _dfs(quantum_computer, visited, assignList, 0)
    return assignList


def _dfs(quantum_computer, visited, assignList, current_qubit):
    if visited[current_qubit]:
        return
    visited[current_qubit] = True
    adjacency_waitlist = []
    assignList.append(current_qubit)
    for neighbor in quantum_computer[current_qubit]:
        if visited[neighbor]:
            continue
        if len(quantum_computer[neighbor]) > 1:
            adjacency_waitlist.append(neighbor)
        else:
            _dfs(quantum_computer, visited, assignList, neighbor)
    for node in adjacency_waitlist:
        if not visited[node]:
            _dfs(quantum_computer, visited, assignList, node)
