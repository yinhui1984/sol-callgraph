import subprocess
import sys
import os
from typing import Optional

def run_dot(dot_content: str, output_format: str, output_path: Optional[str] = None) -> Optional[bytes]:
    """
    Runs Graphviz 'dot' to convert DOT content to SVG or PNG.
    If output_path is provided, writes to it.
    Otherwise returns the bytes of the output.
    """
    cmd = ["dot", f"-T{output_format}"]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False
        )
        stdout, stderr = process.communicate(input=dot_content.encode('utf-8'))
        
        if process.returncode != 0:
            print(f"error: Graphviz 'dot' failed with exit code {process.returncode}", file=sys.stderr)
            if stderr:
                print(stderr.decode('utf-8', errors='ignore'), file=sys.stderr)
            sys.exit(5)
            
        if output_path:
            try:
                with open(output_path, 'wb') as f:
                    f.write(stdout)
                return None
            except Exception as e:
                print(f"error: failed to write output file: {e}", file=sys.stderr)
                sys.exit(4)
        else:
            return stdout
            
    except FileNotFoundError:
        print("error: Graphviz 'dot' command not found. Please install Graphviz.", file=sys.stderr)
        sys.exit(5)
    except Exception as e:
        print(f"error: failed to execute Graphviz: {e}", file=sys.stderr)
        sys.exit(5)
