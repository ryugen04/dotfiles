#!/usr/bin/env bash
set -euo pipefail

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${DOTFILES_TARGET_HOME:-$HOME}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DRY_RUN=false
DELETE=false
VERBOSE=false
ADOPT=false
FORCE=false

CODEX_BLOCK_BEGIN="# >>> dotfiles codex managed >>>"
CODEX_BLOCK_END="# <<< dotfiles codex managed <<<"
CAREFLOW_BLOCK_BEGIN="# >>> dotfiles careflow workspace managed >>>"
CAREFLOW_BLOCK_END="# <<< dotfiles careflow workspace managed <<<"

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] [PACKAGES|COMMANDS...]

Options:
    -n, --dry-run    Show what would be done without making changes
    -D, --delete     Remove managed links/blocks instead of installing
    -a, --adopt      Adopt existing files into stow packages
    -v, --verbose    Show detailed output
    -f, --force      Replace conflicting managed target links
    -h, --help       Show this help message

Commands:
    codex                    Install portable user-level Codex Careflow files
    codex-project <repo>     Bootstrap project-local Codex/Careflow files
    careflow-project <repo>  Bootstrap shared .careflow store and worktree links
    claude-project <repo>    Bootstrap project-local Claude Careflow rules
    workspace-careflow <repo>
                             Bootstrap Careflow store, worktree links, and Claude rules
    sango-project <repo>     Bootstrap project-local sango.yaml if absent

Examples:
    DOTFILES_TARGET_HOME=/tmp/dotfiles-home $(basename "$0") -n codex
    $(basename "$0") codex codex-careflow agents
    $(basename "$0") -n codex-project .
    $(basename "$0") workspace-careflow /path/to/workspace
    $(basename "$0") -D codex

Environment:
    DOTFILES_TARGET_HOME  Override the user-level install target. Use this for
                          dry-run verification against a fixture home.
    DOTFILES_CAREFLOW_STORE
                          Optional shared .careflow store path for
                          codex-project/careflow-project/claude-project/
                          sango-project bootstraps. When unset, project roots
                          may reuse an ancestor .careflow store, while
                          careflow-project creates the target root store.
EOF
}

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

run_or_echo() {
    if $DRY_RUN; then
        printf '[DRY-RUN]'
        printf ' %q' "$@"
        printf '\n'
    else
        "$@"
    fi
}

check_stow() {
    if ! command -v stow &>/dev/null; then
        log_error "GNU Stow is not installed"
        exit 1
    fi
}

get_os() {
    case "$(uname -s)" in
        Linux*) echo "linux" ;;
        Darwin*) echo "darwin" ;;
        *) echo "unknown" ;;
    esac
}

get_packages() {
    local pkg_dir="$1"
    if [[ -d "$pkg_dir" ]]; then
        find "$pkg_dir" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort
    fi
}

ensure_dir() {
    local dir="$1"
    if $DRY_RUN; then
        echo "[DRY-RUN] mkdir -p $dir"
    else
        mkdir -p "$dir" || return 1
    fi
}

install_symlink() {
    local source="$1"
    local target="$2"

    if [[ ! -e "$source" ]]; then
        log_error "Source missing: $source"
        return 1
    fi

    if $DELETE; then
        if [[ -L "$target" && "$(readlink "$target")" == "$source" ]]; then
            run_or_echo rm "$target" || return 1
            log_success "Removed managed link: $target"
        elif [[ -e "$target" ]]; then
            log_warn "Not removing unmanaged path: $target"
        fi
        return 0
    fi

    ensure_dir "$(dirname "$target")" || return 1
    if [[ -L "$target" && "$(readlink "$target")" == "$source" ]]; then
        log_success "Link already installed: $target"
        return 0
    fi
    if [[ -e "$target" || -L "$target" ]]; then
        if ! $FORCE; then
            log_error "Refusing to replace unmanaged path without --force: $target"
            return 1
        fi
        run_or_echo rm -f "$target" || return 1
    fi
    run_or_echo ln -s "$source" "$target" || return 1
    log_success "Installed link: $target"
}

render_codex_block() {
    local template="$DOTFILES_DIR/packages/codex/.codex/config.toml.template"
    cat <<EOF
$CODEX_BLOCK_BEGIN
# Portable settings installed by dotfiles. Keep machine-local project trust
# entries outside this block.
EOF
    cat "$template"
    cat <<EOF
$CODEX_BLOCK_END
EOF
}

update_managed_block() {
    local file="$1"
    local tmp
    tmp="$(mktemp)"
    render_codex_block > "$tmp"
    ensure_dir "$(dirname "$file")" || {
        rm -f "$tmp"
        return 1
    }

    # Always back up the existing file before any mutation.
    # Codex (and the user) may store data inside the managed block (mcp_servers,
    # projects trust, hooks.state). Rendering the template overwrites them, so
    # keep a timestamped copy to allow manual restore. Skipped on DRY_RUN.
    if [[ -f "$file" ]] && ! $DRY_RUN; then
        local backup
        backup="${file}.bak.$(date +%Y%m%d-%H%M%S)"
        cp "$file" "$backup" || {
            log_error "Failed to create backup: $backup"
            rm -f "$tmp"
            return 1
        }
        log_info "Backup saved: $backup"
    fi

    if $DELETE; then
        if [[ -f "$file" ]]; then
            if $DRY_RUN; then
                echo "[DRY-RUN] remove managed block from $file"
            else
                awk -v begin="$CODEX_BLOCK_BEGIN" -v end="$CODEX_BLOCK_END" '
                    $0 == begin {skip=1; next}
                    $0 == end {skip=0; next}
                    !skip {print}
                ' "$file" > "$file.tmp" && mv "$file.tmp" "$file" || {
                    rm -f "$tmp" "$file.tmp"
                    return 1
                }
            fi
        fi
        rm -f "$tmp"
        return 0
    fi

    if [[ -f "$file" && $(grep -cFx "$CODEX_BLOCK_BEGIN" "$file") -gt 0 ]]; then
        if $DRY_RUN; then
            echo "[DRY-RUN] update managed block in $file"
        else
            awk -v begin="$CODEX_BLOCK_BEGIN" -v end="$CODEX_BLOCK_END" -v block="$tmp" '
                $0 == begin {
                    while ((getline line < block) > 0) print line
                    skip=1
                    next
                }
                $0 == end {skip=0; next}
                !skip {print}
            ' "$file" > "$file.tmp" && mv "$file.tmp" "$file" || {
                rm -f "$tmp" "$file.tmp"
                return 1
            }
        fi
    elif [[ -f "$file" ]]; then
        if $DRY_RUN; then
            echo "[DRY-RUN] append managed block to $file"
        else
            printf '\n' >> "$file" && cat "$tmp" >> "$file" || {
                rm -f "$tmp"
                return 1
            }
        fi
    else
        if $DRY_RUN; then
            echo "[DRY-RUN] create $file with managed block"
        else
            cp "$tmp" "$file" || {
                rm -f "$tmp"
                return 1
            }
        fi
    fi
    rm -f "$tmp"
    log_success "Codex config managed block ready: $file"
}

normalize_codex_local_config() {
    local file="$1"
    [[ -f "$file" ]] || return 0

    # Keep machine-local config outside the managed block, but normalize values
    # rejected by current Codex. Older local configs used guardian_subagent;
    # Codex 0.139 accepts user or auto_review.
    if grep -q '^approvals_reviewer = "guardian_subagent"$' "$file"; then
        if $DRY_RUN; then
            echo "[DRY-RUN] normalize unsupported approvals_reviewer in $file"
        else
            awk '{
                if ($0 == "approvals_reviewer = \"guardian_subagent\"") {
                    print "approvals_reviewer = \"auto_review\""
                } else {
                    print
                }
            }' "$file" > "$file.tmp" && mv "$file.tmp" "$file" || {
                rm -f "$file.tmp"
                return 1
            }
        fi
        log_success "Codex local config reviewer normalized: $file"
    fi
}

render_careflow_workspace_block() {
    cat <<EOF
$CAREFLOW_BLOCK_BEGIN
careflow:
  store: .careflow
  case_store: .careflow/cases
  active_state:
    scope: worktree
    worktrees_dir: .careflow/active/worktrees
    sessions_dir: .careflow/active/sessions
  topology:
    shared_store: true
    worktree_link_mode: symlink
$CAREFLOW_BLOCK_END
EOF
}

update_careflow_workspace_block() {
    local file="$1"
    local tmp
    tmp="$(mktemp)"
    render_careflow_workspace_block > "$tmp"
    ensure_dir "$(dirname "$file")" || {
        rm -f "$tmp"
        return 1
    }

    if $DELETE; then
        if [[ -f "$file" && $(grep -cFx "$CAREFLOW_BLOCK_BEGIN" "$file") -gt 0 ]]; then
            if $DRY_RUN; then
                echo "[DRY-RUN] remove Careflow workspace block from $file"
            else
                awk -v begin="$CAREFLOW_BLOCK_BEGIN" -v end="$CAREFLOW_BLOCK_END" '
                    $0 == begin {skip=1; next}
                    $0 == end {skip=0; next}
                    !skip {print}
                ' "$file" > "$file.tmp" && mv "$file.tmp" "$file" || {
                    rm -f "$tmp" "$file.tmp"
                    return 1
                }
            fi
        elif [[ -e "$file" ]]; then
            log_warn "Not removing unmanaged Careflow workspace config: $file"
        fi
        rm -f "$tmp"
        return 0
    fi

    if [[ -f "$file" && $(grep -cFx "$CAREFLOW_BLOCK_BEGIN" "$file") -gt 0 ]]; then
        if $DRY_RUN; then
            echo "[DRY-RUN] update Careflow workspace block in $file"
        else
            awk -v begin="$CAREFLOW_BLOCK_BEGIN" -v end="$CAREFLOW_BLOCK_END" -v block="$tmp" '
                $0 == begin {
                    while ((getline line < block) > 0) print line
                    skip=1
                    next
                }
                $0 == end {skip=0; next}
                !skip {print}
            ' "$file" > "$file.tmp" && mv "$file.tmp" "$file" || {
                rm -f "$tmp" "$file.tmp"
                return 1
            }
        fi
    elif [[ -f "$file" ]]; then
        if grep -Eq '^careflow:' "$file"; then
            log_warn "Existing unmanaged careflow key found; leaving unchanged: $file"
        elif $DRY_RUN; then
            echo "[DRY-RUN] append Careflow workspace block to $file"
        else
            printf '\n' >> "$file" && cat "$tmp" >> "$file" || {
                rm -f "$tmp"
                return 1
            }
        fi
    else
        if $DRY_RUN; then
            echo "[DRY-RUN] create $file with Careflow workspace block"
        else
            cp "$tmp" "$file" || {
                rm -f "$tmp"
                return 1
            }
        fi
    fi
    rm -f "$tmp"
    log_success "Careflow workspace config ready: $file"
}

install_codex() {
    if ! $DELETE && ! command -v agent-careflow >/dev/null 2>&1; then
        log_error "agent-careflow is not on PATH; install agent-careflow before enabling hooks"
        return 1
    fi
    install_symlink "$DOTFILES_DIR/packages/codex/.codex/AGENTS.md" "$TARGET_DIR/.codex/AGENTS.md" || return 1
    install_symlink "$DOTFILES_DIR/packages/codex/.codex/hooks.json" "$TARGET_DIR/.codex/hooks.json" || return 1
    install_symlink "$DOTFILES_DIR/packages/codex/.codex/rules/careflow.rules" "$TARGET_DIR/.codex/rules/careflow.rules" || return 1
    # Per-profile config files (Codex CLI >= 0.138 new format). Each is linked as
    # ~/.codex/<profile-name>.config.toml and invoked with `codex exec --profile <name>`.
    local profile_file
    for profile_file in "$DOTFILES_DIR/packages/codex/.codex/profiles/"*.config.toml; do
        [[ -e "$profile_file" ]] || continue
        install_symlink "$profile_file" "$TARGET_DIR/.codex/$(basename "$profile_file")" || return 1
    done
    update_managed_block "$TARGET_DIR/.codex/config.toml" || return 1
    normalize_codex_local_config "$TARGET_DIR/.codex/config.toml" || return 1
    command -v sango >/dev/null 2>&1 || log_warn "sango is not on PATH; Sango evidence checks are unavailable"
}

copy_managed_file() {
    local source="$1"
    local target="$2"
    local marker="$3"
    shift 3
    local markers=("$marker" "$@")
    ensure_dir "$(dirname "$target")" || return 1

    if $DELETE; then
        if [[ -f "$target" ]] && has_any_marker "$target" "${markers[@]}"; then
            run_or_echo rm "$target" || return 1
            log_success "Removed managed file: $target"
        elif [[ -e "$target" ]]; then
            log_warn "Not removing unmanaged file: $target"
        fi
        return 0
    fi

    if [[ -e "$target" ]] && ! has_any_marker "$target" "${markers[@]}"; then
        log_error "Refusing to replace unmanaged existing file: $target"
        return 1
    fi
    if [[ -e "$target" ]] && ! cmp -s "$source" "$target"; then
        if ! $FORCE; then
            log_error "Refusing to replace diverged managed file without --force: $target"
            return 1
        fi
    fi
    if $DRY_RUN; then
        echo "[DRY-RUN] install $target from $source"
    else
        cp "$source" "$target" || return 1
    fi
    log_success "Installed managed file: $target"
}

has_any_marker() {
    local file="$1"
    shift
    local marker
    for marker in "$@"; do
        if grep -Fq "$marker" "$file"; then
            return 0
        fi
    done
    return 1
}

require_git_repo() {
    local repo="$1"
    if [[ ! -d "$repo" ]]; then
        log_error "Repository path does not exist: $repo"
        return 1
    fi
    git -C "$repo" rev-parse --show-toplevel >/dev/null 2>&1 || {
        log_error "Not a git repository: $repo"
        return 1
    }
}

warn_if_not_git_repo() {
    local root="$1"
    git -C "$root" rev-parse --show-toplevel >/dev/null 2>&1 || {
        log_warn "Not a git repository; treating as workspace root: $root"
        return 0
    }
}

ensure_git_info_exclude_pattern() {
    local repo="$1"
    local pattern="$2"
    local exclude
    git -C "$repo" rev-parse --show-toplevel >/dev/null 2>&1 || return 0
    exclude="$(git -C "$repo" rev-parse --git-path info/exclude)" || return 1
    if [[ "$exclude" != /* ]]; then
        exclude="$repo/$exclude"
    fi
    ensure_dir "$(dirname "$exclude")" || return 1
    if [[ -f "$exclude" ]] && grep -Fxq "$pattern" "$exclude"; then
        log_success "Git info exclude already contains $pattern: $exclude"
        return 0
    fi
    if $DRY_RUN; then
        echo "[DRY-RUN] append $pattern to $exclude"
    else
        {
            printf '\n# dotfiles-managed: careflow local ignore\n'
            printf '%s\n' "$pattern"
        } >> "$exclude" || return 1
    fi
    log_success "Git info exclude ignores $pattern: $exclude"
}

contains_path_segment() {
    local path="$1"
    local segment="$2"
    [[ "/$path/" == *"/$segment/"* ]]
}

ensure_careflow_store_dirs() {
    local store="$1"
    ensure_dir "$store" || return 1
    ensure_dir "$store/cases" || return 1
    ensure_dir "$store/active/worktrees" || return 1
    ensure_dir "$store/active/sessions" || return 1
    ensure_dir "$store/leases" || return 1
    ensure_dir "$store/repos" || return 1
    ensure_dir "$store/research" || return 1
    ensure_dir "$store/learnings" || return 1
    ensure_dir "$store/reviews" || return 1
    ensure_dir "$store/incidents" || return 1
}

write_careflow_workspace_metadata() {
    local store="$1"
    local file="$store/workspace.yaml"
    if $DELETE; then
        return 0
    fi
    if [[ -e "$file" ]]; then
        return 0
    fi
    if $DRY_RUN; then
        echo "[DRY-RUN] create $file"
        return 0
    fi
    cat > "$file" <<'EOF'
# dotfiles-managed: codex-careflow-runtime-workspace-v1
version: 1
store: "."
case_store: cases
active_state:
  scope: worktree
  worktrees_dir: active/worktrees
  sessions_dir: active/sessions
EOF
    log_success "Careflow workspace metadata ready: $file"
}

find_ancestor_careflow_store() {
    local target="$1"
    local current
    current="$(dirname "$target")"
    while [[ "$current" != "/" && -n "$current" ]]; do
        if [[ -e "$current/.careflow" || -L "$current/.careflow" ]]; then
            printf '%s\n' "$current/.careflow"
            return 0
        fi
        current="$(dirname "$current")"
    done
    return 1
}

resolve_careflow_store() {
    local target="$1"
    if [[ -n "${DOTFILES_CAREFLOW_STORE:-}" ]]; then
        if [[ "$DOTFILES_CAREFLOW_STORE" = /* ]]; then
            printf '%s\n' "$DOTFILES_CAREFLOW_STORE"
        else
            printf '%s\n' "$target/$DOTFILES_CAREFLOW_STORE"
        fi
        return 0
    fi
    if find_ancestor_careflow_store "$target"; then
        return 0
    fi
    printf '%s\n' "$target/.careflow"
}

install_careflow_store_link() {
    local target="$1"
    local link="$target/.careflow"
    local store
    if $DELETE; then
        log_warn "Not removing Careflow runtime store or link: $link"
        return 0
    fi
    ensure_git_info_exclude_pattern "$target" ".careflow" || return 1

    if [[ -L "$link" ]]; then
        local link_target
        link_target="$(readlink "$link")"
        if [[ "$link_target" = /* ]]; then
            store="$link_target"
        else
            store="$(cd "$(dirname "$link")" && pwd -P)/$link_target"
        fi
        ensure_careflow_store_dirs "$store" || return 1
        write_careflow_workspace_metadata "$store" || return 1
        log_success "Careflow link already installed: $link -> $link_target"
        return 0
    fi

    if [[ -e "$link" ]]; then
        if [[ ! -d "$link" ]]; then
            log_error "Refusing to replace non-directory .careflow path: $link"
            return 1
        fi
        if contains_path_segment "$target" ".worktrees"; then
            log_warn "Worktree-local .careflow directory found; shared-store symlink is preferred: $link"
        fi
        ensure_careflow_store_dirs "$link" || return 1
        write_careflow_workspace_metadata "$link" || return 1
        log_success "Careflow store ready: $link"
        return 0
    fi

    store="$(resolve_careflow_store "$target")"
    ensure_careflow_store_dirs "$store" || return 1
    write_careflow_workspace_metadata "$store" || return 1
    if [[ "$store" == "$link" ]]; then
        log_success "Careflow store ready: $link"
    else
        run_or_echo ln -s "$store" "$link" || return 1
        log_success "Installed Careflow store link: $link -> $store"
    fi
}

install_careflow_store_link_to_store() {
    local target="$1"
    local store="$2"
    local link="$target/.careflow"
    local store_abs
    [[ -d "$target" ]] || { log_error "Target path does not exist: $target"; return 1; }
    if $DELETE; then
        log_warn "Not removing Careflow runtime store or link: $link"
        return 0
    fi
    ensure_git_info_exclude_pattern "$target" ".careflow" || return 1

    ensure_careflow_store_dirs "$store" || return 1
    write_careflow_workspace_metadata "$store" || return 1
    store_abs="$store"
    if ! $DRY_RUN && [[ -d "$store" ]]; then
        store_abs="$(cd "$store" && pwd -P)"
    fi

    if [[ -L "$link" ]]; then
        local link_target current_abs
        link_target="$(readlink "$link")"
        if [[ "$link_target" = /* ]]; then
            current_abs="$link_target"
        else
            current_abs="$(cd "$(dirname "$link")" && pwd -P)/$link_target"
        fi
        if [[ "$current_abs" == "$store_abs" ]]; then
            log_success "Careflow link already installed: $link -> $link_target"
            return 0
        fi
        if ! $FORCE; then
            log_warn "Careflow link points elsewhere; leaving unchanged: $link -> $link_target"
            return 0
        fi
        run_or_echo rm "$link" || return 1
        run_or_echo ln -s "$store_abs" "$link" || return 1
        log_success "Repointed Careflow link: $link -> $store_abs"
        return 0
    fi

    if [[ -e "$link" ]]; then
        if [[ ! -d "$link" ]]; then
            log_error "Refusing to replace non-directory .careflow path: $link"
            return 1
        fi

        local link_abs
        link_abs="$link"
        if ! $DRY_RUN; then
            link_abs="$(cd "$link" && pwd -P)"
        fi
        if [[ "$link_abs" == "$store_abs" ]]; then
            ensure_careflow_store_dirs "$link" || return 1
            write_careflow_workspace_metadata "$link" || return 1
            log_success "Careflow store ready: $link"
            return 0
        fi

        if ! $FORCE; then
            log_warn "Worktree-local .careflow directory found; rerun with --force to archive and link: $link"
            return 0
        fi

        local archive_root safe archive
        archive_root="$store_abs/migrated"
        ensure_dir "$archive_root" || return 1
        safe="${target#/}"
        safe="${safe//\//_}"
        safe="${safe// /_}"
        archive="$archive_root/${safe}-$(date +%Y%m%d-%H%M%S).careflow"
        run_or_echo mv "$link" "$archive" || return 1
        run_or_echo ln -s "$store_abs" "$link" || return 1
        log_success "Archived local Careflow store and linked shared store: $link -> $store_abs"
        return 0
    fi

    run_or_echo ln -s "$store_abs" "$link" || return 1
    log_success "Installed Careflow store link: $link -> $store_abs"
}

install_careflow_worktree_links() {
    local workspace="$1"
    local store="$workspace/.careflow"
    local worktrees_dir="$workspace/.worktrees"
    local target git_marker
    [[ -d "$worktrees_dir" ]] || {
        log_info "No .worktrees directory found under $workspace"
        return 0
    }

    while IFS= read -r target; do
        install_careflow_store_link_to_store "$target" "$store" || return 1
    done < <(find "$worktrees_dir" -mindepth 1 -maxdepth 2 -type d \
        ! -name .git \
        ! -path "$worktrees_dir/*/.local" \
        ! -path "$worktrees_dir/*/.local/*" \
        -print | sort)

    while IFS= read -r git_marker; do
        install_careflow_store_link_to_store "$(dirname "$git_marker")" "$store" || return 1
    done < <(find "$worktrees_dir" -maxdepth 5 \( -type f -o -type d \) -name .git -print | sort)
}

install_careflow_workspace_file() {
    local repo="$1"
    local file="$repo/.aidlc/workspace.yaml"
    if [[ -e "$file" ]]; then
        update_careflow_workspace_block "$file" || return 1
    else
        copy_managed_file "$DOTFILES_DIR/packages/codex/.codex/templates/careflow/workspace.yaml" "$file" "dotfiles-managed: codex-careflow-workspace-v1" || return 1
    fi
}

install_careflow_project() {
    local repo="${1:-}"
    [[ -n "$repo" ]] || { log_error "careflow-project requires a repository or workspace path"; return 1; }
    [[ -d "$repo" ]] || { log_error "Repository path does not exist: $repo"; return 1; }
    repo="$(cd "$repo" && pwd -P)"
    warn_if_not_git_repo "$repo"
    if ! $DELETE && ! command -v agent-careflow >/dev/null 2>&1; then
        log_error "agent-careflow is not on PATH; install agent-careflow before bootstrapping Careflow"
        return 1
    fi

    local DOTFILES_CAREFLOW_STORE="${DOTFILES_CAREFLOW_STORE:-$repo/.careflow}"
    install_careflow_store_link "$repo" || return 1
    install_careflow_workspace_file "$repo" || return 1
    install_careflow_worktree_links "$repo" || return 1
}

install_claude_project() {
    local repo="${1:-}"
    [[ -n "$repo" ]] || { log_error "claude-project requires a repository or workspace path"; return 1; }
    [[ -d "$repo" ]] || { log_error "Repository path does not exist: $repo"; return 1; }
    repo="$(cd "$repo" && pwd -P)"
    warn_if_not_git_repo "$repo"
    if ! $DELETE && ! command -v agent-careflow >/dev/null 2>&1; then
        log_error "agent-careflow is not on PATH; install agent-careflow before bootstrapping Claude Careflow rules"
        return 1
    fi

    copy_managed_file "$DOTFILES_DIR/packages/claude/.claude/templates/project-CLAUDE.md" "$repo/.claude/CLAUDE.md" "dotfiles-managed: claude-careflow-project-v1" || return 1
    copy_managed_file "$DOTFILES_DIR/packages/claude/.claude/rules/careflow-workspace.md" "$repo/.claude/rules/careflow-workspace.md" "Careflow Workspace Rule" || return 1
    install_careflow_store_link "$repo" || return 1
}

install_workspace_careflow() {
    local repo="${1:-}"
    [[ -n "$repo" ]] || { log_error "workspace-careflow requires a repository or workspace path"; return 1; }
    install_careflow_project "$repo" || return 1
    install_claude_project "$repo" || return 1
}

install_codex_project() {
    local repo="${1:-}"
    local legacy_codex_hook_marker
    [[ -n "$repo" ]] || { log_error "codex-project requires a repository path"; return 1; }
    [[ -d "$repo" ]] || { log_error "Repository path does not exist: $repo"; return 1; }
    repo="$(cd "$repo" && pwd -P)"
    warn_if_not_git_repo "$repo"
    if ! $DELETE && ! command -v agent-careflow >/dev/null 2>&1; then
        log_error "agent-careflow is not on PATH; install agent-careflow before bootstrapping project hooks"
        return 1
    fi
    legacy_codex_hook_marker="$(printf 'careflow %s' 'codex-hook')"
    copy_managed_file "$DOTFILES_DIR/packages/codex/.codex/templates/project-AGENTS.md" "$repo/.codex/AGENTS.md" "dotfiles-managed: codex-careflow-project-v1" || return 1
    copy_managed_file "$DOTFILES_DIR/packages/codex/.codex/hooks.json" "$repo/.codex/hooks.json" "agent-careflow hook codex" "$legacy_codex_hook_marker" || return 1
    copy_managed_file "$DOTFILES_DIR/packages/codex/.codex/rules/careflow.rules" "$repo/.codex/rules/careflow.rules" "Codex Careflow" || return 1
    install_careflow_workspace_file "$repo" || return 1
    install_careflow_store_link "$repo" || return 1
}

install_sango_project() {
    local repo="${1:-}"
    [[ -n "$repo" ]] || { log_error "sango-project requires a repository path"; return 1; }
    [[ -d "$repo" ]] || { log_error "Repository path does not exist: $repo"; return 1; }
    repo="$(cd "$repo" && pwd -P)"
    warn_if_not_git_repo "$repo"
    copy_managed_file "$DOTFILES_DIR/packages/codex/.codex/templates/sango/sango.yaml" "$repo/sango.yaml" "dotfiles-managed: sango-project-v1" || return 1
    install_careflow_store_link "$repo" || return 1
}

stow_package() {
    local pkg_dir="$1"
    local pkg_name="$2"
    local stow_opts=("-t" "$TARGET_DIR" "-d" "$pkg_dir")
    $DRY_RUN && stow_opts+=("-n")
    $VERBOSE && stow_opts+=("-v")
    $ADOPT && stow_opts+=("--adopt")
    $DELETE && stow_opts+=("-D") || stow_opts+=("-R")
    stow "${stow_opts[@]}" "$pkg_name" 2>&1 && log_success "Stow ok: $pkg_name"
}

install_named() {
    local name="$1"
    local arg="${2:-}"
    case "$name" in
        codex) install_codex ;;
        codex-project) install_codex_project "$arg" ;;
        careflow-project) install_careflow_project "$arg" ;;
        claude-project) install_claude_project "$arg" ;;
        workspace-careflow) install_workspace_careflow "$arg" ;;
        sango-project) install_sango_project "$arg" ;;
        *)
            if [[ -d "$DOTFILES_DIR/packages/$name" ]]; then
                stow_package "$DOTFILES_DIR/packages" "$name"
            else
                local os
                os="$(get_os)"
                if [[ -d "$DOTFILES_DIR/packages-$os/$name" ]]; then
                    stow_package "$DOTFILES_DIR/packages-$os" "$name"
                else
                    log_warn "Package not found: $name"
                fi
            fi
            ;;
    esac
}

main() {
    local items=()
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -n|--dry-run) DRY_RUN=true; shift ;;
            -D|--delete) DELETE=true; shift ;;
            -v|--verbose) VERBOSE=true; shift ;;
            -a|--adopt) ADOPT=true; shift ;;
            -f|--force) FORCE=true; shift ;;
            -h|--help) usage; exit 0 ;;
            -*) log_error "Unknown option: $1"; usage; exit 1 ;;
            *) items+=("$1"); shift ;;
        esac
    done
    check_stow
    log_info "Detected OS: $(get_os)"
    $DRY_RUN && log_warn "Dry run mode - no changes will be made"

    if [[ ${#items[@]} -eq 0 ]]; then
        mapfile -t items < <(get_packages "$DOTFILES_DIR/packages")
    fi

    local i=0
    while [[ $i -lt ${#items[@]} ]]; do
        case "${items[$i]}" in
            codex-project|careflow-project|claude-project|workspace-careflow|sango-project)
                install_named "${items[$i]}" "${items[$((i + 1))]:-}" || exit 1
                i=$((i + 2))
                ;;
            *)
                install_named "${items[$i]}" || exit 1
                i=$((i + 1))
                ;;
        esac
    done
    if $DRY_RUN; then
        log_info "Dry run complete. Run without -n to apply changes."
    else
        log_success "Done!"
    fi
}

main "$@"
