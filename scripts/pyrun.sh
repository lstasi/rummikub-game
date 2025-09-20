#!/bin/bash

# pyrun - Execute Python code snippets with project context
# Usage: ./scripts/pyrun.sh "python code here"
#        ./scripts/pyrun.sh -f script.py
#        ./scripts/pyrun.sh -i (interactive mode)

set -e

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Add src to Python path
export PYTHONPATH="$PROJECT_ROOT/src:${PYTHONPATH:-}"

# Function to run Python code
run_python() {
    python3 -c "$1"
}

# Function to run Python file
run_file() {
    python3 "$1"
}

# Function to start interactive Python with project context
run_interactive() {
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT/src')
print('Python interactive mode with project context loaded.')
print('Project root: $PROJECT_ROOT')
print('You can now import from: rummikub.models, etc.')
print('Type exit() to quit.')
print()
" -i
}

# Parse arguments
case "${1:-}" in
    -h|--help)
        echo "pyrun - Execute Python code with project context"
        echo
        echo "Usage:"
        echo "  ./scripts/pyrun.sh \"python code\"     # Run inline code"
        echo "  ./scripts/pyrun.sh -f script.py       # Run Python file"
        echo "  ./scripts/pyrun.sh -i                 # Interactive mode"
        echo
        echo "Examples:"
        echo "  ./scripts/pyrun.sh \"from rummikub.models import Color; print(Color.RED)\""
        echo "  ./scripts/pyrun.sh -f tests/test_example.py"
        echo "  ./scripts/pyrun.sh -i"
        ;;
    -i|--interactive)
        run_interactive
        ;;
    -f|--file)
        if [ -z "${2:-}" ]; then
            echo "Error: -f requires a file path"
            exit 1
        fi
        run_file "$2"
        ;;
    "")
        echo "Error: No Python code provided"
        echo "Use --help for usage information"
        exit 1
        ;;
    *)
        run_python "$1"
        ;;
esac