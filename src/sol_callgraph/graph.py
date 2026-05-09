import os
from collections import deque
from typing import List, Set, Dict, Any, Optional, Tuple
from slither.core.declarations import Contract, Function, Modifier
from slither.slithir.operations import SolidityCall, LibraryCall, HighLevelCall, LowLevelCall

class CallGraph:
    def __init__(self, slither, config):
        self.sl = slither
        self.config = config
        self.nodes = {}  # id -> {label, type, obj}
        self.edges = set()  # (src_id, dst_id, kind)
        self.processed_functions = set()
        self.root_functions = set()

    def build(self):
        self._select_root_functions()
        if not self.root_functions:
            return False

        queue = deque([(f, 0) for f in self.root_functions])
        seen = {f.canonical_name for f in self.root_functions}

        # Root functions/modifiers are already in the nodes with 'root' type
        for f in self.root_functions:
            self._add_node(f.canonical_name, self._get_label(f), "root", f)

        edge_count = 0
        while queue:
            func, depth = queue.popleft()
            
            if depth >= self.config.depth:
                continue

            # Collect edges
            edges = self._collect_edges(func)
            for dst_id, dst_label, kind, dst_obj in edges:
                self.edges.add((func.canonical_name, dst_id, kind))
                edge_count += 1
                
                # Check if we should expand dst
                if dst_obj and isinstance(dst_obj, (Function, Modifier)):
                    if dst_id not in seen:
                        seen.add(dst_id)
                        queue.append((dst_obj, depth + 1))
                        
                        # Add node as expandable if not already added as root
                        if dst_id not in self.nodes:
                            self._add_node(dst_id, dst_label, "expandable", dst_obj)
                else:
                    # Builtin-like or unresolved
                    if dst_id not in self.nodes:
                        node_type = "builtin-like" if kind == "solidity" else "unresolved"
                        self._add_node(dst_id, dst_label, node_type, dst_obj)

        if self.config.verbose:
            print(f"Graph built: {len(self.nodes)} nodes, {edge_count} edges", file=os.sys.stderr)
            print(f"Root functions: {len(self.root_functions)}", file=os.sys.stderr)

        return True

    def _select_root_functions(self):
        target_abs_path = os.path.realpath(self.config.target)
        
        # Determine target contracts
        target_contracts = []
        if self.config.contracts:
            for c_name in self.config.contracts:
                found = False
                for c in self.sl.contracts:
                    if c.name == c_name:
                        target_contracts.append(c)
                        found = True
                        break
                if not found:
                    # Will be handled by core.py for exit 3
                    pass
        else:
            # Default to all contracts in target file
            in_file_contracts = []
            for c in self.sl.contracts:
                if self._is_in_target_file(c, target_abs_path):
                    in_file_contracts.append(c)
            
            if not self.config.quiet and len(in_file_contracts) > 1:
                decls = [f"{c.name}({c.contract_kind})" for c in in_file_contracts]
                print(f"warning: multiple declarations found in {self.config.target}: {', '.join(decls)}", file=os.sys.stderr)
                print(f"warning: using all executable declarations in target file as root scope; use --contract <name> to narrow it", file=os.sys.stderr)

            for c in in_file_contracts:
                # Default rules: include contracts and libraries, skip interfaces unless requested
                if c.contract_kind == "interface":
                    continue
                target_contracts.append(c)

        # Collect functions from target contracts
        for c in target_contracts:
            # ONLY declared functions and modifiers, and MUST be in target file
            for f in c.functions_and_modifiers_declared:
                if f.is_implemented and self._is_in_target_file(f, target_abs_path):
                    self.root_functions.add(f)

    def _is_in_target_file(self, obj, target_abs_path):
        if not hasattr(obj, 'source_mapping') or not obj.source_mapping:
            return False
        # Some versions of slither have different structure for source_mapping
        # But usually we can get the filename
        try:
            filename = os.path.realpath(obj.source_mapping.filename.absolute)
            return filename == target_abs_path
        except:
            return False

    def _get_label(self, func):
        if func in self.root_functions:
            # Short name for root functions
            return func.name + "()"
        return func.canonical_name

    def _add_node(self, node_id, label, node_type, obj):
        if node_id not in self.nodes:
            self.nodes[node_id] = {"label": label, "type": node_type, "obj": obj}

    def _collect_edges(self, func):
        edges = [] # List of (dst_id, dst_label, kind, dst_obj)
        
        # 0. Modifiers (Higher priority to label as 'modifier')
        modifier_names = set()
        if hasattr(func, 'modifiers'):
            for m in func.modifiers:
                edges.append((m.canonical_name, m.canonical_name, "modifier", m))
                modifier_names.add(m.canonical_name)

        # 1. Internal calls
        for ic in func.internal_calls:
            if isinstance(ic, (Function, Modifier)):
                if ic.canonical_name in modifier_names:
                    continue # Already handled as modifier
                edges.append((ic.canonical_name, ic.canonical_name, "internal", ic))
            elif hasattr(ic, 'function') and ic.function:
                 f = ic.function
                 if hasattr(f, 'canonical_name'):
                     if f.canonical_name in modifier_names:
                         continue
                     edges.append((f.canonical_name, f.canonical_name, "internal", f))
                 else:
                     edges.append((str(f), str(f), "solidity", None))

        # 2. Solidity calls
        for sc in func.solidity_calls:
            f = sc.function
            label = str(f)
            edges.append((label, label, "solidity", None))

        # 3. High level calls
        for hlc in func.high_level_calls:
            if isinstance(hlc, tuple):
                contract, op = hlc
                if hasattr(op, 'function') and op.function:
                    f = op.function
                    if hasattr(f, 'canonical_name'):
                        edges.append((f.canonical_name, f.canonical_name, "high_level", f))
                    else:
                        edges.append((f"{contract.name}.{op}", f"{contract.name}.{op}", "high_level", None))
                else:
                    edges.append((f"{contract.name}.{op}", f"{contract.name}.{op}", "high_level", None))

        # 4. Library calls
        for lc in func.library_calls:
            f = lc.function
            if hasattr(f, 'canonical_name'):
                edges.append((f.canonical_name, f.canonical_name, "library", f))

        # 5. Low level calls
        for llc in func.low_level_calls:
            label = str(llc)
            edges.append((label, label, "low_level", None))

        # Deduplicate and prioritize
        return self._deduplicate_edges(edges)

    def _deduplicate_edges(self, edges):
        # Priority: low_level > library > high_level > internal > solidity > modifier
        priority = {
            "low_level": 0,
            "library": 1,
            "high_level": 2,
            "internal": 3,
            "solidity": 4,
            "modifier": 5
        }
        
        best_edges = {} # dst_id -> (dst_label, kind, dst_obj)
        for dst_id, dst_label, kind, dst_obj in edges:
            if dst_id not in best_edges:
                best_edges[dst_id] = (dst_label, kind, dst_obj)
            else:
                current_kind = best_edges[dst_id][1]
                if priority[kind] < priority[current_kind]:
                    best_edges[dst_id] = (dst_label, kind, dst_obj)
        
        return [(dst_id, label, kind, obj) for dst_id, (label, kind, obj) in best_edges.items()]
