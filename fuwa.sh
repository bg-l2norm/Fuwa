#!/usr/bin/env bash
# fuwa.sh - The all-in-one script for Fuwa

set -e

print_help() {
    echo "🌸 Fuwa Multi-tool Script 🌸"
    echo "Usage: ./fuwa.sh [command]"
    echo ""
    echo "Commands:"
    echo "  install  - Installs Fuwa (creates venv, installs deps)"
    echo "  update   - Pulls latest changes and updates deps"
    echo "  doctor   - Checks for issues and fixes them"
    echo "  setup    - Configure Fuwa API and settings"
    echo "  run      - Runs Fuwa (default if no command provided)"
    echo "  help     - Shows this help message"
}

get_python() {
    if command -v python3 >/dev/null 2>&1; then
        echo "python3"
    elif command -v python >/dev/null 2>&1; then
        echo "python"
    else
        echo "❌ Error: Python 3 is not installed." >&2
        return 1
    fi
}

check_python_version() {
    local cmd="$1"
    if ! $cmd -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'; then
        echo "❌ Error: Python 3.8 or higher is required." >&2
        return 1
    fi
}

ensure_bootstrap() {
    PYTHON_CMD=$(get_python)
    if [ $? -ne 0 ]; then return 1; fi
    check_python_version "$PYTHON_CMD"
    if [ $? -ne 0 ]; then return 1; fi

    if [ ! -f "venv/bin/activate" ]; then
        if [ -e "venv" ]; then
            echo "⚠️  Found invalid 'venv' (not a working virtual environment). Removing it..."
            rm -rf venv
        fi
        echo "📦 Creating virtual environment..."
        if ! $PYTHON_CMD -m venv venv; then
            echo "❌ Error: Failed to create virtual environment."
            echo "   (On Debian/Ubuntu, you may need: sudo apt install python3-venv)"
            return 1
        fi
    fi

    # Ensure rich is installed so the installer UI can run
    if ! venv/bin/python -c "import rich" >/dev/null 2>&1; then
        echo "📦 Bootstrapping installer dependencies..."
        venv/bin/pip install rich >/dev/null 2>&1 || { echo "❌ Error: Failed to bootstrap installer."; return 1; }
    fi
}

do_run() {
    if [ ! -f "venv/bin/activate" ] || [ ! -f "venv/.fuwa_installed" ]; then
        echo "⚠️ Virtual environment not found or incomplete. Running install first..."
        ensure_bootstrap || return 1
        venv/bin/python installer.py install
        # If install fails, don't try to run
        if [ $? -ne 0 ]; then
            return 1
        fi
    fi

    if [ ! -f "fuwa.py" ]; then
        echo "❌ Error: fuwa.py not found."
        return 1
    fi

    source venv/bin/activate
    python fuwa.py
}

COMMAND=${1:-run}

case "$COMMAND" in
    install)
        ensure_bootstrap || exit 1
        venv/bin/python installer.py install
        ;;
    update)
        ensure_bootstrap || exit 1
        venv/bin/python installer.py update
        ;;
    doctor)
        ensure_bootstrap || exit 1
        venv/bin/python installer.py doctor
        ;;
    setup)
        ensure_bootstrap || exit 1
        venv/bin/python fuwa.py --setup
        ;;
    run)
        do_run
        ;;
    help)
        print_help
        ;;
    *)
        echo "❌ Unknown command: $COMMAND"
        print_help
        exit 1
        ;;
esac
