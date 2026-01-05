from quantum_compiler.core.mapper_registry import MapperRegistry
from tests.benchmarks.test_circuits import get_test_circuits
from tests.benchmarks.test_pauli_strings import get_test_pauli_strings
from tests.test_suite import CorrectnessTestSuite
from quantum_compiler.backends.factory import BackendFactory
from topologies.topologies import topology_functions


def run_algorithm_validation_tests():
    mappers_discovery = MapperRegistry()
    mappers = mappers_discovery.get_all_mappers()

    backend_factory = BackendFactory(
        legacy_topology_dict=topology_functions
    )
    backends = backend_factory.get_all_backends()

    basic_circuits = get_test_circuits()
    basic_pauli_strings = get_test_pauli_strings()

    for _, backend in backends.items():
        print(f"Running tests on backend: {backend.name} {backend.num_qubits} qubits")
        test_suite = CorrectnessTestSuite(backend)

        for _, mapper in mappers.items():
            print(f" Testing mapper: {mapper.name}")
            test_suite.test_algorithm(mapper, basic_circuits, basic_pauli_strings)


if __name__ == "__main__":
    run_algorithm_validation_tests()
