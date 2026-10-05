#!/usr/bin/env bash
cd ~/code/agents-course || exit 1
source .venv/bin/activate

if ! curl -sf http://127.0.0.1:11434 > /dev/null; then
  echo "Ollama isn't running, starting it..."
  ollama serve > /dev/null 2>&1 &
  until curl -sf http://127.0.0.1:11434 > /dev/null; do sleep 1; done
fi

echo "Ollama is up."
python "${1:-dummyagent.py}"

