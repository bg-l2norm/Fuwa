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

do_install() {
    echo "🌸 Starting Fuwa Installation..."
    PYTHON_CMD=$(get_python)
    if [ $? -ne 0 ]; then return 1; fi
    check_python_version "$PYTHON_CMD"
    if [ $? -ne 0 ]; then return 1; fi

    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        if ! $PYTHON_CMD -m venv venv; then
            echo "❌ Error: Failed to create virtual environment."
            echo "   (On Debian/Ubuntu, you may need: sudo apt install python3-venv)"
            return 1
        fi
    else
        echo "✅ Virtual environment already exists."
    fi

    echo "🔄 Activating virtual environment..."
    source venv/bin/activate || { echo "❌ Error: Failed to activate virtual environment."; return 1; }

    echo "⬇️ Installing dependencies..."
    if ! pip install -r requirements.txt; then
        echo "❌ Error: Failed to install dependencies."
        return 1
    fi

    echo "✅ Fuwa Installation Complete! Run './fuwa.sh run' to start."
}

do_update() {
    echo "🌸 Updating Fuwa..."
    if [ -d ".git" ]; then
        echo "⬇️ Pulling latest changes from git..."
        # Use git fetch and merge to avoid pulling issues
        git fetch origin main || true
        git merge FETCH_HEAD || { echo "❌ Error: git merge failed. Please resolve conflicts manually."; exit 1; }
    fi

    if [ -d "venv" ]; then
        source venv/bin/activate || { echo "❌ Error: Failed to activate virtual environment."; return 1; }
        echo "⬇️ Updating dependencies..."
        if ! pip install -r requirements.txt; then
            echo "❌ Error: Failed to update dependencies."
            return 1
        fi
        echo "✅ Fuwa updated successfully!"
    else
        echo "⚠️ Virtual environment not found. Please run './fuwa.sh install' first."
        return 1
    fi
}

do_doctor() {
    echo "🩺 Starting Fuwa Doctor..."
    set +e # Don't exit on error for doctor
    ISSUES_FOUND=0
    ISSUES_FIXED=0

    PYTHON_CMD=$(get_python)
    if [ $? -ne 0 ]; then
        return 1
    fi
    check_python_version "$PYTHON_CMD"
    if [ $? -ne 0 ]; then
        return 1
    fi
    echo "✅ Python check passed."

    if [ ! -d "venv" ]; then
        echo "⚠️ Issue: Virtual environment 'venv' not found."
        ISSUES_FOUND=$((ISSUES_FOUND+1))
        echo "🔧 Fixing: Creating virtual environment..."
        if $PYTHON_CMD -m venv venv; then
            echo "✅ Fixed: Virtual environment created."
            ISSUES_FIXED=$((ISSUES_FIXED+1))
        else
            echo "❌ Error: Failed to create virtual environment."
        fi
    else
        echo "✅ Virtual environment check passed."
    fi

    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        if ! python -c "import textual, litellm, watchdog" 2>/dev/null; then
            echo "⚠️ Issue: Missing dependencies."
            ISSUES_FOUND=$((ISSUES_FOUND+1))
            echo "🔧 Fixing: Installing dependencies..."
            if pip install -r requirements.txt >/dev/null 2>&1; then
                echo "✅ Fixed: Dependencies installed."
                ISSUES_FIXED=$((ISSUES_FIXED+1))
            else
                echo "❌ Error: Failed to install dependencies."
            fi
        else
            echo "✅ Dependencies check passed."
        fi
    else
        echo "❌ Error: Could not find venv/bin/activate"
    fi

    if [ ! -f "config.json" ]; then
        echo "⚠️ Issue: config.json not found."
        ISSUES_FOUND=$((ISSUES_FOUND+1))
        echo "🔧 Fixing: Generating config.json..."
        if python -c "import config; config.load_config()" >/dev/null 2>&1; then
            echo "✅ Fixed: config.json generated."
            ISSUES_FIXED=$((ISSUES_FIXED+1))
        else
            echo "❌ Error: Failed to generate config.json."
        fi
    fi

    if [ -f "config.json" ]; then
        if grep -q '"api_key": "YOUR_API_KEY_HERE"' config.json; then
            echo "⚠️ Warning: config.json still has default API key."
            echo "   Please edit config.json and set a real API key."
            ISSUES_FOUND=$((ISSUES_FOUND+1))
        else
            echo "✅ config.json check passed."
        fi
    fi

    echo ""
    echo "🩺 Doctor summary: Found $ISSUES_FOUND issues, fixed $ISSUES_FIXED issues."
    if [ $ISSUES_FOUND -gt $ISSUES_FIXED ]; then
        echo "⚠️ Some issues require manual intervention."
    else
        echo "🌸 Your Fuwa installation looks healthy!"
    fi
    set -e
}

do_run() {
    if [ ! -d "venv" ]; then
        echo "⚠️ Virtual environment not found. Running install first..."
        do_install
    fi
    source venv/bin/activate
    python fuwa.py
}

COMMAND=${1:-run}

case "$COMMAND" in
    install)
        do_install
        ;;
    update)
        do_update
        ;;
    doctor)
        do_doctor
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
