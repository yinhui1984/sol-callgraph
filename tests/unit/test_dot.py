from sol_callgraph.dot import escape_dot_id, DotRenderer, format_node

def test_escape_dot_id():
    assert escape_dot_id('normal') == '"normal"'
    assert escape_dot_id('with "quotes"') == '"with \\"quotes\\""'
    assert escape_dot_id('with \\backslash') == '"with \\\\backslash"'
    assert escape_dot_id('with\nnewline') == '"with\\nnewline"'
    assert escape_dot_id('complex "string" with \\ and \n') == '"complex \\"string\\" with \\\\ and \\n"'

def test_dot_renderer_basic():
    renderer = DotRenderer()
    renderer.add_node("A", label="Node A")
    renderer.add_node("B", label="Node B", style="dashed")
    renderer.add_edge("A", "B", label="calls")
    
    dot_output = renderer.render()
    assert 'digraph focused_call_graph {' in dot_output
    assert 'rankdir="LR";' in dot_output
    assert '  "A" [style="rounded", label="Node A"];' in dot_output
    assert '  "B" [style="dashed", label="Node B"];' in dot_output
    assert '  "A" -> "B" [label="calls"];' in dot_output

def test_format_node():
    renderer = DotRenderer()
    format_node(renderer, "root_fn", "_fallback()", "root")
    format_node(renderer, "ext_fn", "Lib.call()", "expandable")
    format_node(renderer, "builtin_fn", "abi.decode()", "builtin-like")
    format_node(renderer, "unresolved_fn", "unknown()", "unresolved")
    
    dot_output = renderer.render()
    assert '  "root_fn" [style="rounded", label="_fallback()", class="root function"];' in dot_output
    assert '  "ext_fn" [style="rounded,dashed", label="Lib.call()", class="expandable function"];' in dot_output
    assert '  "builtin_fn" [style="rounded,dotted", label="abi.decode()", class="builtin function", color="gray", fontcolor="gray"];' in dot_output
    assert '  "unresolved_fn" [style="rounded,dashed", label="unknown()", class="unresolved function", color="gray", fontcolor="gray"];' in dot_output
