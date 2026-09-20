#!/usr/bin/env bash
set -euo pipefail

workflow="$1"
ref="$2"
sha="$3"

summary() {
    if [ -n "${GITHUB_STEP_SUMMARY:-}" ]; then
        printf '%s\n' "$1" >> "$GITHUB_STEP_SUMMARY"
    fi
}

started="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "::notice::Dispatched ${workflow} at ${ref} (commit ${sha})"
gh workflow run "${workflow}" --ref "${ref}"

run_id=""
for _ in $(seq 1 60); do
    sleep 5
    run_id="$(
        gh run list \
            --workflow="${workflow}" \
            --event=workflow_dispatch \
            --limit=50 \
            --json databaseId,headSha,createdAt \
            --jq "[.[] | select(.headSha == \"${sha}\" and .createdAt >= \"${started}\")] | sort_by(.createdAt) | last | .databaseId // empty"
    )"
    if [ -n "${run_id}" ]; then
        break
    fi
    echo "::debug::No ${workflow} run for ${sha} yet; polling since ${started}"
done

if [ -z "${run_id}" ]; then
    echo "::error::No ${workflow} run for ${sha} appeared within 5 minutes of dispatch (checked the last 50 runs). Confirm ${workflow} has a workflow_dispatch trigger and the token has actions:write."
    summary "### ${workflow} — dispatch not observed"
    summary ""
    summary "Dispatched at \`${ref}\` (commit \`${sha}\`) but no matching run appeared within 5 minutes."
    summary "Tag \`${ref}\` may already exist. Retry with: \`gh workflow run ${workflow} --ref ${ref}\`"
    exit 1
fi

run_url="$(gh run view "${run_id}" --json url --jq .url 2>/dev/null || echo "")"
echo "::notice::Watching ${workflow} run ${run_id} ${run_url}"

if gh run watch "${run_id}" --compact --exit-status; then
    echo "::notice::${workflow} run ${run_id} succeeded for ${ref}"
    summary "### ${workflow} — published \`${ref}\`"
    summary ""
    summary "Run [${run_id}](${run_url}) succeeded."
    exit 0
fi

conclusion="$(gh run view "${run_id}" --json conclusion --jq .conclusion 2>/dev/null || echo unknown)"

echo "::error::${workflow} run ${run_id} finished with conclusion \"${conclusion}\" for ${ref}. Failed step logs follow; full run: ${run_url}"

echo "::group::Failed steps of ${workflow} run ${run_id}"
gh run view "${run_id}" --log-failed || echo "Could not retrieve failed-step logs for run ${run_id}"
echo "::endgroup::"

summary "### ${workflow} — FAILED for \`${ref}\`"
summary ""
summary "Run [${run_id}](${run_url}) concluded \`${conclusion}\`."
summary ""
summary "Tag \`${ref}\` was already pushed before this step ran, so it still exists."
summary "The version was not published. To retry without re-tagging:"
summary ""
summary '```'
summary "gh workflow run ${workflow} --ref ${ref}"
summary '```'

exit 1
