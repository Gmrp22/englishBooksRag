import os
import pathlib
import re

import pymupdf4llm
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

SOURCE_PDF = os.environ["SOURCE_PDF"]
OUTPUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "designing-data-intensive-applications.md"

# line that is just a stray page number (typical footer)
PAGE_NUMBER_LINE = re.compile(r"^\s*\d{1,4}\s*$")
# lines that mark markdown structure and shouldn't be merged into a paragraph
BLOCK_PREFIX = re.compile(r"^\s*(#{1,6}\s|[-*]\s|\d+\.\s|\||```)")


def clean_markdown(text: str) -> str:
    paragraphs = []
    buffer = []

    def flush():
        if buffer:
            paragraphs.append(" ".join(buffer))
            buffer.clear()

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if PAGE_NUMBER_LINE.match(line):
            continue
        if BLOCK_PREFIX.match(line):
            flush()
            paragraphs.append(stripped)
            continue
        buffer.append(stripped)
    flush()

    return "\n\n".join(paragraphs)

#Read pdf
md_text = pymupdf4llm.to_markdown(SOURCE_PDF)
#Clean
clean_text = clean_markdown(md_text)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.write_text(clean_text, encoding="utf-8")

print(f"Guardado en {OUTPUT_FILE}")