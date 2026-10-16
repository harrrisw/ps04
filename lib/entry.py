"""Module launcher also supporting Windows embedded Python and isolated tests."""
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
module = sys.argv.pop(1)
runpy.run_module(module, run_name='__main__')
