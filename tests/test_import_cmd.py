"""Tests for stash import command."""

from __future__ import annotations

import json


def _init_vault(runner, cli_app, vault_dir) -> None:
    result = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "init", "--name", "test", "--force"],
    )
    assert result.exit_code == 0


def _seed_entry(runner, cli_app, vault_dir) -> None:
    result = runner.invoke(
        cli_app,
        [
            "--config-dir",
            str(vault_dir),
            "entry",
            "add",
            "Deploy",
            "kubectl apply -f deploy.yaml",
            "--force",
        ],
    )
    assert result.exit_code == 0


def test_import_skips_duplicates(runner, cli_app, vault_dir, tmp_path) -> None:
    """Import skips entries similar to existing vault entries."""
    _init_vault(runner, cli_app, vault_dir)
    _seed_entry(runner, cli_app, vault_dir)

    import_file = tmp_path / "entries.json"
    import_file.write_text(
        json.dumps(
            [
                {
                    "title": "Deploy again",
                    "content": "kubectl apply -f deploy.yaml",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli_app,
        [
            "--config-dir",
            str(vault_dir),
            "--json",
            "import",
            "--from-file",
            str(import_file),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["imported"] == 0
    assert payload["skipped_duplicates"] == 1
    assert len(payload["duplicates"]) == 1

    listed = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "--json", "entry", "list"],
    )
    assert len(json.loads(listed.stdout)) == 1


def test_import_ignore_duplicates(runner, cli_app, vault_dir, tmp_path) -> None:
    """Import imports duplicates when --ignore-duplicates is set."""
    _init_vault(runner, cli_app, vault_dir)
    _seed_entry(runner, cli_app, vault_dir)

    import_file = tmp_path / "entries.json"
    import_file.write_text(
        json.dumps(
            [
                {
                    "title": "Deploy again",
                    "content": "kubectl apply -f deploy.yaml",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli_app,
        [
            "--config-dir",
            str(vault_dir),
            "--json",
            "import",
            "--from-file",
            str(import_file),
            "--ignore-duplicates",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["imported"] == 1
    assert payload["skipped_duplicates"] == 0

    listed = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "--json", "entry", "list"],
    )
    assert len(json.loads(listed.stdout)) == 2


def test_import_dry_run_reports_duplicates(runner, cli_app, vault_dir, tmp_path) -> None:
    """Dry run reports duplicates without writing."""
    _init_vault(runner, cli_app, vault_dir)
    _seed_entry(runner, cli_app, vault_dir)

    import_file = tmp_path / "entries.json"
    import_file.write_text(
        json.dumps(
            [
                {
                    "title": "Deploy again",
                    "content": "kubectl apply -f deploy.yaml",
                }
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli_app,
        [
            "--config-dir",
            str(vault_dir),
            "--json",
            "import",
            "--from-file",
            str(import_file),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert payload["imported"] == 0
    assert payload["skipped_duplicates"] == 1

    listed = runner.invoke(
        cli_app,
        ["--config-dir", str(vault_dir), "--json", "entry", "list"],
    )
    assert len(json.loads(listed.stdout)) == 1


def test_import_skips_intra_batch_duplicates(runner, cli_app, vault_dir, tmp_path) -> None:
    """Import skips duplicate rows within the same file."""
    _init_vault(runner, cli_app, vault_dir)

    import_file = tmp_path / "entries.json"
    import_file.write_text(
        json.dumps(
            [
                {
                    "title": "Deploy",
                    "content": "kubectl apply -f deploy.yaml",
                },
                {
                    "title": "Deploy copy",
                    "content": "kubectl apply -f deploy.yaml",
                },
            ]
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli_app,
        [
            "--config-dir",
            str(vault_dir),
            "--json",
            "import",
            "--from-file",
            str(import_file),
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["imported"] == 1
    assert payload["skipped_duplicates"] == 1
