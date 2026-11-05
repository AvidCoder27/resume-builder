# Local Resume Editor

A local, Markdown-first resume editor that renders an ATS-friendly PDF.

## Run

```sh
# Nix (provides all dependencies)
sh scripts/nix/serve-resume-editor.sh

# Linux/macOS without Nix (needs python3, pandoc, wkhtmltopdf on PATH)
sh scripts/posix/serve-resume-editor.sh
```

On Windows, run `scripts\windows\install.bat` once (installs Python, Pandoc, and wkhtmltopdf via winget), then double-click or run:

```bat
scripts\windows\serve-resume-editor.bat
```

Open `http://127.0.0.1:8765` in a browser. The Nix scripts provide Python, Pandoc, and wkhtmltopdf automatically; the POSIX and Windows scripts need them installed (Windows can install them for you).

## Features

- Edit Markdown and preview the generated PDF side by side or full screen.
- Select a font and 0.5, 0.75, or 1 inch page margins.
- Import, save, and download Markdown files.
- Keep up to five distinct prior Markdown versions and restore them from the editor.

## Local Data

Personal resume source, render output, styling selections, and backups live in `local-resumes/`. That directory is ignored by Git; the repository tracks only reusable code, templates, and writing guidance in `docs/resume-tips.md`.

## Project Layout

```
src/                 Editor server (resume_editor_server.py) and UI (resume-editor.html)
templates/           Starter resume Markdown and CSS
docs/                Resume writing guidance (resume-tips.md)
scripts/nix/         serve-resume-editor.sh, render-resume.sh (via nix-shell)
scripts/posix/       Same scripts using system-installed tools, plus deps.sh
scripts/windows/     install.bat, deps.bat, serve-resume-editor.bat, render-resume.bat
local-resumes/       Your resumes, renders, and backups (git-ignored)
```
