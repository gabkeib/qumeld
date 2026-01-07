from experiments.experiments_runner import ExperimentConfig, ExperimentRunner
from quantum_algorithms.registry import AlgorithmRegistry
from quantum_compiler.core.mapper_registry import MapperRegistry
from quantum_compiler.mappers.base_mapper import QubitMapper
from quantum_compiler.utils.paths import get_project_root
from quantum_compiler.backends.factory import BackendFactory
from topologies.topologies import topology_functions
from typing import Any, List
from pathlib import Path
from datetime import datetime
from qiskit.providers import BackendV2


def run_experiments(
    topologies: List[str],
    algorithms: List[str],
    optimizers: List[str],
    output_dir: str = None,
):
    # Setup mappers
    mappers_discovery = MapperRegistry()

    # Setup backends
    backend_factory = BackendFactory()

    algorithm_registry = AlgorithmRegistry()

    experiments_runner = ExperimentRunner(
        mapper_registry=mappers_discovery,
        backend_factory=backend_factory,
        algorithm_registry=algorithm_registry,
    )

    print(algorithm_registry.list_algorithms())

    project_root = get_project_root()
    if not output_dir:
        timestamp = int(datetime.now().timestamp())
        output_dir = f"{project_root}/results/{timestamp}"

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for backend in topologies:
        Path(f"{output_dir}/{backend}").mkdir(exist_ok=True)
        for algorithm_name in algorithms:
            for mapper in optimizers:
                algorithm_params: dict[str, Any] = {"name": algorithm_name}
                if algorithm_name == "qaoa" or algorithm_name == "qaoa_ansatz":
                    algorithm_params["graph"] = [
                        [0, 1, 1, 0, 1],
                        [1, 0, 1, 0, 0],
                        [1, 1, 0, 1, 0],
                        [0, 0, 1, 0, 1],
                        [1, 0, 0, 1, 0],
                    ]
                    algorithm_params["num_qubits"] = 5

                if algorithm_name == "efficient_su2":
                    algorithm_params["num_qubits"] = 5

                print(
                    f"Running experiment: Backend={backend}, Algorithm={algorithm_name}, Mapper={mapper}"
                )
                config = ExperimentConfig(
                    quantum_computer=backend,
                    quantum_algorithm=algorithm_name,
                    mapper_name=mapper,
                    output_dir=f"{output_dir}/{backend}/{algorithm_name}",
                    algorithm_params=algorithm_params,
                )
                experiments_runner.run_experiment(config)
