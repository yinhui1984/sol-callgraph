import sys
import os
from slither import Slither
from sol_callgraph.cli import parse_args
from sol_callgraph.graph import CallGraph
from sol_callgraph.dot import DotRenderer, format_node
from sol_callgraph.graphviz import run_dot

def main():
    config = parse_args(sys.argv[1:])
    
    if not config.target and not config.list_contracts:
        sys.stderr.write("error: no target file specified\n\n")
        config.parser.print_help()
        sys.exit(1)

    if not os.path.exists(config.target):
        print(f"error: target file not found: {config.target}", file=sys.stderr)
        sys.exit(3)

    try:
        sl = Slither(config.target)
    except Exception as e:
        print(f"error: Slither/solc failed to parse {config.target}: {e}", file=sys.stderr)
        sys.exit(2)

    if config.list_contracts:
        target_abs_path = os.path.realpath(config.target)
        for c in sl.contracts:
            if hasattr(c, 'source_mapping') and c.source_mapping:
                try:
                    filename = os.path.realpath(c.source_mapping.filename.absolute)
                    if filename == target_abs_path:
                        print(f"{c.name:<30} {c.contract_kind}")
                except:
                    pass
        sys.exit(0)

    cg = CallGraph(sl, config)
    
    # Task 2: Fix --contract not found error handling
    if config.contracts:
        target_abs_path = os.path.realpath(config.target)
        available_decls = []
        for c in sl.contracts:
            try:
                if os.path.realpath(c.source_mapping.filename.absolute) == target_abs_path:
                    available_decls.append(c)
            except: pass
            
        for c_name in config.contracts:
            if not any(c.name == c_name for c in sl.contracts):
                print(f"error: contract {c_name} not found in {config.target}", file=sys.stderr)
                print("Available declarations:", file=sys.stderr)
                for c in available_decls:
                    print(f"  {c.name:<20} {c.contract_kind}", file=sys.stderr)
                sys.exit(3)

    if not cg.build():
        print(f"error: no root functions found in {config.target}", file=sys.stderr)
        sys.exit(3)

    renderer = DotRenderer()
    for node_id, data in cg.nodes.items():
        format_node(renderer, node_id, data["label"], data["type"])
    
    for src, dst, kind in cg.edges:
        renderer.add_edge(src, dst, label=kind)
    
    dot_content = renderer.render()

    if config.format == "dot":
        if config.out:
            try:
                with open(config.out, 'w', encoding='utf-8') as f:
                    f.write(dot_content)
            except Exception as e:
                print(f"error: failed to write output file: {e}", file=sys.stderr)
                sys.exit(4)
        else:
            print(dot_content)
    else:
        # Task 3: SVG or PNG - Fix redundant call
        if config.out:
            run_dot(dot_content, config.format, config.out)
        else:
            binary_output = run_dot(dot_content, config.format)
            if binary_output:
                sys.stdout.buffer.write(binary_output)

if __name__ == "__main__":
    main()
