# Local Resume Editor

A local, Markdown-first resume editor that renders an ATS-friendly PDF.

## Run

```sh
sh serve-resume-editor.sh
```

Open `http://127.0.0.1:8765` in a browser. The launcher uses Nix to provide Python, Pandoc, and wkhtmltopdf.

## Features

- Edit Markdown and preview the generated PDF side by side or full screen.
- Select a font and 0.5, 0.75, or 1 inch page margins.
- Import, save, and download Markdown files.
- Keep up to five distinct prior Markdown versions and restore them from the editor.

## Local Data

Personal resume source, render output, styling selections, and backups live in `local-resumes/`. That directory is ignored by Git; the repository tracks only reusable code, templates, and writing guidance in `resume-tips.md`.
