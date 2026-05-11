#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
errors=0

fail() {
    printf '[FAIL] %s\n' "$1" >&2
    errors=$((errors + 1))
}

pass() {
    printf '[OK] %s\n' "$1"
}

tracked_and_untracked_files() {
    (
        cd "$ROOT_DIR"
        git ls-files
        git ls-files --others --exclude-standard
    ) | sort -u
}

scan_pattern() {
    local label="$1"
    local pattern="$2"
    local tmp
    tmp="$(mktemp)"
    if tracked_and_untracked_files | (cd "$ROOT_DIR" && xargs -r grep -InE "$pattern") > "$tmp" 2>/dev/null; then
        sed -E 's/^([^:]+:[0-9]+):.*$/\1: forbidden pattern/' "$tmp" >&2
        fail "$label"
    else
        pass "$label"
    fi
    rm -f "$tmp"
}

scan_forbidden_words() {
    if [[ -z "${FORBIDDEN_WORDS:-}" ]]; then
        fail "FORBIDDEN_WORDS must be set from local env or CI secret"
        return
    fi

    local pattern
    pattern="$(printf '%s\n' "$FORBIDDEN_WORDS" | sed '/^[[:space:]]*$/d' | sed 's/[.[\*^$()+?{}|\\]/\\&/g' | paste -sd '|' -)"
    if [[ -z "$pattern" ]]; then
        fail "FORBIDDEN_WORDS does not contain usable entries"
        return
    fi
    pass "FORBIDDEN_WORDS is configured"
    scan_pattern "no configured forbidden identifiers in tracked or candidate files" "$pattern"
}

require_file_absent() {
    local path="$1"
    if git -C "$ROOT_DIR" ls-files --error-unmatch "$path" >/dev/null 2>&1; then
        fail "$path must not be tracked"
    else
        pass "$path is not tracked"
    fi
}

require_file_exists() {
    local path="$1"
    if [[ -f "$ROOT_DIR/$path" ]]; then
        pass "$path exists"
    else
        fail "$path is missing"
    fi
}

require_pattern() {
    local path="$1"
    local pattern="$2"
    local label="$3"
    if grep -Eq "$pattern" "$ROOT_DIR/$path"; then
        pass "$label"
    else
        fail "$label"
    fi
}

scan_forbidden_words
require_file_absent "packages/codex/.codex/config.toml"
require_file_exists "packages/codex/.codex/config.toml.template"
require_file_exists "install.sh"
require_file_exists ".github/workflows/secret-scan.yml"
require_file_exists "packages/codex-careflow/.codex-careflow/bin/doctor.py"

home_path_pattern="$(printf '/%s/[[:alnum:]_.-]+/' home)"
users_path_pattern="$(printf '/%s/[[:alnum:]_.-]+/' Users)"
scan_pattern "no machine-local absolute paths" "$home_path_pattern|$users_path_pattern"
scan_pattern "no obvious secret-shaped patterns" 'BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY|ghp_[[:alnum:]_]{30,}|github_pat_[[:alnum:]_]{20,}|sk-[[:alnum:]_-]{20,}|(api[_-]?key|secret[_-]?key|access[_-]?token|private[_-]?key)[[:space:]]*[:=][[:space:]]*['\''"][^'\''"]{12,}'

for pattern in \
    '\.aidlc/local/' \
    '\.aidlc/logs/' \
    '\.aidlc/runs/' \
    '\.worktrees/' \
    '\.careflow/' \
    '\.sango/logs/' \
    '\.sango/pids/' \
    '\.sango/work/'
do
    require_pattern ".gitignore" "$pattern" ".gitignore ignores $pattern"
done

for pattern in \
    '\\.aidlc' \
    '\\.worktrees' \
    '\\.careflow' \
    '\\.sango'
do
    require_pattern ".stow-global-ignore" "$pattern" ".stow-global-ignore excludes $pattern"
done

if (( errors > 0 )); then
    printf '\n%d portability check(s) failed.\n' "$errors" >&2
    exit 1
fi

printf '\nPortability checks passed.\n'
