#!/bin/bash

BINDIR="$(dirname "$(readlink -f "$BASH_SOURCE")")"
ROOTDIR="$(readlink -f "$BINDIR"/..)"
PROC="$(basename "$0")"

# shellcheck source=/dev/null
source "$ROOTDIR"/venv/bin/activate
"$ROOTDIR/$PROC.py" "$@"
