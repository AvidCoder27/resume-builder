#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/../.."
. scripts/posix/deps.sh
python3 src/resume_editor_server.py
