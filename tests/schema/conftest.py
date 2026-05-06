"""pytest 配置:把 tests/schema/ 加到 sys.path,供 test_*.py 直接 import validate_*."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
