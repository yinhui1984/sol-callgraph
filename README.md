# sol-callgraph

A focused call graph exporter for Solidity code using Slither.

## Introduction

`sol-callgraph` is a CLI tool designed to generate concise, focused call graphs for Solidity smart contracts. Unlike standard Slither printers that often produce overwhelming "all-contract" graphs, `sol-callgraph` centers the graph around a specific file or contract, ensuring critical calls across files, libraries, and proxies (like ERC1967) are retained while filtering out noise.

**Note**: `sol-callgraph` is a **focused static call graph exporter**. It is NOT an execution graph, an attack path searcher, or a blockchain state analyzer. It does not prove runtime reachability.

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd sol-callgraph

# Setup virtual environment and install in editable mode
python3 -m venv .venv
./.venv/bin/python -m pip install -e ".[dev]"
```

Slither must be installed in your environment. The tool will automatically detect your Slither installation (including pyenv shims).

## Usage

### Basic Usage

```bash
# Generate a focused call graph for a Solidity file
./sol-callgraph contracts/MyContract.sol

# Focus on a specific contract within a file
./sol-callgraph contracts/MyContract.sol --contract MyContract

# Increase expansion depth
./sol-callgraph contracts/MyContract.sol --depth 2
```

### Project Root & Compilation Context

`sol-callgraph` automatically detects your project root (Foundry, Hardhat, Truffle, etc.) by looking for markers like `foundry.toml` or `package.json`.

- `--root <dir>`: Explicitly specify the project root.
- `--no-root-detect`: Disable auto-detection and use current working directory.
- `--print-env`: Print detected environment information (root, slither paths, etc.) and exit.

### Scope Control

- `--contract <name>`: Focus on specific contract/library/interface.
- `--list-contracts`: List all recognized contracts in the target file.
- `--depth <n>`: Depth of call graph expansion (default: 1).

### Output Formats

- `--format dot`: Standard Graphviz DOT format (default).
- `--format svg`: Scalable Vector Graphics.
- `--format png`: Portable Network Graphics.
- `-o <path>`: Write output to a file instead of stdout.
  - **Note**: Relative output paths are resolved based on the directory where the command was executed, even if a project root is automatically detected.

## Environment Management

`sol-callgraph` uses a launcher-core architecture to ensure it runs with the correct Python interpreter where Slither is installed.

- `--debug-env`: Print Slither environment detection results and exit.
- `--slither-python <path>`: Manually specify the Python interpreter to use for Slither.

## Development & Testing

We use a local `.venv` for development. 

```bash
# Run all tests (unit, integration, OpenZeppelin smoke tests)
make test

# Run full OpenZeppelin self-test (processes ~40 contracts)
make test-selftest-oz

# Run everything
make test-all
```

Test reports are generated in `test-artifacts/`.

## Limitations

- Does not resolve runtime target for dynamic calls (low-level calls).
- Does not prove that a path is reachable in production.
- Interface functions without implementations are skipped as roots by default.
