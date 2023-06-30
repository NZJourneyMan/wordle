#!/bin/bash

BINDIR="$(readlink -f "$(dirname "$0")")"
PROC="$(basename "$0")"

# shellcheck source=/dev/null
source "$BINDIR"/venv/bin/activate
"$BINDIR/$PROC.py" "$@"
