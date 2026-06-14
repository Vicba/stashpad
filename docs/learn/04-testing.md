# Testing

- **Docs:** [Testing](https://typer.tiangolo.com/tutorial/testing/)
- **Code:** `tests/test_cli.py`, `tests/conftest.py`

## CliRunner

```python
from typer.testing import CliRunner
from stash_cli.cli import app

runner = CliRunner()
result = runner.invoke(app, ["--config-dir", "/tmp/vault", "init", "--name", "t", "--force"])
assert result.exit_code == 0
```

## Isolated vault

The `vault_dir` fixture sets `STASH_DATA_DIR` to a temp directory so tests never touch your real vault:

```python
def test_something(runner, cli_app, vault_dir):
    runner.invoke(cli_app, ["--config-dir", str(vault_dir), "init", "--name", "test", "--force"])
```

## Testing patterns in this repo

| Test file | Covers |
|-----------|--------|
| `test_cli.py` | help, version, full lifecycle, aliases, tags |
| `test_storage.py` | storage layer unit tests |
| `test_api.py` | FastAPI TestClient |
| `test_config.py` | settings and env |

Run: `poetry run poe test`
