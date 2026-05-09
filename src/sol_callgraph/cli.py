import argparse
import sys
from typing import List, Optional

class SmartArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write(f'error: {message}\n\n')
        self.print_help()
        sys.exit(1)

class Config:
    def __init__(self, args: argparse.Namespace, parser: SmartArgumentParser):
        self.target = args.target
        self.contracts = args.contract or []
        self.depth = args.depth
        self.out = args.out
        self.format = args.format
        self.list_contracts = args.list_contracts
        self.quiet = args.quiet
        self.verbose = args.verbose
        self.parser = parser
        # Phase 2
        self.root = args.root
        self.no_root_detect = args.no_root_detect
        self.print_env = args.print_env
        self.include_inherited = args.include_inherited
        self.include_interfaces = args.include_interfaces
        self.root_function = args.root_function or []
        # Phase 2 Display Controls
        self.include_events = args.include_events
        self.no_errors = args.no_errors
        self.no_builtins = args.no_builtins
        self.no_constructors = args.no_constructors
        self.include_overrides = args.include_overrides
        self.cluster = args.cluster
        # Phase 2 Size Protection & Diagnostics
        self.max_nodes = args.max_nodes
        self.max_edges = args.max_edges
        self.fail_on_unresolved = args.fail_on_unresolved
        self.fail_on_warning = args.fail_on_warning
        # Phase 2 Slither/solc passthrough
        self.slither_args = args.slither_arg or []
        self.solc_remaps = args.solc_remaps
        self.solc_args = args.solc_args
        self.compile_force_framework = args.compile_force_framework
        self.debug_slither = args.debug_slither

def parse_args(args: List[str]) -> Config:
    description = (
        "sol-callgraph: A focused call graph exporter for Solidity.\n\n"
        "This tool generates concise call graphs centered around a specific Solidity file or contract.\n"
        "Unlike standard Slither printers, it ensures that critical calls across files, libraries, \n"
        "and proxies (like ERC1967) are retained while filtering out project-wide noise.\n\n"
        "Environment Management:\n"
        "  --debug-env              (Launcher only) Print Slither environment info and exit\n"
        "  --slither-python <path>  (Launcher only) Explicitly set the Python interpreter with Slither installed\n"
        "  --print-env              Print compilation environment info and exit"
    )
    
    parser = SmartArgumentParser(
        prog="sol-callgraph",
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Positionals
    parser.add_argument(
        "target",
        nargs="?",
        help="Target Solidity file"
    )
    
    # Options
    parser.add_argument(
        "-c", "--contract",
        action="append",
        help="Focus on specific contract/library/interface (can be repeated)"
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=1,
        help="Depth of call graph expansion (default: 1)"
    )
    parser.add_argument(
        "-o", "--out",
        help="Output file path (default: stdout)"
    )
    parser.add_argument(
        "--format",
        choices=["dot", "svg", "png", "json"],
        default="dot",
        help="Output format (default: dot)"
    )
    parser.add_argument(
        "--list-contracts",
        action="store_true",
        help="List all recognized contracts/libraries in the target file and exit"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress non-essential warnings"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable detailed diagnostic logging"
    )
    
    # Phase 2 Options
    parser.add_argument(
        "--root",
        help="Explicitly specify the Solidity project root directory"
    )
    parser.add_argument(
        "--no-root-detect",
        action="store_true",
        help="Disable automatic project root detection"
    )
    parser.add_argument(
        "--print-env",
        action="store_true",
        help="Print detected compilation environment and exit"
    )
    parser.add_argument(
        "--include-inherited",
        action="store_true",
        help="Include inherited functions/modifiers in the root scope"
    )
    parser.add_argument(
        "--include-interfaces",
        action="store_true",
        help="Include interface functions as root nodes"
    )
    parser.add_argument(
        "--root-function",
        action="append",
        help="Start the call graph from specific function names (can be repeated)"
    )
    
    parser.add_argument(
        "--include-events",
        action="store_true",
        help="Include event emissions in the graph"
    )
    parser.add_argument(
        "--no-errors",
        action="store_true",
        help="Hide custom error and revert nodes"
    )
    parser.add_argument(
        "--no-builtins",
        action="store_true",
        help="Hide Solidity built-in functions (e.g., abi.decode, keccak256)"
    )
    parser.add_argument(
        "--no-constructors",
        action="store_true",
        help="Exclude constructor functions from the root scope"
    )
    parser.add_argument(
        "--include-overrides",
        action="store_true",
        help="Include override/overrides relationships in the graph"
    )
    
    parser.add_argument(
        "--cluster",
        action="store_true",
        default=False,
        help="Cluster functions by contract"
    )
    parser.add_argument(
        "--no-cluster",
        action="store_false",
        dest="cluster",
        help="Disable clustering (default)"
    )
    
    parser.add_argument(
        "--max-nodes",
        type=int,
        default=500,
        help="Maximum number of nodes in the graph (default: 500, 0 for unlimited)"
    )
    parser.add_argument(
        "--max-edges",
        type=int,
        default=1000,
        help="Maximum number of edges in the graph (default: 1000, 0 for unlimited)"
    )
    parser.add_argument(
        "--fail-on-unresolved",
        action="store_true",
        help="Exit with non-zero code if there are unresolved calls"
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with non-zero code if there are warnings"
    )
    
    # Phase 2 Slither/solc passthrough
    parser.add_argument(
        "--slither-arg",
        action="append",
        help="Pass extra arguments to Slither (can be repeated)"
    )
    parser.add_argument(
        "--solc-remaps",
        help="Pass remappings to solc"
    )
    parser.add_argument(
        "--solc-args",
        help="Pass extra arguments to solc"
    )
    parser.add_argument(
        "--compile-force-framework",
        choices=["foundry", "hardhat", "truffle", "brownie", "ape"],
        help="Force Slither to use a specific compilation framework"
    )
    parser.add_argument(
        "--debug-slither",
        action="store_true",
        help="Show detailed Slither invocation and environment info"
    )

    parsed_args = parser.parse_args(args)

    if parsed_args.target == "-":
        sys.stderr.write("error: stdin input '-' is not supported. sol-callgraph requires a real file path for Slither analysis.\n\n")
        parser.print_help()
        sys.exit(1)

    if parsed_args.depth < 1:
        sys.stderr.write("error: --depth must be >= 1\n\n")
        parser.print_help()
        sys.exit(1)
        
    return Config(parsed_args, parser)
