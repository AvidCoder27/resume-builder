#!/usr/bin/env sh
set -eu

nix-shell -p python3 pandoc wkhtmltopdf --run \
  'python3 -c "import resume_editor_server as server; server.ensure_resume_files(); server.render_resume()"'
