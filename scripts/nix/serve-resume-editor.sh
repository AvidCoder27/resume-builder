#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/../.."
nix-shell -p python3 pandoc wkhtmltopdf --run 'python3 src/resume_editor_server.py'
