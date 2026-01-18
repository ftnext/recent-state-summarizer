#!/bin/bash

if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
    exit 0
fi

PROJECT_DIR=$(dirname $(dirname $(dirname $0)))
echo "${PROJECT_DIR}"
echo "Setting up Claude Code on the Web environment..."

echo "Install gh..."
bun x gh-setup-hooks

if [ ! -d "${PROJECT_DIR}/venv" ]; then
    echo "Create Python virtual environment..."
    python -m venv "${PROJECT_DIR}/venv" --upgrade-deps
    "${PROJECT_DIR}/venv/bin/python" -m pip install -r "${PROJECT_DIR}/requirements.lock"
    "${PROJECT_DIR}/venv/bin/python" -m pip install -e '.[testing]'
fi

echo "Setup complete!"
exit 0
