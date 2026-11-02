"""
Parser and CLI lookup tool for CS-370_Artificial_Intelligence_Lab_Manual_Updated_2026.docx.
Extracts all 15 labs (objectives, theory, reference implementation, lab tasks, and references)
into lab_system/lab_manual_index.json and extracts the MCS and NUST crests into lab_system/assets/.
"""

import argparse
import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MANUAL_DOCX = BASE_DIR / "CS-370_Artificial_Intelligence_Lab_Manual_Updated_2026.docx"
ASSETS_DIR = Path(__file__).resolve().parent / "assets"
INDEX_JSON = Path(__file__).resolve().parent / "lab_manual_index.json"

CLO_MAP = {
    1: "1, 4",
    2: "1",
    3: "1, 4",
    4: "1, 3, 4",
    5: "1, 3, 4",
    6: "1, 3, 4",
    7: "1, 4",
    8: "1, 3, 4",
    9: "1, 4",
    10: "1, 3, 4",
    11: "1, 4",
    12: "1, 3, 4",
    13: "1, 3, 4",
    14: "1, 3, 4",
    15: "1, 2, 4",
}


def extract_assets_and_lines(docx_path: Path = MANUAL_DOCX) -> list[str]:
    """Extract logos to assets/ and return all paragraph texts from the manual."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(docx_path, "r") as zf:
        if "word/media/image1.jpeg" in zf.namelist():
            (ASSETS_DIR / "mcs_logo.jpeg").write_bytes(zf.read("word/media/image1.jpeg"))
        if "word/media/image2.jpeg" in zf.namelist():
            (ASSETS_DIR / "nust_logo.jpeg").write_bytes(zf.read("word/media/image2.jpeg"))
        xml_bytes = zf.read("word/document.xml")

    tree = ET.fromstring(xml_bytes)
    ns_p = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"
    ns_t = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t"

    paragraphs: list[str] = []
    for p in tree.iter(ns_p):
        texts = [t.text for t in p.iter(ns_t) if t.text]
        if texts:
            line = "".join(texts).strip()
            if line:
                paragraphs.append(line)
    return paragraphs


def parse_manual(docx_path: Path = MANUAL_DOCX) -> dict:
    """Parse all 15 labs from the manual into a structured dictionary."""
    lines = extract_assets_and_lines(docx_path)

    # Locate the actual Lab sections (skip the Table of Contents entries which end in page numbers)
    lab_header_re = re.compile(r"^Lab\s*#\s*(\d+)\s*:\s*(.+)$")
    lab_starts: list[tuple[int, int, str]] = []

    for idx, line in enumerate(lines):
        m = lab_header_re.match(line)
        if m:
            lab_num = int(m.group(1))
            title = m.group(2).strip()
            # Table of contents entries end with page digits like "...Programming8"
            if re.search(r"[a-zA-Z\*]\d+$", title):
                continue
            lab_starts.append((idx, lab_num, title))

    labs_data: dict[str, dict] = {}
    for i, (start_idx, lab_num, title) in enumerate(lab_starts):
        end_idx = lab_starts[i + 1][0] if i + 1 < len(lab_starts) else len(lines)
        chunk = lines[start_idx + 1 : end_idx]

        # Clean trailing Midterm banner if present inside Lab 8
        cleaned_chunk = []
        for c in chunk:
            if c.startswith("MID TERM PRACTICAL EXAMINATION") or c.startswith("Covers Labs 1-8:"):
                continue
            cleaned_chunk.append(c)
        chunk = cleaned_chunk

        time_req = "3 hrs"
        prog_lang = "Python 3"
        software_req = "Anaconda / Google Colab"
        objective = ""

        # Parse metadata header lines
        cursor = 0
        while cursor < len(chunk):
            line = chunk[cursor]
            if line == "Time Required" and cursor + 2 < len(chunk) and chunk[cursor + 1] == ":":
                time_req = chunk[cursor + 2]
                cursor += 3
                continue
            if line == "Programming Language" and cursor + 2 < len(chunk) and chunk[cursor + 1] == ":":
                prog_lang = chunk[cursor + 2]
                cursor += 3
                continue
            if line == "Software Required" and cursor + 2 < len(chunk) and chunk[cursor + 1] == ":":
                software_req = chunk[cursor + 2]
                cursor += 3
                continue
            if line.startswith("Objective:"):
                objective = line.removeprefix("Objective:").strip()
                cursor += 1
                break
            cursor += 1

        body_lines = chunk[cursor:]

        # Segment body into Theory/Implementation, Lab Task, and References
        section = "theory_and_implementation"
        theory_impl_lines: list[str] = []
        task_lines: list[str] = []
        ref_lines: list[str] = []

        for bline in body_lines:
            if bline in ("Lab Task", "Project Requirements"):
                section = "tasks"
                continue
            elif bline == "References":
                section = "references"
                continue

            if section == "theory_and_implementation":
                theory_impl_lines.append(bline)
            elif section == "tasks":
                task_lines.append(bline)
            elif section == "references":
                ref_lines.append(bline)

        # Group individual tasks nicely
        parsed_tasks: list[str] = []
        for tline in task_lines:
            if re.match(r"^(Task\s*\d+|1\.|2\.|3\.|4\.|5\.)", tline):
                parsed_tasks.append(tline)
            elif parsed_tasks:
                parsed_tasks[-1] += "\n   " + tline
            else:
                parsed_tasks.append(tline)

        labs_data[str(lab_num)] = {
            "lab_number": lab_num,
            "title": title,
            "full_heading": f"Lab # {lab_num}: {title}",
            "clos": CLO_MAP.get(lab_num, "1, 4"),
            "time_required": time_req,
            "programming_language": prog_lang,
            "software_required": software_req,
            "objective": objective,
            "tasks": parsed_tasks,
            "raw_task_lines": task_lines,
            "theory_and_implementation": theory_impl_lines,
            "references": ref_lines,
        }

    index_payload = {
        "course_code": "CS-370",
        "course_title": "Artificial Intelligence",
        "institution": "Military College of Signals (NUST)",
        "department": "Department of Computer Software Engineering",
        "default_student": {
            "submitted_to": "Lec Shehla",
            "submitted_by": "GC HAMMAD LATIF",
            "cms_id": "534740",
            "class_section": "BESE 30B",
        },
        "total_labs": len(labs_data),
        "labs": labs_data,
    }

    INDEX_JSON.write_text(json.dumps(index_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return index_payload


def format_lab_summary(lab_info: dict) -> str:
    """Return a clean Markdown summary of a lab for chat display."""
    out = [
        f"# {lab_info['full_heading']}",
        f"- **Course:** CS-370 — Artificial Intelligence | **CLOs:** {lab_info['clos']}",
        f"- **Time Required:** {lab_info['time_required']} | **Software:** {lab_info['software_required']}",
        "",
        "## Objective",
        lab_info["objective"],
        "",
        "## Lab Tasks to Implement",
    ]
    for i, t in enumerate(lab_info["tasks"], 1):
        out.append(f"- {t}")
    if lab_info["references"]:
        out.append("")
        out.append("## References")
        for r in lab_info["references"]:
            out.append(f"- {r}")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="CS-370 AI Lab Manual Parser & Lookup Tool")
    parser.add_argument("--lab", type=int, help="Lab number (1-15) to display")
    parser.add_argument("--list", action="store_true", help="List all 15 labs")
    args = parser.parse_args()

    if not INDEX_JSON.exists():
        index = parse_manual()
    else:
        index = json.loads(INDEX_JSON.read_text(encoding="utf-8"))

    if args.list:
        print(f"CS-370 AI Lab Manual — {index['total_labs']} Labs Indexed:")
        for k, v in index["labs"].items():
            print(f"  Lab #{k:>2}: {v['title']} (CLOs: {v['clos']}, Tasks: {len(v['tasks'])})")
    elif args.lab:
        lab_key = str(args.lab)
        if lab_key not in index["labs"]:
            print(f"Error: Lab #{args.lab} not found. Valid labs are 1..15.")
            return
        print(format_lab_summary(index["labs"][lab_key]))
    else:
        index = parse_manual()
        print(f"Successfully parsed {index['total_labs']} labs into {INDEX_JSON}")
        print(f"Extracted logos into {ASSETS_DIR}")


if __name__ == "__main__":
    main()
