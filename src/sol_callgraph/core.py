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
    if not cg.build():
        print(f"error: no root functions found in {config.target}", file=sys.stderr)
        if config.contracts:
             print(f"Available declarations:", file=sys.stderr)
             target_abs_path = os.path.realpath(config.target)
             for c in sl.contracts:
                 if hasattr(c, 'source_mapping') and c.source_mapping:
                     try:
                         if os.path.realpath(c.source_mapping.filename.absolute) == target_abs_path:
                             print(f"  {c.name:<20} {c.contract_kind}", file=sys.stderr)
                     except: pass
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
        # SVG or PNG
        run_dot(dot_content, config.format, config.out)
        # if not config.out, run_dot returns bytes, but we need to handle stdout
        if not config.out:
            binary_output = run_dot(dot_content, config.format)
            if binary_output:
                sys.stdout.buffer.write(binary_output)

if __name__ == "__main__":
    main()
