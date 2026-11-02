#!/usr/bin/env python3
"""Serve the local resume editor and safely run the installed renderer."""

import json
import os
import re
import subprocess
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESUME_DIR = ROOT / "local-resumes"
MARKDOWN_FILE = RESUME_DIR / "resume.md"
STYLESHEET_FILE = RESUME_DIR / "resume.css"
HTML_FILE = RESUME_DIR / "resume.html"
PDF_FILE = RESUME_DIR / "resume.pdf"
MARKDOWN_TEMPLATE = ROOT / "resume-template.md"
STYLESHEET_TEMPLATE = ROOT / "resume-template.css"
PORT = 8765

FONT_STACKS = {
    "Cambria": 'Cambria, "Liberation Serif", "Times New Roman", serif',
    "Times New Roman": '"Times New Roman", "Liberation Serif", Times, serif',
    "Georgia": 'Georgia, "Liberation Serif", serif',
    "Garamond": 'Garamond, "EB Garamond", "Liberation Serif", serif',
    "Calibri": 'Calibri, Carlito, Arial, sans-serif',
    "Arial": 'Arial, Helvetica, sans-serif',
}
FONT_PATTERN = re.compile(r"(font-family:\s*)[^;]+;")


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
    updated, replacements = FONT_PATTERN.subn(rf"\1{stack};", stylesheet, count=1)
    if replacements != 1:
        raise RuntimeError("The resume font setting is missing from resume.css.")
    STYLESHEET_FILE.write_text(updated, encoding="utf-8")


def render_resume():
    ensure_resume_files()
    pandoc = subprocess.run(
        ["pandoc", "--from", "markdown", "--to", "html5", "--standalone", "--css", STYLESHEET_FILE.name, "--output", HTML_FILE.name, MARKDOWN_FILE.name],
        cwd=RESUME_DIR,
        capture_output=True,
        text=True,
    )
    if pandoc.returncode:
        raise RuntimeError(pandoc.stderr.strip() or "Pandoc could not render the Markdown.")

    pdf = subprocess.run(
        ["wkhtmltopdf", "--enable-local-file-access", "--disable-javascript", "--encoding", "utf-8", "--print-media-type", "--disable-smart-shrinking", "--page-size", "Letter", "--margin-top", "0", "--margin-right", "0", "--margin-bottom", "0", "--margin-left", "0", HTML_FILE.name, PDF_FILE.name],
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
                write_json(self, HTTPStatus.OK, {"markdown": MARKDOWN_FILE.read_text(encoding="utf-8"), "font": current_font()})
            except RuntimeError as error:
                write_json(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(error)})
            return
        if self.path.split("?", 1)[0] == "/":
            self.path = "/resume-editor.html"
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/render":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 1_000_000:
                raise ValueError("The Markdown document is too large.")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            markdown = payload["markdown"]
            font = payload["font"]
            if not isinstance(markdown, str) or not markdown.strip():
                raise ValueError("Resume Markdown cannot be empty.")
            if font not in FONT_STACKS:
                raise ValueError("Choose a supported font.")
            ensure_resume_files()
            MARKDOWN_FILE.write_text(markdown, encoding="utf-8")
            update_font(font)
            render_resume()
            write_json(self, HTTPStatus.OK, {"ok": True})
        except (KeyError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as error:
            write_json(self, HTTPStatus.BAD_REQUEST, {"error": str(error)})
        except RuntimeError as error:
            write_json(self, HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(error)})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", PORT), ResumeEditorHandler)
    print(f"Resume editor: http://127.0.0.1:{PORT}")
    server.serve_forever()
