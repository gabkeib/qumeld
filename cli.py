import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import List

from quantum_algorithms.registry import AlgorithmRegistry
from quantum_compiler import mappers
from quantum_compiler.backends.factory import BackendFactory
from quantum_compiler.core.mapper_registry import MapperRegistry
from scripts.run_circuit_optimisation import run_circuit_optimisation
from scripts.run_experiments import run_experiments
from scripts.run_tests import run_algorithm_validation_tests
from topologies import topologies
from qiskit import QuantumCircuit
from topologies.topologies import topology_functions


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Quantum Circuit Optimization CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Optimize a circuit file
  python cli.py optimize --circuit my_circuit.qasm --topology rigetti_novera_q9 --optimizer sabre

  # Run full experiments
  python cli.py experiment --topologies rigetti_novera_q9 --algorithms vqe_demo --optimizers sabre qiskit

  # Optimize with multiple optimizers
  python cli.py optimize --circuit circuit.qasm --topology rigetti_novera_q9 --optimizer sabre qiskit doustra
        """,
    )

    parser.add_argument("-v", "--verbose", action="count", help="Enable verbose logging", default=0)

    backend_factory = BackendFactory()
    all_topologies = backend_factory.list_available()

    algorithms_registry = AlgorithmRegistry()
    all_algorithms = algorithms_registry.list_algorithms()

    mappers_discovery = MapperRegistry()
    all_optimisers = mappers_discovery.list_available_mappers()

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Circuit optimization command
    optimize_parser = subparsers.add_parser(
        "optimize", help="Optimize a single quantum circuit"
    )
    optimize_parser.add_argument(
        "--circuit", "-c", required=True, help="Path to quantum circuit file (.qasm)"
    )
    optimize_parser.add_argument(
        "--topology",
        "-t",
        required=True,
        choices=all_topologies,
        help="Quantum computer topology",
    )
    optimize_parser.add_argument(
        "--optimizers",
        "-o",
        nargs="+",
        choices=all_optimisers + ["auto"],
        default=["lightSABRE"],
        help="Circuit optimization algorithm(s)",
    )
    optimize_parser.add_argument(
        "--output", "-out", help="Output directory (default: ./results/timestamp)"
    )

    # Experiment command
    exp_parser = subparsers.add_parser("experiment", help="Run full experiments")
    exp_parser.add_argument(
        "--topologies",
        "-t",
        nargs="+",
        choices=all_topologies,
        default=all_topologies,
        help="Quantum computer topologies",
    )
    exp_parser.add_argument(
        "--algorithms",
        "-a",
        nargs="+",
        choices=all_algorithms,
        default=all_algorithms,
        help="Algorithms to run",
    )
    exp_parser.add_argument(
        "--optimizers",
        "-o",
        nargs="+",
        choices=all_optimisers,
        default=all_optimisers,
        help='Circuit optimization algorithm(s) or "auto" to return circuit with the best performance',
    )

    exp_parser.add_argument(
        "--output", "-out", help="Output directory (default: ./results/timestamp)"
    )

    test_parser = subparsers.add_parser("test", help="Run algorithm validation tests")

    return parser.parse_args()


def optimize_circuit(
    circuit_path: str, topology: str, optimizers: List[str], output_dir: str = None
):
    """Optimize a single quantum circuit"""

    # Validate circuit file exists
    circuit_file = Path(circuit_path)
    if not circuit_file.exists():
        print(f"Error: Circuit file {circuit_path} not found")
        return False

    # Load circuit
    try:
        with open(circuit_file, "r") as f:
            circuit = QuantumCircuit.from_qasm_str(f.read())
        print(f"Circuit loaded: {circuit.num_qubits} qubits, depth {circuit.depth()}")
    except Exception as e:
        print(f"Error loading circuit: {e}")
        return False

    if not output_dir:
        timestamp = int(datetime.now().timestamp())
        output_dir = f"./optimisation_results/{timestamp}/"

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results = run_circuit_optimisation(
        circuit=circuit,
        quantum_computer=topology,
        mappers_to_use=optimizers,
        output_dir=output_dir,
    )

    # Print summary
    if results:
        print(f"Optimization Summary (of {len(results)} results):")
        print("-" * 50)
        for result in results:
            print(
                f"{result.mapper:12} | Swaps: {result.swap_count:3} | Depth: {result.depth:4} | Time: {result.optimisation_time:.3f}s"
            )

        # Find best
        best_swaps = min(results, key=lambda x: x.swap_count)
        best_depth = min(results, key=lambda x: x.depth)
        best_time = min(results, key=lambda x: x.optimisation_time)

        print(f" Best Results:")
        print(f"   Fewest swaps: {best_swaps.mapper} ({best_swaps.swap_count})")
        print(f"   Shortest depth: {best_depth.mapper} ({best_depth.depth})")
        print(f"   Fastest: {best_time.mapper} ({best_time.optimisation_time:.3f}s)")
    return True


def run_tests_cli():
    run_algorithm_validation_tests()


def main():
    args = parse_arguments()

    level = logging.WARNING
    if args.verbose == 1:
        level = logging.INFO
    elif args.verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(levelname)s | %(name)s | %(message)s"
    )

    if not args.command:
        print("Error: Please specify a command (optimize or experiment)")
        print("Use --help for more information")
        return 1

    try:
        if args.command == "optimize":
            success = optimize_circuit(
                circuit_path=args.circuit,
                topology=args.topology,
                optimizers=args.optimizers,
                output_dir=args.output,
            )
            return 0 if success else 1

        elif args.command == "experiment":
            run_experiments(
                topologies=args.topologies,
                algorithms=args.algorithms,
                optimizers=args.optimizers,
            )
            return 0

        elif args.command == "test":
            run_tests_cli()
            return 0

    except KeyboardInterrupt:
        print("Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
