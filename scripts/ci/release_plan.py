# /// script
# requires-python = ">=3.11"
# dependencies = ["packaging>=24"]
# ///

import json
import os
import subprocess
import tomllib
from pathlib import Path

from packaging.version import InvalidVersion, Version

PROJECTS = json.loads((Path(__file__).parent / "projects.json").read_text())


def matches(path: str, watched: str) -> bool:
    return path == watched or path.startswith(watched.rstrip("/") + "/")


def raw_version(manifest: str) -> str:
    with Path(manifest).open("rb") as file:
        return tomllib.load(file)["project"]["version"]


def changed_since(rev: str, watched: list[str]) -> list[str]:
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", f"{rev}..HEAD"],
        text=True,
    ).splitlines()
    return [p for p in changed if any(matches(p, w) for w in watched)]


existing_tags = set(
    subprocess.check_output(["git", "tag", "--list"], text=True).split()
)

lines = []
rows = []
failed = False

for name, policy in PROJECTS.items():
    manifest = policy["manifest"]

    if not Path(manifest).exists():
        print(
            f"::error file=scripts/ci/projects.json::"
            f"{name}: configured manifest \"{manifest}\" does not exist. "
            f"Update the \"{name}\" entry in scripts/ci/projects.json."
        )
        raise SystemExit(1)

    raw = raw_version(manifest)

    try:
        parsed = Version(raw)
    except InvalidVersion:
        print(f"::error file={manifest}::{name}: version \"{raw}\" is not a valid PEP 440 version.")
        raise SystemExit(1)

    tag = f"{policy['tag_prefix']}{parsed}"
    release = tag not in existing_tags

    lines.append(f"{name}={str(release).lower()}")
    lines.append(f"{name}_tag={tag}")

    if release:
        print(f"::notice::{name} will be released as {tag}")
        rows.append(f"| {name} | `{parsed}` | `{tag}` | will release |")
        continue

    stale = changed_since(tag, policy["watch"])
    if stale:
        shown = ", ".join(stale[:5]) + (", ..." if len(stale) > 5 else "")
        print(
            f"::error file={manifest}::"
            f"{name}: {tag} is already tagged, but {len(stale)} watched file(s) changed since it "
            f"({shown}). "
            f"Those changes will never be published under an existing tag. "
            f"Bump [project].version in {manifest}."
        )
        rows.append(
            f"| {name} | `{parsed}` | `{tag}` | **stale — {len(stale)} file(s) changed since the tag** |"
        )
        failed = True
    else:
        print(f"{name}: {tag} already tagged, nothing to do")
        rows.append(f"| {name} | `{parsed}` | `{tag}` | already released |")

summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
if summary_path:
    with open(summary_path, "a") as file:
        file.write("### Release plan\n\n")
        file.write("| project | version | tag | decision |\n")
        file.write("| --- | --- | --- | --- |\n")
        file.write("\n".join(rows) + "\n")
        if failed:
            file.write(
                "\nA project has unreleased changes under an existing tag. "
                "Bump its `[project].version` and merge again.\n"
            )

output = os.environ.get("GITHUB_OUTPUT")
if output:
    with open(output, "a") as file:
        file.write("\n".join(lines) + "\n")
else:
    print("\n".join(lines))

raise SystemExit(1 if failed else 0)
