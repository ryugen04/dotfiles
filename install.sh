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
    sango-project <repo>     Bootstrap project-local sango.yaml if absent

Examples:
    DOTFILES_TARGET_HOME=/tmp/dotfiles-home $(basename "$0") -n codex
    $(basename "$0") codex codex-careflow agents
    $(basename "$0") -n codex-project .
    $(basename "$0") -D codex

Environment:
    DOTFILES_TARGET_HOME  Override the user-level install target. Use this for
                          dry-run verification against a fixture home.
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

install_codex() {
    if ! $DELETE && ! command -v careflow >/dev/null 2>&1; then
        log_error "careflow is not on PATH; install Codex Careflow before enabling hooks"
        return 1
    fi
    install_symlink "$DOTFILES_DIR/packages/codex/.codex/AGENTS.md" "$TARGET_DIR/.codex/AGENTS.md" || return 1
    install_symlink "$DOTFILES_DIR/packages/codex/.codex/hooks.json" "$TARGET_DIR/.codex/hooks.json" || return 1
    install_symlink "$DOTFILES_DIR/packages/codex/.codex/rules/careflow.rules" "$TARGET_DIR/.codex/rules/careflow.rules" || return 1
    update_managed_block "$TARGET_DIR/.codex/config.toml" || return 1
    command -v sango >/dev/null 2>&1 || log_warn "sango is not on PATH; Sango evidence checks are unavailable"
}

copy_managed_file() {
    local source="$1"
    local target="$2"
    local marker="$3"
    ensure_dir "$(dirname "$target")" || return 1

    if $DELETE; then
        if [[ -f "$target" ]] && grep -Fq "$marker" "$target"; then
            run_or_echo rm "$target" || return 1
            log_success "Removed managed file: $target"
        elif [[ -e "$target" ]]; then
            log_warn "Not removing unmanaged file: $target"
        fi
        return 0
    fi

    if [[ -e "$target" ]] && ! grep -Fq "$marker" "$target"; then
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

install_codex_project() {
    local repo="${1:-}"
    [[ -n "$repo" ]] || { log_error "codex-project requires a repository path"; return 1; }
    [[ -d "$repo" ]] || { log_error "Repository path does not exist: $repo"; return 1; }
    repo="$(cd "$repo" && pwd -P)"
    require_git_repo "$repo" || return 1
    if ! $DELETE && ! command -v careflow >/dev/null 2>&1; then
        log_error "careflow is not on PATH; install Codex Careflow before bootstrapping project hooks"
        return 1
    fi
    copy_managed_file "$DOTFILES_DIR/packages/codex/.codex/templates/project-AGENTS.md" "$repo/.codex/AGENTS.md" "dotfiles-managed: codex-careflow-project-v1" || return 1
    copy_managed_file "$DOTFILES_DIR/packages/codex/.codex/hooks.json" "$repo/.codex/hooks.json" "careflow codex-hook" || return 1
    copy_managed_file "$DOTFILES_DIR/packages/codex/.codex/rules/careflow.rules" "$repo/.codex/rules/careflow.rules" "Codex Careflow" || return 1
    copy_managed_file "$DOTFILES_DIR/packages/codex/.codex/templates/careflow/workspace.yaml" "$repo/.aidlc/workspace.yaml" "dotfiles-managed: codex-careflow-workspace-v1" || return 1
}

install_sango_project() {
    local repo="${1:-}"
    [[ -n "$repo" ]] || { log_error "sango-project requires a repository path"; return 1; }
    [[ -d "$repo" ]] || { log_error "Repository path does not exist: $repo"; return 1; }
    repo="$(cd "$repo" && pwd -P)"
    require_git_repo "$repo" || return 1
    copy_managed_file "$DOTFILES_DIR/packages/codex/.codex/templates/sango/sango.yaml" "$repo/sango.yaml" "dotfiles-managed: sango-project-v1" || return 1
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
            codex-project|sango-project)
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
