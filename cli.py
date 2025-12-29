import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List

from experiments import run_experiments
from topologies import topologies
from qiskit import QuantumCircuit

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
        """
    )
    
    all_optimisers = run_experiments.circuit_optimisation_algorithms.keys()
    pauli_algorithms = run_experiments.pauli_algorithms.keys()
    circuit_algorithms = run_experiments.circuits.keys()
    all_algorithms = list(pauli_algorithms) + list(circuit_algorithms)
    all_topologies = topologies.topology_functions.keys()  

    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Circuit optimization command
    optimize_parser = subparsers.add_parser('optimize', help='Optimize a single quantum circuit')
    optimize_parser.add_argument('--circuit', '-c', required=True, 
                               help='Path to quantum circuit file (.qasm)')
    optimize_parser.add_argument('--topology', '-t', required=True,
                               choices=all_topologies,
                               help='Quantum computer topology')
    optimize_parser.add_argument('--optimizer', '-o', nargs='+', 
                               choices=all_optimisers,
                               default=['qiskit'],
                               help='Circuit optimization algorithm(s)')
    optimize_parser.add_argument('--output', '-out', 
                               help='Output directory (default: ./results/timestamp)')
    
    # Experiment command
    exp_parser = subparsers.add_parser('experiment', help='Run full experiments')
    exp_parser.add_argument('--topologies', '-t', nargs='+',
                          choices=all_topologies,
                          default=all_topologies,
                          help='Quantum computer topologies')
    exp_parser.add_argument('--algorithms', '-a', nargs='+',
                          choices=all_algorithms,
                          default=all_algorithms,
                          help='Algorithms to run')
    exp_parser.add_argument('--optimizers', '-o', nargs='+',
                          choices=all_optimisers,
                          default=all_optimisers,
                          help='Circuit optimization algorithms')
    exp_parser.add_argument('--output', '-out',
                          help='Output directory (default: ./results/timestamp)')
    
    return parser.parse_args()

def optimize_circuit(circuit_path: str, topology: str, optimizers: List[str], output_dir: str = None):
    """Optimize a single quantum circuit"""
    
    # Validate circuit file exists
    circuit_file = Path(circuit_path)
    if not circuit_file.exists():
        print(f"Error: Circuit file {circuit_path} not found")
        return False
    
    # Load circuit
    try:
        with open(circuit_file, 'r') as f:
            circuit = QuantumCircuit.from_qasm_str(f.read())
        print(f"Circuit loaded: {circuit.num_qubits} qubits, depth {circuit.depth()}")
    except Exception as e:
        print(f"Error loading circuit: {e}")
        return False
    
    if not output_dir:
        timestamp = int(datetime.now().timestamp())
        output_dir = f"./optimisation_results/{timestamp}/"
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    results = []
    for optimizer in optimizers:
        print(f"Optimizing with {optimizer}")
        try:

            result = run_experiments.run_circuit_optimisation(
                circuit, topology, optimizer, 
                path_to_save=f"{output_dir}/{optimizer}.qasm"
            )
            results.append(result)
            print(f"{optimizer}: {result.swap_count} swaps, depth {result.depth}")
        except Exception as e:
            print(f"{optimizer} error: {e}")
    
    # Print summary
    if results:
        print(f"Optimization Summary:")
        print("-" * 50)
        for result in results:
            print(f"{result.name:12} | Swaps: {result.swap_count:3} | Depth: {result.depth:4} | Time: {result.optimisation_time:.3f}s")
        
        # Find best
        best_swaps = min(results, key=lambda x: x.swap_count)
        best_depth = min(results, key=lambda x: x.depth)
        best_time = min(results, key=lambda x: x.optimisation_time)
        
        print(f" Best Results:")
        print(f"   Fewest swaps: {best_swaps.name} ({best_swaps.swap_count})")
        print(f"   Shortest depth: {best_depth.name} ({best_depth.depth})")
        print(f"   Fastest: {best_time.name} ({best_time.optimisation_time:.3f}s)")    
    return True

def run_experiments_cli(topologies: List[str], algorithms: List[str], optimizers: List[str], output_dir: str = None):
    # Setup output directory
    if not output_dir:
        timestamp = int(datetime.now().timestamp())
        output_dir = f"./results/{timestamp}"
    
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Running experiments")
    
    for topology in topologies:
        Path(f"{output_dir}/{topology}").mkdir(exist_ok=True)
        for algorithm in algorithms:
            for optimizer in optimizers:
                print(f"Running {topology} with {algorithm} using {optimizer}")
                run_experiments.run_experiments(
                    topology, algorithm, optimizer, 
                    path_to_save=f"{output_dir}/{topology}/{algorithm}"
                )

def main():
    args = parse_arguments()

    print(args)
    
    if not args.command:
        print("Error: Please specify a command (optimize or experiment)")
        print("Use --help for more information")
        return 1
    
    try:
        if args.command == 'optimize':
            success = optimize_circuit(
                circuit_path=args.circuit,
                topology=args.topology,
                optimizers=args.optimizer,
                output_dir=args.output
            )
            return 0 if success else 1
            
        elif args.command == 'experiment':
            run_experiments_cli(
                topologies=args.topologies,
                algorithms=args.algorithms,
                optimizers=args.optimizers,
                output_dir=args.output
            )
            return 0
            
    except KeyboardInterrupt:
        print("Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
