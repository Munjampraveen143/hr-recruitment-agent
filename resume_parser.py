
import re
from pathlib import Path

import fitz
from docx import Document


def extract_text(file_path):
    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        text = ""

        with fitz.open(path) as pdf:
            for page in pdf:
                text += page.get_text() + "\n"

        return text.strip()

    elif extension == ".docx":
        document = Document(path)

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
        ]

        return "\n".join(paragraphs).strip()

    elif extension == ".txt":
        return path.read_text(
            encoding="utf-8",
            errors="ignore"
        ).strip()

    else:
        raise ValueError(
            "Unsupported format. Upload PDF, DOCX, or TXT."
        )


def extract_email(text):
    match = re.search(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        text
    )

    return match.group(0) if match else ""


def extract_phone(text):
    match = re.search(
        r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?"
        r"(?:\d[-.\s]?){9,12}\d(?!\d)",
        text
    )

    return match.group(0).strip() if match else ""


def extract_candidate_name(text):
    for line in text.splitlines():
        line = line.strip()

        if (
            line
            and len(line) < 70
            and not "@" in line
            and not any(char.isdigit() for char in line)
        ):
            return line

    return "Unknown Candidate"


def parse_resume(file_path):
    text = extract_text(file_path)

    if not text:
        raise ValueError(
            "No text found. This may be a scanned PDF."
        )

    return {
        "name": extract_candidate_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "resume_text": text
    }
