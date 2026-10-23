"""Exercise the installed command from outside its source directory."""
from pathlib import Path
import json
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COMMAND = 'sessionscope'
ARGS = ['examples/before.har', 'examples/after.har']
ARGS = [str(ROOT / item) if item.startswith('examples/') else item for item in ARGS]
with tempfile.TemporaryDirectory() as raw:
    destination = Path(raw) / 'report.json'
    subprocess.run([COMMAND, *ARGS, '-o', str(destination)], cwd=raw, check=True)
    result = json.loads(destination.read_text(encoding='utf-8'))
    assert result['tool'], 'tool metadata missing'
    subprocess.run([COMMAND, '--help'], cwd=raw, check=True, capture_output=True)
    print(COMMAND + ': installed command and JSON demo passed')
