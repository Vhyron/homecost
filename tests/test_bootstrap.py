import subprocess
import sys


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "homecost.cli", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "usage:" in result.stdout.lower()
