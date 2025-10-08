from experiments import run_experiments
from pathlib import Path
from datetime import datetime

if __name__ == "__main__":

    quantum_computer_topologies = [
        "rigetti_novera_q9"
    ]

    algorithms_to_run = [
        "vqe_demo",
        "vqe_H2",
        # "vqe_LiH"
    ]

    circuit_optimisation_algorithms = [
        # "sabre",
        # "qiskit",
        # "pauliforest",
        "doustra"
    ]

    Path("./results").mkdir(exist_ok=True)

    timestamp = int(datetime.now().timestamp())
    Path(f"./results/{timestamp}").mkdir(exist_ok=True)

    for quantum_computer in quantum_computer_topologies:
        Path(f"./results/{timestamp}/{quantum_computer}").mkdir(exist_ok=True)
        for algorithm in algorithms_to_run:
            for circuit_optimisation_algorithm in circuit_optimisation_algorithms:
                print(f"Running {quantum_computer} with {algorithm} using {circuit_optimisation_algorithm}")
                run_experiments.run_experiments_paulistrings(quantum_computer, algorithm, circuit_optimisation_algorithm, path_to_save=f"./results/{timestamp}/{quantum_computer}/{algorithm}")
