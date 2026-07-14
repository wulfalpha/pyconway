#!/usr/bin/env bash

PROJECT_DIR="$HOME/Projects/python/conway"

exec uv run --project "$PROJECT_DIR" \
    python "$PROJECT_DIR/main.py" "$@"
