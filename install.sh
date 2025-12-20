#!/usr/bin/env bash
set -uo pipefail

# dotfiles installer using GNU Stow
# Usage:
#   ./install.sh              # Install all packages
#   ./install.sh shell nvim   # Install specific packages
#   ./install.sh -n           # Dry run
#   ./install.sh -D shell     # Uninstall package

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$HOME"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Options
DRY_RUN=false
DELETE=false
VERBOSE=false
ADOPT=false

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] [PACKAGES...]

Options:
    -n, --dry-run    Show what would be done without making changes
    -D, --delete     Remove symlinks instead of creating them
    -a, --adopt      Adopt existing files into stow packages
    -v, --verbose    Show detailed output
    -h, --help       Show this help message

Examples:
    $(basename "$0")              # Install all packages
    $(basename "$0") shell nvim   # Install specific packages
    $(basename "$0") -n           # Dry run (preview changes)
    $(basename "$0") -D shell     # Uninstall shell package
EOF
}

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_stow() {
    if ! command -v stow &>/dev/null; then
        log_error "GNU Stow is not installed"
        echo ""
        echo "Install with:"
        echo "  Ubuntu/Debian: sudo apt install stow"
        echo "  macOS:         brew install stow"
        echo "  Arch:          sudo pacman -S stow"
        exit 1
    fi
}

get_os() {
    case "$(uname -s)" in
        Linux*)  echo "linux" ;;
        Darwin*) echo "darwin" ;;
        *)       echo "unknown" ;;
    esac
}

get_packages() {
    local pkg_dir="$1"
    if [[ -d "$pkg_dir" ]]; then
        find "$pkg_dir" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort
    fi
}

stow_package() {
    local pkg_dir="$1"
    local pkg_name="$2"
    local stow_opts=("-t" "$TARGET_DIR" "-d" "$pkg_dir")

    if $DRY_RUN; then
        stow_opts+=("-n")
    fi

    if $VERBOSE; then
        stow_opts+=("-v")
    fi

    if $ADOPT; then
        stow_opts+=("--adopt")
    fi

    if $DELETE; then
        stow_opts+=("-D")
        if stow "${stow_opts[@]}" "$pkg_name" 2>&1; then
            log_success "Removed: $pkg_name"
        else
            log_warn "Failed to remove: $pkg_name (skipping)"
        fi
    else
        # Use --restow to handle updates cleanly
        stow_opts+=("-R")
        if stow "${stow_opts[@]}" "$pkg_name" 2>&1; then
            log_success "Installed: $pkg_name"
        else
            log_warn "Failed to install: $pkg_name (skipping)"
        fi
    fi
}

main() {
    local packages=()

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -D|--delete)
                DELETE=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -a|--adopt)
                ADOPT=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
            *)
                packages+=("$1")
                shift
                ;;
        esac
    done

    check_stow

    local os
    os=$(get_os)
    log_info "Detected OS: $os"

    if $DRY_RUN; then
        log_warn "Dry run mode - no changes will be made"
    fi

    # Determine which packages to install
    local common_packages
    common_packages=$(get_packages "$DOTFILES_DIR/packages")

    local os_packages=""
    if [[ -d "$DOTFILES_DIR/packages-$os" ]]; then
        os_packages=$(get_packages "$DOTFILES_DIR/packages-$os")
    fi

    # If specific packages requested, filter
    if [[ ${#packages[@]} -gt 0 ]]; then
        for pkg in "${packages[@]}"; do
            if [[ -d "$DOTFILES_DIR/packages/$pkg" ]]; then
                stow_package "$DOTFILES_DIR/packages" "$pkg"
            elif [[ -d "$DOTFILES_DIR/packages-$os/$pkg" ]]; then
                stow_package "$DOTFILES_DIR/packages-$os" "$pkg"
            else
                log_warn "Package not found: $pkg"
            fi
        done
    else
        # Install all packages
        echo ""
        log_info "Installing common packages..."
        for pkg in $common_packages; do
            stow_package "$DOTFILES_DIR/packages" "$pkg"
        done

        if [[ -n "$os_packages" ]]; then
            echo ""
            log_info "Installing $os-specific packages..."
            for pkg in $os_packages; do
                stow_package "$DOTFILES_DIR/packages-$os" "$pkg"
            done
        fi
    fi

    echo ""
    if $DRY_RUN; then
        log_info "Dry run complete. Run without -n to apply changes."
    else
        log_success "Done!"
    fi
}

main "$@"
