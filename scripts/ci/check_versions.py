# /// script
# requires-python = ">=3.11"
# dependencies = ["packaging>=24"]
# ///

import json
import subprocess
import sys
import tomllib
from pathlib import Path

from packaging.version import InvalidVersion, Version

PROJECTS = json.loads((Path(__file__).parent / "projects.json").read_text())


def matches(path: str, watched: str) -> bool:
    return path == watched or path.startswith(watched.rstrip("/") + "/")


def raw_version(text: str) -> str:
    return tomllib.loads(text)["project"]["version"]


def current_raw(manifest: str) -> str:
    return raw_version(Path(manifest).read_text())


def resolves(rev: str) -> bool:
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"],
        capture_output=True,
    ).returncode == 0


def raw_at(rev: str, manifest: str) -> str | None:
    if not resolves(rev):
        print(
            f"::error::cannot resolve revision \"{rev}\". "
            f"The version gate needs it; check that actions/checkout ran with fetch-depth: 0."
        )
        raise SystemExit(1)
    result = subprocess.run(
        ["git", "show", f"{rev}:{manifest}"],
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return raw_version(result.stdout.decode())


def dependents_of(target: str) -> set[str]:
    found = set()
    pending = [target]
    while pending:
        current = pending.pop()
        for name, policy in PROJECTS.items():
            if current in policy.get("depends_on", []) and name not in found:
                found.add(name)
                pending.append(name)
    return found


base_sha = sys.argv[1]
base_ref = sys.argv[2] if len(sys.argv) > 2 else None

for name, policy in PROJECTS.items():
    for watched in (*policy["watch"], policy["manifest"]):
        if not Path(watched).exists():
            print(
                f"::error file=scripts/ci/projects.json::"
                f"{name}: configured path \"{watched}\" does not exist. "
                f"Update the \"{name}\" entry in scripts/ci/projects.json."
            )
            raise SystemExit(1)
    for dependency in policy.get("depends_on", []):
        if dependency not in PROJECTS:
            print(
                f"::error file=scripts/ci/projects.json::"
                f"{name}: depends_on names unknown project \"{dependency}\"."
            )
            raise SystemExit(1)

diff_base = f"origin/{base_ref}" if base_ref else base_sha

changed_files = subprocess.check_output(
    ["git", "diff", "--name-only", f"{diff_base}...HEAD"],
    text=True,
).splitlines()

directly_changed = {
    name
    for name, policy in PROJECTS.items()
    if any(matches(path, watched) for path in changed_files for watched in policy["watch"])
}

affected = set(directly_changed)
for name in directly_changed:
    affected |= dependents_of(name)

failed = False

for name, policy in PROJECTS.items():
    manifest = policy["manifest"]

    if name not in affected:
        print(f"{name}: unchanged")
        continue

    if name in directly_changed:
        reason = "sources changed"
    else:
        triggers = sorted(d for d in directly_changed if name in dependents_of(d))
        reason = "depends on " + ", ".join(triggers)

    raw_new = current_raw(manifest)

    try:
        new = Version(raw_new)
    except InvalidVersion:
        print(f"::error file={manifest}::{name}: version \"{raw_new}\" is not a valid PEP 440 version.")
        failed = True
        continue

    if raw_new != str(new):
        print(
            f"::error file={manifest}::"
            f"{name}: version \"{raw_new}\" is not in canonical PEP 440 form. "
            f"Write it as \"{new}\" so the git tag and the published artifact agree."
        )
        failed = True
        continue

    floors = []
    raw_base = raw_at(base_sha, manifest)
    if raw_base is not None:
        floors.append((Version(raw_base), f"base commit {base_sha[:12]}"))
    if base_ref:
        raw_tip = raw_at(f"origin/{base_ref}", manifest)
        if raw_tip is not None:
            floors.append((Version(raw_tip), f"tip of {base_ref}"))

    if not floors:
        print(f"{name}: new project at {new}")
        continue

    old, where = max(floors, key=lambda pair: pair[0])

    if new <= old:
        print(
            f"::error file={manifest}::"
            f"{name} {reason} but its version ({new}) is not above {old} on {where}. "
            f"Set [project].version above {old} in {manifest}."
        )
        failed = True
    else:
        print(f"{name}: {old} -> {new} ({reason})")

raise SystemExit(1 if failed else 0)
