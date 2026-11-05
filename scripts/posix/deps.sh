#!/usr/bin/env sh
# Shared helper (sourced): verifies python3, pandoc, and wkhtmltopdf are on PATH.

missing=""
for tool in python3 pandoc wkhtmltopdf; do
  command -v "$tool" >/dev/null 2>&1 || missing="$missing $tool"
done

if [ -n "$missing" ]; then
  echo "Missing:$missing" >&2
  case "$(uname -s)" in
    Darwin) echo "Install with: brew install python pandoc wkhtmltopdf" >&2 ;;
    *)
      if command -v apt-get >/dev/null 2>&1; then
        echo "Install with: sudo apt-get install python3 pandoc wkhtmltopdf" >&2
      elif command -v dnf >/dev/null 2>&1; then
        echo "Install with: sudo dnf install python3 pandoc wkhtmltopdf" >&2
      elif command -v pacman >/dev/null 2>&1; then
        echo "Install with: sudo pacman -S python pandoc wkhtmltopdf" >&2
      else
        echo "Install python3, pandoc, and wkhtmltopdf with your package manager." >&2
      fi
      ;;
  esac
  exit 1
fi
