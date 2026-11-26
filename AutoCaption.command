#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

# Ensure venv exists or create it
if [ ! -d "$DIR/venv" ]; then
    echo "⚡ Initializing Auto Caption Python Environment..."
    python3 -m venv "$DIR/venv"
    "$DIR/venv/bin/pip" install --upgrade pip
    "$DIR/venv/bin/pip" install imageio-ffmpeg openai-whisper
fi

# Run Auto Caption Studio
"$DIR/venv/bin/python3" "$DIR/ui/desktop_gui.py"
