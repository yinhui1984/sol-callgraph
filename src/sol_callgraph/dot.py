import json

def escape_dot_id(id_str: str) -> str:
    """Escapes a string for use as a DOT ID or label."""
    # Simple JSON dumps can handle many escapes, but DOT has its own rules.
    # For DOT, we just need to escape double quotes and backslashes, and handle newlines.
    escaped = id_str.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    return f'"{escaped}"'

class DotRenderer:
    def __init__(self, name: str = "focused_call_graph"):
        self.name = name
        self.nodes = []
        self.edges = []
        self.rankdir = "LR"

    def add_node(self, name: str, label: str = None, style: str = "rounded", class_attr: str = None, color: str = None):
        attrs = [f'style={escape_dot_id(style)}']
        if label:
            attrs.append(f'label={escape_dot_id(label)}')
        if class_attr:
            attrs.append(f'class={escape_dot_id(class_attr)}')
        if color:
            attrs.append(f'color={escape_dot_id(color)}')
            attrs.append(f'fontcolor={escape_dot_id(color)}')
        
        attr_str = ", ".join(attrs)
        self.nodes.append(f'  {escape_dot_id(name)} [{attr_str}];')

    def add_edge(self, src: str, dst: str, label: str = None):
        attrs = []
        if label:
            attrs.append(f'label={escape_dot_id(label)}')
        
        attr_str = ""
        if attrs:
            attr_str = f' [{", ".join(attrs)}]'
        
        self.edges.append(f'  {escape_dot_id(src)} -> {escape_dot_id(dst)}{attr_str};')

    def render(self) -> str:
        lines = [
            f'digraph {self.name} {{',
            f'  rankdir={escape_dot_id(self.rankdir)};',
            '  node [shape=box, style="rounded", fontname="Helvetica"];',
            '  edge [fontname="Helvetica"];',
            ''
        ]
        lines.extend(self.nodes)
        if self.nodes and self.edges:
            lines.append('')
        lines.extend(self.edges)
        lines.append('}')
        return '\n'.join(lines)

def format_node(renderer: DotRenderer, node_id: str, label: str, node_type: str):
    """
    Applies styling based on node type:
    - root: solid rounded box
    - expandable: rounded dashed box
    - builtin-like: rounded dotted gray box
    - unresolved: rounded dashed gray box
    """
    if node_type == "root":
        renderer.add_node(node_id, label=label, style="rounded", class_attr="root function")
    elif node_type == "expandable":
        renderer.add_node(node_id, label=label, style="rounded,dashed", class_attr="expandable function")
    elif node_type == "builtin-like":
        renderer.add_node(node_id, label=label, style="rounded,dotted", class_attr="builtin function", color="gray")
    elif node_type == "unresolved":
        renderer.add_node(node_id, label=label, style="rounded,dashed", class_attr="unresolved function", color="gray")
    else:
        renderer.add_node(node_id, label=label, style="rounded")
