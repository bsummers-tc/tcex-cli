"""Tests for the template_files force-overwrite + --no-prompt update feature.

Covers:
* TemplateCli._collect_template_file_keys — union of template_files across the
  resolved parent chain (real fixture data).
* Planner.build(force_keys=...) — would-be prompt_user entries whose key is in
  force_keys are routed to auto_update; others keep prompt-on-modify behavior.
* Planner.apply(no_prompt=True) — prompt_user files are left untouched on disk
  and returned in the preserved list (prompt_fn is never called); force=True
  still overwrites and returns an empty preserved list.
* End-to-end TemplateCli.update(..., no_prompt=True) over the fixture cache.
* Regression: default update still prompts for a modified non-template file.
"""

# standard library
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

# first-party
from tcex_cli.cli.template.planner import Hasher, ManifestStore, Plan, Planner, SafeFileOps

# ==================================================================
# Helpers
# ==================================================================


def _sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def _write_manifest(path: Path, meta: dict) -> None:
    """Write a manifest.json to path."""
    path.write_text(json.dumps(meta, indent=2))


def _make_planner() -> Planner:
    """Return a Planner wired with the real (stateless) collaborators."""
    return Planner(ManifestStore(), Hasher(), SafeFileOps())


class RecordingPrompt:
    """A prompt_fn stand-in that records calls and raises if invoked.

    Used to prove no_prompt never prompts: any call fails the test loudly.
    """

    def __init__(self) -> None:
        """Initialize the call recorder."""
        self.calls: list[str] = []

    def __call__(self, msg: str) -> str:
        """Record the prompt and fail — should never be reached under no_prompt."""
        self.calls.append(msg)
        ex_msg = f'prompt_fn was called unexpectedly: {msg!r}'
        raise AssertionError(ex_msg)


# ==================================================================
# _collect_template_file_keys
# ==================================================================
class TestCollectTemplateFileKeys:
    """Union of template_files across the resolved parent chain."""

    def test_playbook_basic_union(self, template_cli):
        """playbook/basic + parent _app_common template_files union (the seven files).

        ``_app_common`` lists ``gitignore`` in its ``template_files`` (renamed to the
        on-disk ``.gitignore`` key), so the union is the leaf-owned files plus the four
        parent-owned files including ``.gitignore``.
        """
        cache_dir = template_cli._cache_dir('v2')
        keys = template_cli._collect_template_file_keys(cache_dir, 'basic', 'playbook')

        assert keys == {
            'playbook_app.py',
            'run.py',
            'run_local.py',
            '.coveragerc',
            '.pre-commit-config.yaml',
            'pyproject.toml',
            '.gitignore',
        }

    def test_includes_parent_keys(self, template_cli):
        """The parent (_app_common) keys are present in the union, not just the leaf's."""
        cache_dir = template_cli._cache_dir('v2')
        keys = template_cli._collect_template_file_keys(cache_dir, 'basic', 'playbook')

        # leaf-owned
        assert 'playbook_app.py' in keys
        # parent-owned
        assert 'pyproject.toml' in keys
        # parent-owned, renamed gitignore -> .gitignore (now template-owned)
        assert '.gitignore' in keys


# ==================================================================
# Planner.build(force_keys=...)
# ==================================================================
class TestPlannerBuildForceKeys:
    """force_keys routes would-be prompt_user entries to auto_update."""

    @staticmethod
    def _setup_diverged(tmp_path: Path) -> tuple[Path, Path]:
        """Create a template dir + project dir where a tracked file diverged.

        The template file content, the local manifest's recorded sha256, and the
        on-disk local content are all distinct, so the planner's hash comparison
        falls through to the "user modified" (prompt_user) branch.
        """
        template_dir = tmp_path / 'template'
        project_dir = tmp_path / 'project'
        template_dir.mkdir()
        project_dir.mkdir()

        # template ships new content for owned.py
        new_content = b'# template version\n'
        (template_dir / 'owned.py').write_bytes(new_content)
        template_meta = {
            'owned.py': {
                'last_commit': 'new_commit',
                'sha256': _sha256_bytes(new_content),
                'template_path': 'owned.py',
            }
        }
        _write_manifest(template_dir / 'manifest.json', template_meta)

        # local project last synced an older version (recorded sha differs)
        old_content = b'# original template version\n'
        local_meta = {
            'owned.py': {
                'last_commit': 'old_commit',
                'sha256': _sha256_bytes(old_content),
                'template_path': 'owned.py',
            }
        }
        _write_manifest(project_dir / 'manifest.json', local_meta)

        # but the user edited it to something else entirely → diverged
        (project_dir / 'owned.py').write_bytes(b'# user edits\n')

        return template_dir, project_dir

    def test_diverged_file_in_force_keys_goes_to_auto_update(self, tmp_path):
        """A modified, diverged file routes to auto_update when its key is forced."""
        template_dir, project_dir = self._setup_diverged(tmp_path)
        planner = _make_planner()

        plan = planner.build(template_dir, project_dir, force_keys={'owned.py'})

        assert ('owned.py', 'owned.py') in plan.auto_update
        assert ('owned.py', 'owned.py') not in plan.prompt_user

    def test_diverged_file_not_in_force_keys_stays_prompt_user(self, tmp_path):
        """The same diverged file stays in prompt_user when not forced."""
        template_dir, project_dir = self._setup_diverged(tmp_path)
        planner = _make_planner()

        plan = planner.build(template_dir, project_dir, force_keys=set())

        assert ('owned.py', 'owned.py') in plan.prompt_user
        assert ('owned.py', 'owned.py') not in plan.auto_update

    def test_new_file_on_disk_in_force_keys_goes_to_auto_update(self, tmp_path):
        """New template file already on disk: forced → auto_update, not prompt_user."""
        template_dir = tmp_path / 'template'
        project_dir = tmp_path / 'project'
        template_dir.mkdir()
        project_dir.mkdir()

        content = b'# new template file\n'
        (template_dir / 'fresh.py').write_bytes(content)
        _write_manifest(
            template_dir / 'manifest.json',
            {
                'fresh.py': {
                    'last_commit': 'c1',
                    'sha256': _sha256_bytes(content),
                    'template_path': 'fresh.py',
                }
            },
        )
        # local manifest has no entry for fresh.py (new), but file exists on disk
        _write_manifest(project_dir / 'manifest.json', {})
        (project_dir / 'fresh.py').write_bytes(b'# pre-existing local file\n')

        planner = _make_planner()

        forced = planner.build(template_dir, project_dir, force_keys={'fresh.py'})
        assert ('fresh.py', 'fresh.py') in forced.auto_update
        assert ('fresh.py', 'fresh.py') not in forced.prompt_user

        unforced = planner.build(template_dir, project_dir, force_keys=set())
        assert ('fresh.py', 'fresh.py') in unforced.prompt_user
        assert ('fresh.py', 'fresh.py') not in unforced.auto_update


# ==================================================================
# Planner.build — template-owned reconciliation ignores last_commit match
# ==================================================================
class TestPlannerBuildForceKeysSameCommit:
    """Regression: a force_keys file is reconciled even when last_commit matches.

    The closed gap: a locally-modified template-owned file whose local manifest
    last_commit STILL MATCHES the template was previously short-circuited to skip
    (never restored). The force_keys reconciliation must run BEFORE the
    last_commit short-circuit.
    """

    @staticmethod
    def _setup_same_commit(tmp_path: Path, *, local_content: bytes) -> tuple[Path, Path, bytes]:
        """Template + project where last_commit matches but on-disk content may differ.

        The local manifest's ``last_commit`` is identical to the template's, so the
        ``last_commit ==`` short-circuit would skip the file if it ran first. ``sha256``
        is also recorded as the template hash (a clean prior sync). The on-disk content
        is driven by ``local_content`` so the caller can exercise both the diverged and
        identical cases.
        """
        template_dir = tmp_path / 'template'
        project_dir = tmp_path / 'project'
        template_dir.mkdir()
        project_dir.mkdir()

        template_bytes = b'# template version\n'
        (template_dir / 'owned.py').write_bytes(template_bytes)

        shared_commit = 'same_commit'
        meta = {
            'owned.py': {
                'last_commit': shared_commit,
                'sha256': _sha256_bytes(template_bytes),
                'template_path': 'owned.py',
            }
        }
        _write_manifest(template_dir / 'manifest.json', meta)
        # local manifest records the SAME last_commit (clean prior sync)
        _write_manifest(project_dir / 'manifest.json', meta)

        # on-disk content per the caller's scenario
        (project_dir / 'owned.py').write_bytes(local_content)

        return template_dir, project_dir, template_bytes

    def test_modified_force_key_same_commit_goes_to_auto_update(self, tmp_path):
        """Modified template-owned file at matching last_commit → auto_update (restored)."""
        template_dir, project_dir, _template_bytes = self._setup_same_commit(
            tmp_path, local_content=b'# user edits\n'
        )
        planner = _make_planner()

        plan = planner.build(template_dir, project_dir, force_keys={'owned.py'})

        assert ('owned.py', 'owned.py') in plan.auto_update
        assert ('owned.py', 'owned.py') not in plan.skip
        assert ('owned.py', 'owned.py') not in plan.prompt_user

    def test_deleted_force_key_same_commit_goes_to_auto_update(self, tmp_path):
        """Missing template-owned file at matching last_commit → auto_update (restored)."""
        template_dir, project_dir, _template_bytes = self._setup_same_commit(
            tmp_path, local_content=b'placeholder\n'
        )
        (project_dir / 'owned.py').unlink()
        planner = _make_planner()

        plan = planner.build(template_dir, project_dir, force_keys={'owned.py'})

        assert ('owned.py', 'owned.py') in plan.auto_update
        assert ('owned.py', 'owned.py') not in plan.skip

    def test_identical_force_key_same_commit_skips(self, tmp_path):
        """Template-owned file already matching the template hash → skip (no rewrite)."""
        template_dir, project_dir, template_bytes = self._setup_same_commit(
            tmp_path, local_content=b'# template version\n'
        )
        # sanity: on-disk content matches the template byte-for-byte
        assert (project_dir / 'owned.py').read_bytes() == template_bytes
        planner = _make_planner()

        plan = planner.build(template_dir, project_dir, force_keys={'owned.py'})

        assert ('owned.py', 'owned.py') in plan.skip
        assert ('owned.py', 'owned.py') not in plan.auto_update

    def test_modified_non_force_key_same_commit_skips(self, tmp_path):
        """The same modified file, NOT force-owned, still skips at matching last_commit."""
        template_dir, project_dir, _template_bytes = self._setup_same_commit(
            tmp_path, local_content=b'# user edits\n'
        )
        planner = _make_planner()

        plan = planner.build(template_dir, project_dir, force_keys=set())

        # non-template file at matching last_commit short-circuits to skip
        assert ('owned.py', 'owned.py') in plan.skip
        assert ('owned.py', 'owned.py') not in plan.auto_update


# ==================================================================
# End-to-end — modified template-owned file restored at matching last_commit
# ==================================================================
class TestUpdateRestoresTemplateOwnedSameCommit:
    """End-to-end: a modified template-owned file is restored without a manifest bump."""

    @staticmethod
    def _init(template_cli, project_dir, monkeypatch) -> None:
        monkeypatch.chdir(project_dir)
        with patch.object(template_cli, 'ensure_cache', return_value=template_cli._cache_dir('v2')):
            template_cli.update('v2', 'basic', 'playbook', force=True)

    def test_modified_run_py_restored_with_unchanged_manifest(
        self, template_cli, project_dir, monkeypatch
    ):
        """run.py (template-owned) is overwritten back to the template with no prompt.

        The local manifest is left untouched (last_commit still matches the template),
        proving the last_commit match does not preempt template-owned reconciliation.
        """
        self._init(template_cli, project_dir, monkeypatch)

        cache_dir = template_cli._cache_dir('v2')
        template_run = (cache_dir / 'playbook' / 'basic' / 'run.py').read_text()

        # modify a template-owned file WITHOUT touching the manifest
        (project_dir / 'run.py').write_text('# user run.py edits')

        with (
            patch.object(template_cli, 'ensure_cache', return_value=template_cli._cache_dir('v2')),
            patch('tcex_cli.render.render.Render.prompt.ask') as mock_prompt,
        ):
            template_cli.update('v2', 'basic', 'playbook')

        assert (project_dir / 'run.py').read_text() == template_run
        prompted_files = [call.args[0] for call in mock_prompt.call_args_list]
        assert not any('run.py' in f for f in prompted_files)

    def test_unmodified_run_py_skipped_with_unchanged_manifest(
        self, template_cli, project_dir, monkeypatch
    ):
        """An untouched template-owned file already matching the template is skipped."""
        self._init(template_cli, project_dir, monkeypatch)

        cache_dir = template_cli._cache_dir('v2')
        template_run = (cache_dir / 'playbook' / 'basic' / 'run.py').read_text()

        with (
            patch.object(template_cli, 'ensure_cache', return_value=template_cli._cache_dir('v2')),
            patch('tcex_cli.render.render.Render.prompt.ask') as mock_prompt,
        ):
            template_cli.update('v2', 'basic', 'playbook')

        # unchanged on disk (already matched → skipped, no needless rewrite)
        assert (project_dir / 'run.py').read_text() == template_run
        mock_prompt.assert_not_called()


# ==================================================================
# Planner.apply(no_prompt=...)
# ==================================================================
class TestPlannerApplyNoPrompt:
    """no_prompt preserves prompt_user files; force still overwrites."""

    @staticmethod
    def _setup_apply(tmp_path: Path) -> tuple[Path, Path, bytes]:
        """Create a template + project where prompt.py is a modified prompt_user file."""
        template_dir = tmp_path / 'template'
        project_dir = tmp_path / 'project'
        template_dir.mkdir()
        project_dir.mkdir()

        template_bytes = b'# template content\n'
        (template_dir / 'prompt.py').write_bytes(template_bytes)

        local_bytes = b'# user content\n'
        (project_dir / 'prompt.py').write_bytes(local_bytes)

        return template_dir, project_dir, template_bytes

    def test_no_prompt_preserves_and_records_without_prompting(self, tmp_path):
        """no_prompt: file untouched on disk, returned preserved, prompt_fn never called."""
        template_dir, project_dir, _template_bytes = self._setup_apply(tmp_path)
        local_bytes = (project_dir / 'prompt.py').read_bytes()

        plan = Plan(prompt_user=[('prompt.py', 'prompt.py')])
        planner = _make_planner()
        recorder = RecordingPrompt()

        preserved = planner.apply(
            plan,
            template_root=template_dir,
            project_root=project_dir,
            no_prompt=True,
            prompt_fn=recorder,
        )

        # file left byte-for-byte unchanged
        assert (project_dir / 'prompt.py').read_bytes() == local_bytes
        # returned in the preserved list
        assert ('prompt.py', 'prompt.py') in preserved
        # prompt_fn never invoked
        assert recorder.calls == []

    def test_force_overwrites_and_returns_empty_preserved(self, tmp_path):
        """force=True: prompt_user file is overwritten, preserved list is empty."""
        template_dir, project_dir, template_bytes = self._setup_apply(tmp_path)

        plan = Plan(prompt_user=[('prompt.py', 'prompt.py')])
        planner = _make_planner()
        recorder = RecordingPrompt()

        preserved = planner.apply(
            plan,
            template_root=template_dir,
            project_root=project_dir,
            force=True,
            prompt_fn=recorder,
        )

        # overwritten from template
        assert (project_dir / 'prompt.py').read_bytes() == template_bytes
        # no preserved entries on the force path
        assert preserved == []
        # prompt_fn never invoked under force
        assert recorder.calls == []


# ==================================================================
# End-to-end update --no-prompt over the fixture cache
# ==================================================================
class TestUpdateNoPromptEndToEnd:
    """Drive TemplateCli.update(no_prompt=True) over the real fixture cache."""

    @staticmethod
    def _init(template_cli, project_dir, monkeypatch) -> None:
        monkeypatch.chdir(project_dir)
        with patch.object(template_cli, 'ensure_cache', return_value=template_cli._cache_dir('v2')):
            template_cli.update('v2', 'basic', 'playbook', force=True)

    @staticmethod
    def _simulate_change(project_dir: Path, filename: str) -> None:
        manifest = json.loads((project_dir / 'manifest.json').read_text())
        manifest[filename]['last_commit'] = 'old_commit_before_update'
        (project_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2))

    def test_template_owned_file_overwritten_and_non_template_preserved(
        self, template_cli, project_dir, monkeypatch
    ):
        """no_prompt: run.py (template-owned) overwritten; app.py (non-template) preserved.

        The whole run completes with zero prompts.
        """
        self._init(template_cli, project_dir, monkeypatch)

        cache_dir = template_cli._cache_dir('v2')
        template_run = (cache_dir / 'playbook' / 'basic' / 'run.py').read_text()

        # user modifies both a template-owned file and a non-template file
        (project_dir / 'run.py').write_text('# user run.py edits')
        (project_dir / 'app.py').write_text('# user app.py edits')

        # simulate the template moving on for both
        self._simulate_change(project_dir, 'run.py')
        self._simulate_change(project_dir, 'app.py')

        with (
            patch.object(template_cli, 'ensure_cache', return_value=template_cli._cache_dir('v2')),
            patch('tcex_cli.render.render.Render.prompt.ask') as mock_prompt,
        ):
            template_cli.update('v2', 'basic', 'playbook', no_prompt=True)

        # template-owned run.py overwritten back to the template content
        assert (project_dir / 'run.py').read_text() == template_run
        # non-template app.py preserved byte-for-byte
        assert (project_dir / 'app.py').read_text() == '# user app.py edits'
        # zero prompts during the entire run
        mock_prompt.assert_not_called()

    def test_no_prompt_renders_preserved_report(self, template_cli, project_dir, monkeypatch):
        """no_prompt with a preserved file renders the 'Preserved - Review Manually' report."""
        self._init(template_cli, project_dir, monkeypatch)

        (project_dir / 'app.py').write_text('# user app.py edits')
        self._simulate_change(project_dir, 'app.py')

        with (
            patch.object(template_cli, 'ensure_cache', return_value=template_cli._cache_dir('v2')),
            patch('tcex_cli.render.render.Render.table.key_value') as mock_table,
        ):
            template_cli.update('v2', 'basic', 'playbook', no_prompt=True)

        titles = [call.args[0] for call in mock_table.call_args_list]
        assert 'Preserved - Review Manually' in titles


# ==================================================================
# Regression — default update still prompts for non-template files
# ==================================================================
class TestDefaultUpdateStillPrompts:
    """Without --no-prompt, a modified non-template file still prompts y/N."""

    @staticmethod
    def _init(template_cli, project_dir, monkeypatch) -> None:
        monkeypatch.chdir(project_dir)
        with patch.object(template_cli, 'ensure_cache', return_value=template_cli._cache_dir('v2')):
            template_cli.update('v2', 'basic', 'playbook', force=True)

    @staticmethod
    def _simulate_change(project_dir: Path, filename: str) -> None:
        manifest = json.loads((project_dir / 'manifest.json').read_text())
        manifest[filename]['last_commit'] = 'old_commit_before_update'
        (project_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2))

    def test_modified_non_template_file_prompts(self, template_cli, project_dir, monkeypatch):
        """Default update prompts for app.py (non-template) and preserves it on 'N'."""
        self._init(template_cli, project_dir, monkeypatch)

        (project_dir / 'app.py').write_text('# user app.py edits')
        self._simulate_change(project_dir, 'app.py')

        with (
            patch.object(template_cli, 'ensure_cache', return_value=template_cli._cache_dir('v2')),
            patch('tcex_cli.render.render.Render.prompt.ask', return_value='N') as mock_prompt,
        ):
            template_cli.update('v2', 'basic', 'playbook')

        # app.py was prompted for (it is not template-owned)
        prompted_files = [call.args[0] for call in mock_prompt.call_args_list]
        assert any('app.py' in f for f in prompted_files)
        # answered 'N' → preserved
        assert (project_dir / 'app.py').read_text() == '# user app.py edits'
