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

def parse_args(args: List[str]) -> Config:
    description = (
        "sol-callgraph: A focused call graph exporter for Solidity.\n\n"
        "This tool generates concise call graphs centered around a specific Solidity file or contract.\n"
        "Unlike standard Slither printers, it ensures that critical calls across files, libraries, \n"
        "and proxies (like ERC1967) are retained while filtering out project-wide noise."
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
        choices=["dot", "svg", "png"],
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

    parsed_args = parser.parse_args(args)

    if parsed_args.depth < 1:
        sys.stderr.write("error: --depth must be >= 1\n\n")
        parser.print_help()
        sys.exit(1)
        
    return Config(parsed_args, parser)
