from typer.testing import CliRunner
from similitude.cli.app import app

runner = CliRunner()

def test_cli_help_runs():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage" in result.stdout
