import sys
from pathlib import Path

# Add this directory to sys.path so _path_bootstrap and peer modules are importable
# regardless of where pytest is invoked from.
sys.path.insert(0, str(Path(__file__).parent))
