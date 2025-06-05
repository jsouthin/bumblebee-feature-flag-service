import subprocess
import os
import sys
import tempfile
import shutil
import pytest

CLI_PATH = os.path.join(os.path.dirname(__file__), '../src/feature_flags_cli.py')
DB_PATH = 'test_cli_feature_flags.db'

@pytest.fixture(autouse=True)
def cleanup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def run_cli(args):
    return subprocess.run(
        [sys.executable, CLI_PATH, "--db-path", DB_PATH] + args,
        capture_output=True,
        text=True,
        check=False
    )

def test_add_and_list_feature():
    result = run_cli(["add-feature", "cli_test_feature"])
    assert result.returncode == 0
    result = run_cli(["list-all-features"])
    assert "cli_test_feature" in result.stdout

def test_add_and_list_customer():
    result = run_cli(["add-customer", "1234"])
    assert result.returncode == 0
    result = run_cli(["list-all-customers"])
    assert "1234" in result.stdout

def test_rename_feature():
    run_cli(["add-feature", "old_cli_feature"])
    result = run_cli(["rename-feature", "old_cli_feature", "new_cli_feature"])
    assert result.returncode == 0
    result = run_cli(["list-all-features"])
    assert "new_cli_feature" in result.stdout
    assert "old_cli_feature" not in result.stdout

def test_error_on_conflicting_flags():
    run_cli(["add-feature", "err_feature"])
    result = run_cli(["set-flag", "err_feature", "--customer-id", "1", "--enabled", "--disabled"])
    assert result.returncode != 0 or "Specify --enabled or --disabled" in result.stderr 