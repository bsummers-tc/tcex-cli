"""Template update planner and file operations.

Self-contained helper classes for computing file-level diffs between
a template and a user's project, and applying the resulting plan.
No dependency on CliABC, HTTP sessions, or rendering — pure logic.
"""

# standard library
import contextlib
import hashlib
import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict

# third-party
from pydantic import BaseModel, Field

# ==================================================================
# Shared Types
# ==================================================================


class FileMeta(TypedDict):
    """Metadata for a single file in the manifest."""

    last_commit: str
    sha256: str
    template_path: str


Meta = dict[str, FileMeta]  # key: POSIX-style project-relative path


# ==================================================================
# Plan Model
# ==================================================================


class Plan(BaseModel):
    """Update plan for template files.

    Built by Planner.build(), consumed by Planner.apply().
    Each list contains (project_relative_key, template_path) tuples.
    """

    skip: list[tuple] = Field(default=[], description='Files that are unchanged.')
    auto_update: list[tuple] = Field(
        default=[], description='Files that will be updated automatically.'
    )
    prompt_user: list[tuple] = Field(
        default=[], description='Files that require user confirmation.'
    )
    template_new: list[tuple] = Field(default=[], description='New files in the template.')
    template_removed: list[tuple] = Field(
        default=[], description='Files removed from the template.'
    )

    @property
    def summary(self) -> dict[str, str | None]:
        """Return a summary dict suitable for Render.table.key_value."""
        return {
            'Skip': str(len(self.skip)),
            'Auto Update': str(len(self.auto_update)),
            'Prompt User': str(len(self.prompt_user)),
            'Template New': str(len(self.template_new)),
            'Template Removed': str(len(self.template_removed)),
        }

    @property
    def details(self) -> dict:
        """Return detailed plan information as a dictionary."""
        return {
            'skip': self.skip,
            'auto_update': self.auto_update,
            'prompt_user': self.prompt_user,
            'template_new': self.template_new,
            'template_removed': self.template_removed,
        }


# ==================================================================
# Hashing
# ==================================================================


class Hasher:
    """Stable SHA-256 hashing for files."""

    @staticmethod
    def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str | None:
        """Return the SHA-256 hex digest of a file, or None if missing."""
        if not path.exists():
            return None
        h = hashlib.sha256()
        with path.open('rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()


# ==================================================================
# Manifest I/O
# ==================================================================


class ManifestStore:
    """Load manifest.json files and compute key sets."""

    @staticmethod
    def load_json(path: Path) -> Meta:
        """Load and return a manifest dict from disk (empty dict if missing)."""
        if not path.exists():
            return {}
        with path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            ex_msg = f'Expected object at top-level in {path}'
            raise TypeError(ex_msg)
        return data  # type: ignore[return-value]

    @staticmethod
    def collect_keys(template_meta: Meta, main_meta: Meta) -> tuple[list[str], list[str]]:
        """Return (keys_in_template, removed_in_template).

        ``removed_in_template`` = keys present in the local manifest
        but absent from the template manifest (i.e., the template
        stopped shipping those files).
        """
        template_keys = set(template_meta.keys())
        main_keys = set(main_meta.keys())
        return sorted(template_keys), sorted(main_keys - template_keys)


# ==================================================================
# Safe File Operations
# ==================================================================


class SafeFileOps:
    """Filesystem mutations with preserved file modes."""

    def copy_from_template(self, template_root: Path, key: str, dest: Path) -> None:
        """Copy a template file to the project, preserving mode on overwrite."""
        src = template_root / key
        if not src.exists():
            ex_msg = f'Template file does not exist: {src}'
            raise FileNotFoundError(ex_msg)
        self.ensure_parent(dest)

        data = src.read_bytes()
        if dest.exists():
            mode = dest.stat().st_mode
            dest.write_bytes(data)
            dest.chmod(mode)
        else:
            dest.write_bytes(data)
            with contextlib.suppress(Exception):
                shutil.copymode(src, dest)

    @staticmethod
    def ensure_parent(path: Path) -> None:
        """Ensure parent directory exists."""
        path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def remove_file(path: Path) -> None:
        """Remove file if it exists."""
        if path.exists():
            path.unlink()

    @staticmethod
    def copy_tree_or_file(src: Path, target: Path) -> None:
        """Copy a file or directory tree from src to target."""
        if src.is_dir():
            shutil.copytree(src, target)
        else:
            shutil.copy2(src, target)


# ==================================================================
# Planner
# ==================================================================


class Planner:
    """Compute and apply file-level update plans.

    The Planner uses a two-manifest comparison strategy:
    - "template manifest": what the remote template currently provides
    - "local manifest": what was last synced to the user's project

    By comparing ``last_commit`` values and SHA-256 hashes, the Planner
    categorizes every file into: skip, auto_update, prompt_user,
    template_new, or template_removed.
    """

    def __init__(self, manifest: ManifestStore, hasher: Hasher, file_ops: SafeFileOps):
        """Initialize with dependencies."""
        self.manifest = manifest
        self.hasher = hasher
        self.file_ops = file_ops

    def build(
        self,
        temp_dest: Path,
        dest: Path,
        file_name: str = 'manifest.json',
        force=False,
        force_keys: set[str] | None = None,
    ) -> Plan:
        """Build an update plan by comparing template and local manifests.

        Syncing logic:
        1. Load both the remote template manifest and the local project manifest.
        2. Determine which file keys exist in the template and which were removed.
        3. For each key still in the template:
           - If ``force`` is set, auto-update unconditionally.
           - If the key is absent from the local manifest, it is a new file.
             Auto-update when the file doesn't exist on disk yet; prompt the
             user if it already exists (to avoid silently overwriting local work).
           - If both manifests share the same ``last_commit``, the template
             hasn't changed this file since last sync — skip.
           - Otherwise, hash the local file and compare:
             * If the hash matches the new template or the file is missing, skip.
             * All other modified files require user confirmation.
        4. For each key removed from the template:
           - If the local file is gone or unchanged from last-known hash,
             auto-remove (safe cleanup).
           - If the user modified the file, prompt before removing.

        ``force_keys`` is the set of project-relative keys declared as
        template-owned (via each template.yaml ``template_files``). Any file
        whose key is in this set is reconciled against the template hash
        unconditionally — independent of ``last_commit`` / local-manifest state.
        The local file is hashed against the template's ``sha256``: if it differs
        (or the file is missing) it is routed to ``auto_update`` to restore/refresh
        it from the template; if it already matches it is skipped. This check runs
        before the ``last_commit`` short-circuit so a stale-but-matching manifest
        cannot preempt the reconciliation. Keys not in the set keep the default
        prompt-on-modify behavior.
        """
        template_meta = self.manifest.load_json(temp_dest / file_name)
        local_meta = self.manifest.load_json(dest / file_name)

        force_keys = force_keys or set()

        plan = Plan()

        keys_in_template, removed_in_template = self.manifest.collect_keys(
            template_meta, local_meta
        )

        # --- updates and additions ---
        for key in keys_in_template:
            template_info = template_meta[key]
            local_info = local_meta.get(key)
            value = (key, template_info['template_path'])

            project_path = dest / key

            if force is True:
                plan.auto_update.append(value)
                continue

            # new file being tracked in the template
            if local_info is None:
                plan.template_new.append(value)
                if project_path.exists() and key not in force_keys:
                    plan.prompt_user.append(value)
                else:
                    plan.auto_update.append(value)
                continue

            # template-owned files are always reconciled against the template
            # hash, independent of last_commit / local-manifest state — this
            # runs before the last_commit short-circuit so a stale-but-matching
            # manifest cannot preempt the reconciliation.
            if key in force_keys:
                current_hash = self.hasher.sha256_file(project_path)
                if current_hash == template_info['sha256']:
                    plan.skip.append(value)
                else:
                    # differs or missing — restore/refresh from template
                    plan.auto_update.append(value)
                continue

            # both sides have metadata and template hasn't changed this file
            if template_info['last_commit'] == local_info['last_commit']:
                plan.skip.append(value)
                continue

            # template changed — check if local file also diverged
            current_hash = self.hasher.sha256_file(project_path)
            if current_hash == template_info['sha256'] or current_hash is None:
                plan.skip.append(value)
            else:
                plan.prompt_user.append(value)

        # --- removals ---
        for key in removed_in_template:
            local_info = local_meta[key]
            value = (key, local_info['template_path'])
            plan.template_removed.append(value)

            current_hash = self.hasher.sha256_file(dest / key)

            if current_hash is None:
                plan.auto_update.append(value)  # already gone
            elif current_hash == local_info['sha256'] or key in force_keys:
                plan.auto_update.append(value)  # unchanged or template-owned — safe to remove
            else:
                plan.prompt_user.append(value)  # user modified — ask first

        return plan

    def apply(
        self,
        plan: Plan,
        *,
        template_root: Path,
        project_root: Path,
        force: bool = False,
        no_prompt: bool = False,
        prompt_fn: Callable[[str], str] = input,
    ) -> list[tuple]:
        """Apply the plan to the project directory.

        Auto-update files are copied/removed without prompting.
        Prompt-user files ask for confirmation via ``prompt_fn``
        (injected for testability — defaults to ``input()``).

        Behavior for the ``prompt_user`` set:
        - ``force`` → overwrite/remove without prompting.
        - ``no_prompt`` (and not ``force``) → leave the file untouched on disk
          (no prompt) and record it as preserved.
        - otherwise → prompt via ``prompt_fn``.

        Returns the list of preserved ``(local, template)`` tuples (the
        modified, non-template-owned files left untouched under ``no_prompt``);
        an empty list for the interactive/force paths.
        """
        auto_set = set(plan.auto_update)
        prompt_set = set(plan.prompt_user)
        removed_keys = {local for local, _template in plan.template_removed}
        preserved: list[tuple] = []

        # auto-update: copies and removals
        for local, template in auto_set:
            local_ = project_root / local
            if local in removed_keys:
                self.file_ops.remove_file(local_)
            else:
                self.file_ops.copy_from_template(template_root, template, local_)

        if prompt_set and force:
            # force: overwrite or remove without prompting
            for local, template in prompt_set:
                local_ = project_root / local
                if local in removed_keys:
                    self.file_ops.remove_file(local_)
                else:
                    self.file_ops.copy_from_template(template_root, template, local_)
        elif prompt_set and no_prompt:
            # non-interactive: never clobber — preserve and report
            preserved.extend(sorted(prompt_set))
        elif prompt_set:
            # interactive: ask before overwriting or removing
            for local, template in sorted(prompt_set):
                local_ = project_root / local
                if local in removed_keys:
                    response = prompt_fn(f"Remove modified file '{local}'?").strip().lower()
                    if response == 'y':
                        self.file_ops.remove_file(local_)
                else:
                    response = (
                        prompt_fn(f"Overwrite modified file '{local}' from template?")
                        .strip()
                        .lower()
                    )
                    if response == 'y':
                        self.file_ops.copy_from_template(template_root, template, local_)

        return preserved
