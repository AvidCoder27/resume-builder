#!/usr/bin/env sh
set -eu

nix-shell -p python3 pandoc wkhtmltopdf --run 'python3 resume_editor_server.py'
