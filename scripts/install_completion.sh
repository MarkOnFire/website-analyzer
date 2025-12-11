#!/bin/bash
#
# Bug Finder Shell Completion Installation Script
#
# Installs bash and zsh completion for the bug-finder CLI tool.
#
# Usage:
#   bash scripts/install_completion.sh
#   bash scripts/install_completion.sh --shell bash
#   bash scripts/install_completion.sh --shell zsh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Determine target shell
SHELL_TYPE="${1:-both}"

if [[ "$1" == "--shell" ]]; then
    SHELL_TYPE="${2:-both}"
fi

echo -e "${BLUE}Bug Finder Shell Completion Installer${NC}"
echo "========================================"
echo ""

# Function to install bash completion
install_bash_completion() {
    echo -e "${BLUE}Installing bash completion...${NC}"

    # Determine bash completion directory
    if [[ -d /usr/local/etc/bash_completion.d ]]; then
        COMPLETION_DIR="/usr/local/etc/bash_completion.d"
    elif [[ -d /etc/bash_completion.d ]]; then
        COMPLETION_DIR="/etc/bash_completion.d"
    elif [[ -d ~/.local/share/bash-completion/completions ]]; then
        COMPLETION_DIR="$HOME/.local/share/bash-completion/completions"
    else
        # Fallback: use home directory
        mkdir -p "$HOME/.bash_completion.d"
        COMPLETION_DIR="$HOME/.bash_completion.d"
    fi

    echo "  Target directory: $COMPLETION_DIR"

    # Check if we have write permission
    if [[ ! -w "$COMPLETION_DIR" && "$COMPLETION_DIR" != "$HOME/.bash_completion.d" ]]; then
        echo "  Need sudo for system directory..."
        sudo cp "$PROJECT_DIR/completions/bug-finder.bash" "$COMPLETION_DIR/bug-finder"
        sudo chmod 644 "$COMPLETION_DIR/bug-finder"
    else
        mkdir -p "$COMPLETION_DIR"
        cp "$PROJECT_DIR/completions/bug-finder.bash" "$COMPLETION_DIR/bug-finder"
        chmod 644 "$COMPLETION_DIR/bug-finder"
    fi

    echo -e "${GREEN}✓ Bash completion installed${NC}"

    # Add to .bashrc if not already there
    if [[ -f ~/.bashrc ]]; then
        if ! grep -q "bug-finder.bash" ~/.bashrc && ! grep -q "bash_completion.d" ~/.bashrc; then
            echo ""
            echo "Add this to your ~/.bashrc to enable completions:"
            echo "  source $COMPLETION_DIR/bug-finder"
            echo ""
        fi
    fi
}

# Function to install zsh completion
install_zsh_completion() {
    echo -e "${BLUE}Installing zsh completion...${NC}"

    # Determine zsh completion directory
    if [[ -d /usr/local/share/zsh/site-functions ]]; then
        COMPLETION_DIR="/usr/local/share/zsh/site-functions"
    elif [[ -d /usr/share/zsh/site-functions ]]; then
        COMPLETION_DIR="/usr/share/zsh/site-functions"
    else
        # Fallback: use home directory
        mkdir -p "$HOME/.zsh/completions"
        COMPLETION_DIR="$HOME/.zsh/completions"
    fi

    echo "  Target directory: $COMPLETION_DIR"

    # Check if we have write permission
    if [[ ! -w "$COMPLETION_DIR" && "$COMPLETION_DIR" != "$HOME/.zsh/completions" ]]; then
        echo "  Need sudo for system directory..."
        sudo cp "$PROJECT_DIR/completions/bug-finder.zsh" "$COMPLETION_DIR/_bug-finder"
        sudo chmod 644 "$COMPLETION_DIR/_bug-finder"
    else
        mkdir -p "$COMPLETION_DIR"
        cp "$PROJECT_DIR/completions/bug-finder.zsh" "$COMPLETION_DIR/_bug-finder"
        chmod 644 "$COMPLETION_DIR/_bug-finder"
    fi

    echo -e "${GREEN}✓ Zsh completion installed${NC}"

    # Add to .zshrc if not already there
    if [[ -f ~/.zshrc ]]; then
        if ! grep -q "fpath.*zsh/completions" ~/.zshrc; then
            echo ""
            echo "Add this to your ~/.zshrc to enable completions:"
            echo "  fpath=($HOME/.zsh/completions \$fpath)"
            echo "  autoload -Uz compinit && compinit"
            echo ""
        fi
    fi
}

# Main installation logic
case "$SHELL_TYPE" in
    bash)
        install_bash_completion
        ;;
    zsh)
        install_zsh_completion
        ;;
    both)
        install_bash_completion
        echo ""
        install_zsh_completion
        ;;
    *)
        echo "Unknown shell: $SHELL_TYPE"
        echo "Valid options: bash, zsh, both"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "To test completions, run:"
echo "  bug-finder scan --[TAB]"
echo ""
echo "You may need to restart your shell or run:"
echo "  exec \$SHELL"
echo ""
