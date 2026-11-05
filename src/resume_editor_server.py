#!/usr/bin/env python3
"""Serve the local resume editor and safely run the installed renderer."""

import json
import os
import re
import subprocess
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RESUME_DIR = ROOT / "local-resumes"
MARKDOWN_FILE = RESUME_DIR / "resume.md"
STYLESHEET_FILE = RESUME_DIR / "resume.css"
HTML_FILE = RESUME_DIR / "resume.html"
PDF_FILE = RESUME_DIR / "resume.pdf"
BACKUP_DIR = RESUME_DIR / "backups"
MARKDOWN_TEMPLATE = ROOT / "templates" / "resume-template.md"
STYLESHEET_TEMPLATE = ROOT / "templates" / "resume-template.css"
PORT = 8765

FONT_STACKS = {
    "Cambria": 'Cambria, "Liberation Serif", "Times New Roman", serif',
    "Times New Roman": '"Times New Roman", "Liberation Serif", Times, serif',
    "Georgia": 'Georgia, "Liberation Serif", serif',
    "Garamond": 'Garamond, "EB Garamond", "Liberation Serif", serif',
    "Calibri": 'Calibri, Carlito, Arial, sans-serif',
    "Arial": 'Arial, Helvetica, sans-serif',
}
PAGE_MARGINS = {"0.5": "0.5in", "0.75": "0.75in", "1": "1in"}
FONT_PATTERN = re.compile(r"(font-family:\s*)[^;]+;")
MARGIN_PATTERN = re.compile(r"(--page-margin:\s*)[^;]+;")
LEGACY_MARGIN_PATTERN = re.compile(r"(@page\s*\{[^}]*?margin:\s*)[^;]+;", re.DOTALL)


def write_json(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def ensure_resume_files():
    RESUME_DIR.mkdir(exist_ok=True)
    if not MARKDOWN_FILE.exists():
        MARKDOWN_FILE.write_text(MARKDOWN_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    if not STYLESHEET_FILE.exists():
        STYLESHEET_FILE.write_text(STYLESHEET_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
    else:
        stylesheet = STYLESHEET_FILE.read_text(encoding="utf-8")
        if "--page-margin:" not in stylesheet:
            legacy_margin = LEGACY_MARGIN_PATTERN.search(stylesheet)
            margin = legacy_margin.group(0).split("margin:", 1)[1].rstrip(";").strip() if legacy_margin else "0.5in"
            if margin not in PAGE_MARGINS.values():
                margin = "0.5in"
            stylesheet = f":root {{\n  --page-margin: {margin};\n}}\n\n" + LEGACY_MARGIN_PATTERN.sub(r"\g<1>0;", stylesheet, count=1)
            STYLESHEET_FILE.write_text(stylesheet, encoding="utf-8")


def recent_backups():
    if not BACKUP_DIR.exists():
        return []
    backups = sorted(BACKUP_DIR.glob("resume-*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    return [{"name": path.name, "label": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")} for path in backups]


def save_markdown(markdown):
    ensure_resume_files()
    current = MARKDOWN_FILE.read_text(encoding="utf-8")
    if current != markdown:
        BACKUP_DIR.mkdir(exist_ok=True)
        backup_contents = [path.read_text(encoding="utf-8") for path in BACKUP_DIR.glob("resume-*.md")]
        if current not in backup_contents:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
            (BACKUP_DIR / f"resume-{timestamp}.md").write_text(current, encoding="utf-8")
        MARKDOWN_FILE.write_text(markdown, encoding="utf-8")

        # Keep only the five versions immediately preceding the current file.
        for backup in recent_backups()[5:]:
            (BACKUP_DIR / backup["name"]).unlink()
    return recent_backups()


def load_backup(name):
    if Path(name).name != name or not name.startswith("resume-") or not name.endswith(".md"):
        raise ValueError("Choose a valid backup.")
    backup = BACKUP_DIR / name
    if not backup.is_file():
        raise FileNotFoundError("That backup no longer exists.")
    markdown = backup.read_text(encoding="utf-8")
    return markdown, save_markdown(markdown)


def current_font():
    ensure_resume_files()
    stylesheet = STYLESHEET_FILE.read_text(encoding="utf-8")
    match = FONT_PATTERN.search(stylesheet)
    if not match:
        raise RuntimeError("The resume font setting is missing from resume.css.")
    stack = match.group(0).split(":", 1)[1].rstrip(";").strip()
    return next((name for name, value in FONT_STACKS.items() if value == stack), "Cambria")


def update_font(font):
    ensure_resume_files()
    stack = FONT_STACKS[font]
    stylesheet = STYLESHEET_FILE.read_text(encoding="utf-8")
    updated, replacements = FONT_PATTERN.subn(rf"\g<1>{stack};", stylesheet, count=1)
    if replacements != 1:
        raise RuntimeError("The resume font setting is missing from resume.css.")
    STYLESHEET_FILE.write_text(updated, encoding="utf-8")


def current_margin():
    ensure_resume_files()
    stylesheet = STYLESHEET_FILE.read_text(encoding="utf-8")
    match = MARGIN_PATTERN.search(stylesheet)
    if not match:
        raise RuntimeError("The page margin setting is missing from resume.css.")
    value = match.group(0).split("margin:", 1)[1].rstrip(";").strip()
    return next((margin for margin, css_value in PAGE_MARGINS.items() if css_value == value), "0.5")


def update_margin(margin):
    stylesheet = STYLESHEET_FILE.read_text(encoding="utf-8")
    updated, replacements = MARGIN_PATTERN.subn(rf"\g<1>{PAGE_MARGINS[margin]};", stylesheet, count=1)
    if replacements != 1:
        raise RuntimeError("The page margin setting is missing from resume.css.")
    STYLESHEET_FILE.write_text(updated, encoding="utf-8")


def render_resume():
    ensure_resume_files()
    page_margin = PAGE_MARGINS[current_margin()]
    pandoc = subprocess.run(
        ["pandoc", "--from", "markdown", "--to", "html5", "--standalone", "--css", STYLESHEET_FILE.name, "--output", HTML_FILE.name, MARKDOWN_FILE.name],
        cwd=RESUME_DIR,
        capture_output=True,
        text=True,
    )
    if pandoc.returncode:
        raise RuntimeError(pandoc.stderr.strip() or "Pandoc could not render the Markdown.")

    pdf = subprocess.run(
        ["wkhtmltopdf", "--enable-local-file-access", "--disable-javascript", "--encoding", "utf-8", "--print-media-type", "--disable-smart-shrinking", "--page-size", "Letter", "--margin-top", page_margin, "--margin-right", page_margin, "--margin-bottom", page_margin, "--margin-left", page_margin, HTML_FILE.name, PDF_FILE.name],
        cwd=RESUME_DIR,
        capture_output=True,
        text=True,
    )
    if pdf.returncode:
        raise RuntimeError(pdf.stderr.strip() or "wkhtmltopdf could not create the PDF.")


class ResumeEditorHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?", 1)[0] == "/api/resume":
            try:
                ensure_resume_files()
                write_json(self, HTTPStatus.OK, {"markdown": MARKDOWN_FILE.read_text(encoding="utf-8"), "font": current_font(), "margin": current_margin()})
            except RuntimeError as error:
                write_json(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(error)})
            return
        if self.path.split("?", 1)[0] == "/api/backups":
            write_json(self, HTTPStatus.OK, {"backups": recent_backups()})
            return
        if self.path.split("?", 1)[0] == "/":
            self.path = "/src/resume-editor.html"
        super().do_GET()

    def do_POST(self):
        if self.path not in {"/api/render", "/api/save", "/api/load-backup"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                raise ValueError("The Markdown document is too large.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if self.path == "/api/load-backup":
                markdown, backups = load_backup(payload["backup"])
                write_json(self, HTTPStatus.OK, {"markdown": markdown, "backups": backups})
                return

            markdown = payload["markdown"]
            if not isinstance(markdown, str) or not markdown.strip():
                raise ValueError("Resume Markdown cannot be empty.")
            backups = save_markdown(markdown)

            if self.path == "/api/save":
                write_json(self, HTTPStatus.OK, {"markdown": markdown, "backups": backups})
                return

            font = payload["font"]
            margin = payload["margin"]
            if font not in FONT_STACKS:
                raise ValueError("Choose a supported font.")
            if margin not in PAGE_MARGINS:
                raise ValueError("Choose a supported page margin.")
            update_font(font)
            update_margin(margin)
            render_resume()
            write_json(self, HTTPStatus.OK, {"ok": True, "backups": backups})
        except (KeyError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
            write_json(self, HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except FileNotFoundError as error:
            write_json(self, HTTPStatus.NOT_FOUND, {"error": str(error)})
        except RuntimeError as error:
            write_json(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(error)})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), ResumeEditorHandler)
    print(f"Resume editor: http://127.0.0.1:{PORT}")
    server.serve_forever()
