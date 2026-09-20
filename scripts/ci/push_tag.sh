#!/usr/bin/env bash
set -euo pipefail

tag="$1"

summary() {
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
        printf '%s\n' "$1" >> "$GITHUB_STEP_SUMMARY"
    fi
}

if git rev-parse -q --verify "refs/tags/${tag}" >/dev/null; then
    echo "::notice::Tag ${tag} already exists locally; skipped tagging"
    exit 0
fi

if git ls-remote --exit-code --tags origin "refs/tags/${tag}" >/dev/null 2>&1; then
    echo "::notice::Tag ${tag} already exists on origin; skipped tagging"
    exit 0
fi

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git tag -a "${tag}" -m "${tag}"

if ! git push origin "refs/tags/${tag}"; then
    echo "::error::Could not push tag ${tag} to origin. The tag exists locally on the runner only; nothing was released."
    summary "### Tagging failed for \`${tag}\`"
    summary ""
    summary "\`git push origin refs/tags/${tag}\` failed. No tag reached origin and nothing was published."
    exit 1
fi

echo "::notice::Pushed tag ${tag} at ${GITHUB_SHA:-HEAD}"
summary "### Tagged \`${tag}\`"
summary ""
summary "Pushed \`${tag}\` at commit \`${GITHUB_SHA:-HEAD}\`. Publishing next; if that fails the tag remains and must be re-dispatched or deleted."
