#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")/../.."
nix-shell -p python3 pandoc wkhtmltopdf --run \
  'python3 -c "import sys; sys.path.insert(0, \"src\"); import resume_editor_server as server; server.ensure_resume_files(); server.render_resume()"'
