"""
CS-370 AI Lab Report Generator (.docx + .ipynb + .py + 2x Colab Screenshots).
Uses clean, natural Word paragraphs and subtle left-border accents (matching demo lab.docx)
with NUST Royal Navy (#0F2C59) & Executive Teal (#0D9488) typography — zero boxy 1x1 card tables
or special box-drawing characters.
"""

import argparse
import importlib
import json
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor

from lab_system.colab_renderer import (
    DOCX_SYNTAX_HEX,
    execute_task_code,
    render_colab_screenshot,
    tokenize_code_lines,
)
from lab_system.manual_parser import BASE_DIR, INDEX_JSON, parse_manual

# Clean Academic Palette
NAVY_HEX = "0F2C59"
TEAL_HEX = "0D9488"
SLATE_TEXT_HEX = "1E293B"
MUTED_TEXT_HEX = "475569"
BORDER_HEX = "CBD5E1"
TABLE_LABEL_BG = "F1F5F9"
CODE_SHADING_HEX = "F8FAFC"

RGB_NAVY = RGBColor(0x0F, 0x2C, 0x59)
RGB_TEAL = RGBColor(0x0D, 0x94, 0x88)
RGB_SLATE = RGBColor(0x1E, 0x29, 0x3B)
RGB_MUTED = RGBColor(0x47, 0x55, 0x69)
RGB_BLACK = RGBColor(0x00, 0x00, 0x00)
RGB_WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def hex_to_rgb(hex_str: str) -> RGBColor:
    h = hex_str.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def set_cell_shading(cell, fill_hex: str):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def set_cell_margins(cell, top=90, bottom=90, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for side, val in [("top", top), ("bottom", bottom), ("left", left), ("right", right)]:
        node = OxmlElement(f"w:{side}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table, color="CBD5E1", sz="6"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="single" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f"</w:tblBorders>"
    )
    tblPr.append(borders)


def set_paragraph_left_accent(paragraph, color_hex: str, sz: int = 12, fill_hex: str | None = None):
    """Apply a clean left border line (like demo lab.docx) to a code or output paragraph."""
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), str(sz))
    left.set(qn("w:space"), "8")
    left.set(qn("w:color"), color_hex)
    pBdr.append(left)
    pPr.append(pBdr)
    if fill_hex:
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        pPr.append(shd)


def set_paragraph_bottom_rule(paragraph, color_hex: str = TEAL_HEX, sz: int = 8):
    """Add a clean bottom underline rule to a section heading paragraph."""
    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(sz))
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), color_hex)
    pBdr.append(bottom)
    pPr.append(pBdr)


def configure_document_styles(doc: Document):
    """Configure page margins and clean Calibri/Segoe UI typography."""
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)
    section.page_width = Inches(8.5)
    section.page_height = Inches(11.0)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Calibri"
    normal_style.font.size = Pt(11)
    normal_style.font.color.rgb = RGB_SLATE


def add_header_and_metadata(doc: Document, lab_num: int, lab_title: str, student: dict):
    """
    Build the clean centered title block and 4x2 metadata table matching demo lab.docx,
    accented with NUST Royal Navy & Teal colors.
    """
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(4)
    p_inst.paragraph_format.space_after = Pt(2)
    r_inst = p_inst.add_run("MILITARY COLLEGE OF SIGNALS")
    r_inst.font.name = "Calibri"
    r_inst.font.size = Pt(16)
    r_inst.font.bold = True
    r_inst.font.color.rgb = RGB_NAVY

    p_course = doc.add_paragraph()
    p_course.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_course.paragraph_format.space_before = Pt(2)
    p_course.paragraph_format.space_after = Pt(2)
    r_course = p_course.add_run("CS-370 - Artificial Intelligence")
    r_course.font.name = "Calibri"
    r_course.font.size = Pt(14)
    r_course.font.bold = True
    r_course.font.color.rgb = RGB_TEAL

    p_lab = doc.add_paragraph()
    p_lab.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_lab.paragraph_format.space_before = Pt(2)
    p_lab.paragraph_format.space_after = Pt(10)
    r_lab = p_lab.add_run(f"Lab # {lab_num}: {lab_title}")
    r_lab.font.name = "Calibri"
    r_lab.font.size = Pt(14)
    r_lab.font.bold = True
    r_lab.font.color.rgb = RGB_NAVY

    # 4x2 Student Metadata Table (just like demo lab.docx)
    meta_rows = [
        ("SUBMITTED TO", student["submitted_to"]),
        ("SUBMITTED BY", student["submitted_by"]),
        ("CMS ID", student["cms_id"]),
        ("CLASS", student["class_section"]),
    ]
    tbl = doc.add_table(rows=4, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl, color=BORDER_HEX, sz="6")

    for r_idx, (label, val) in enumerate(meta_rows):
        c_label, c_val = tbl.rows[r_idx].cells
        c_label.width = Inches(3.2)
        c_val.width = Inches(3.6)
        set_cell_shading(c_label, TABLE_LABEL_BG)
        set_cell_margins(c_label, top=75, bottom=75, left=140, right=140)
        set_cell_margins(c_val, top=75, bottom=75, left=140, right=140)

        pl = c_label.paragraphs[0]
        pl.paragraph_format.space_before = Pt(0)
        pl.paragraph_format.space_after = Pt(0)
        rl = pl.add_run(label)
        rl.font.name = "Calibri"
        rl.font.size = Pt(10.5)
        rl.font.bold = True
        rl.font.color.rgb = RGB_NAVY

        pv = c_val.paragraphs[0]
        pv.paragraph_format.space_before = Pt(0)
        pv.paragraph_format.space_after = Pt(0)
        rv = pv.add_run(val)
        rv.font.name = "Calibri"
        rv.font.size = Pt(10.5)
        rv.font.bold = True
        rv.font.color.rgb = RGB_SLATE

    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(4)
    sp.paragraph_format.space_after = Pt(4)


def add_section_heading(doc: Document, text: str):
    """Add a clean Heading 1 with a subtle bottom Teal rule (no boxes)."""
    p = doc.add_paragraph(style="Heading 1")
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    set_paragraph_bottom_rule(p, color_hex=TEAL_HEX, sz=6)

    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = RGB_NAVY


def add_sub_label(doc: Document, label_text: str, color_rgb: RGBColor = RGB_NAVY):
    """Add a clean bold underlined sub-label ('Code', 'Output', 'Analysis') like demo lab.docx."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(label_text)
    r.font.name = "Calibri"
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.underline = True
    r.font.color.rgb = color_rgb


def add_body_paragraph(doc: Document, label_prefix: str | None, text: str):
    """Add a normal, unboxed paragraph of explanatory text."""
    if not text or not text.strip():
        return
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(3)
    p.paragraph_format.space_after = Pt(5)
    p.paragraph_format.line_spacing = 1.15
    if label_prefix:
        rp = p.add_run(label_prefix + ": ")
        rp.font.name = "Calibri"
        rp.font.size = Pt(10.5)
        rp.font.bold = True
        rp.font.color.rgb = RGB_NAVY
    rb = p.add_run(text.strip())
    rb.font.name = "Calibri"
    rb.font.size = Pt(10.5)
    rb.font.color.rgb = RGB_SLATE


def add_code_paragraphs(doc: Document, code: str):
    """
    Add syntax-colored code lines using clean paragraph left-borders (like demo lab.docx)
    without any table boxes or special Unicode box-drawing characters.
    """
    add_sub_label(doc, "Code", RGB_NAVY)
    tokenized_lines = tokenize_code_lines(code.strip("\n"))
    for spans in tokenized_lines:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.05
        set_paragraph_left_accent(p, color_hex="2E74B5", sz=12)

        if not spans:
            r_empty = p.add_run(" ")
            r_empty.font.name = "Consolas"
            r_empty.font.size = Pt(9)
            continue

        for seg_text, cat in spans:
            r_seg = p.add_run(seg_text)
            r_seg.font.name = "Consolas"
            r_seg.font.size = Pt(9)
            hex_color = DOCX_SYNTAX_HEX.get(cat, "1E293B")
            r_seg.font.color.rgb = hex_to_rgb(hex_color)
            if cat in ("kw_control", "kw_decl"):
                r_seg.font.bold = True


def add_output_paragraphs(doc: Document, output_text: str):
    """
    Add console output lines using a clean green/teal left paragraph border (like demo lab.docx)
    without any table boxes.
    """
    if not output_text or not output_text.strip():
        return
    add_sub_label(doc, "Output", RGB_TEAL)
    for line in output_text.strip("\n").splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.05
        set_paragraph_left_accent(p, color_hex=TEAL_HEX, sz=12)

        r = p.add_run(line if line else " ")
        r.font.name = "Consolas"
        r.font.size = Pt(9)
        r.font.color.rgb = RGB_SLATE


def add_unboxed_screenshot(doc: Document, img_path: Path):
    """Insert the Google Colab screenshot directly as a clean paragraph (no outer box table)."""
    if not img_path.exists():
        return
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(10)
    p.add_run().add_picture(str(img_path), width=Inches(6.6))


def add_data_table(doc: Document, headers: list[str], rows: list[list[str]], title: str | None = None):
    """Add a clean comparison table when a task specifically requires tabular results."""
    if title:
        tp = doc.add_paragraph()
        tp.paragraph_format.space_before = Pt(8)
        tp.paragraph_format.space_after = Pt(3)
        tp.paragraph_format.keep_with_next = True
        tr = tp.add_run(title)
        tr.font.name = "Calibri"
        tr.font.size = Pt(10.5)
        tr.font.bold = True
        tr.font.color.rgb = RGB_NAVY

    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tbl, color=BORDER_HEX, sz="6")

    for c_idx, h_text in enumerate(headers):
        cell = tbl.rows[0].cells[c_idx]
        set_cell_shading(cell, NAVY_HEX)
        set_cell_margins(cell, top=70, bottom=70, left=100, right=100)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(str(h_text))
        r.font.name = "Calibri"
        r.font.size = Pt(9.5)
        r.font.bold = True
        r.font.color.rgb = RGB_WHITE

    for r_idx, r_data in enumerate(rows):
        bg = "FFFFFF" if r_idx % 2 == 0 else TABLE_LABEL_BG
        for c_idx, val in enumerate(r_data):
            cell = tbl.rows[r_idx + 1].cells[c_idx]
            set_cell_shading(cell, bg)
            set_cell_margins(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(val))
            r.font.name = "Calibri"
            r.font.size = Pt(9.5)
            if c_idx == 0:
                r.font.bold = True
                r.font.color.rgb = RGB_NAVY
            else:
                r.font.color.rgb = RGB_SLATE


def export_colab_notebook(spec: dict, executed_tasks: list[dict], out_ipynb: Path, bundle_name: str):
    """Export a valid Google Colab / Jupyter .ipynb file with Open-in-Colab badge."""
    colab_link = f"https://colab.research.google.com/github/Hammad271618/CS-370-Artificial-Intelligence-Labs/blob/main/reports/{bundle_name}/{out_ipynb.name}"

    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                f"[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({colab_link})\n\n",
                f"# CS-370 - Artificial Intelligence\n",
                f"## Lab # {spec['lab_number']}: {spec['title']}\n",
                f"**Submitted To:** {spec['student']['submitted_to']}  \n",
                f"**Submitted By:** {spec['student']['submitted_by']} (`{spec['student']['cms_id']}`)  \n",
                f"**Class:** {spec['student']['class_section']}\n",
                "---\n",
                f"### Objective\n",
                f"{spec['objective']}\n",
            ],
        }
    ]

    for idx, t in enumerate(executed_tasks, 1):
        cells.append(
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"## Task {idx} - {t['title']}\n",
                    f"{t.get('problem_statement', '')}\n",
                ],
            }
        )
        code_lines = [line + "\n" for line in t["code"].strip("\n").splitlines()]
        out_lines = [line + "\n" for line in t["output"].splitlines()] if t["output"] else []
        cells.append(
            {
                "cell_type": "code",
                "execution_count": idx,
                "metadata": {},
                "outputs": (
                    [
                        {
                            "name": "stdout",
                            "output_type": "stream",
                            "text": out_lines,
                        }
                    ]
                    if out_lines
                    else []
                ),
                "source": code_lines,
            }
        )
        if t.get("analysis"):
            cells.append(
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [
                        f"### Analysis (Task {idx})\n",
                        f"{t['analysis']}\n",
                    ],
                }
            )

    nb_payload = {
        "cells": cells,
        "metadata": {
            "colab": {"name": out_ipynb.name, "provenance": []},
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    out_ipynb.write_text(json.dumps(nb_payload, indent=2, ensure_ascii=False), encoding="utf-8")


def export_python_script(spec: dict, executed_tasks: list[dict], out_py: Path):
    """Export a clean, well-commented .py script containing all tasks for the lab."""
    blocks = [
        '"""',
        f"MILITARY COLLEGE OF SIGNALS (NUST)",
        f"CS-370 - Artificial Intelligence",
        f"Lab # {spec['lab_number']}: {spec['title']}",
        f"Submitted To : {spec['student']['submitted_to']}",
        f"Submitted By : {spec['student']['submitted_by']} (CMS ID: {spec['student']['cms_id']})",
        f"Class        : {spec['student']['class_section']}",
        '"""',
        "",
    ]
    for idx, t in enumerate(executed_tasks, 1):
        blocks.append("# " + "=" * 74)
        blocks.append(f"# Task {idx} - {t['title']}")
        blocks.append("# " + "=" * 74)
        blocks.append(t["code"].strip("\n"))
        blocks.append("")
    out_py.write_text("\n".join(blocks), encoding="utf-8")


def generate_lab_bundle(spec: dict) -> dict[str, Path]:
    """
    Execute all tasks in `spec`, render 2x Google Colab Dark-Mode screenshots,
    and build the complete submission bundle (.docx, .ipynb, .py, screenshots/).
    """
    if not INDEX_JSON.exists():
        parse_manual()
    manual_index = json.loads(INDEX_JSON.read_text(encoding="utf-8"))

    lab_num = int(spec["lab_number"])
    manual_lab = manual_index["labs"].get(str(lab_num), {})
    title = spec.get("title") or manual_lab.get("title", f"Lab {lab_num}")
    title = title.replace("—", "-").replace("–", "-")
    clos = spec.get("clos") or manual_lab.get("clos", "1, 4")
    objective = spec.get("objective") or manual_lab.get("objective", "")
    student = {**manual_index["default_student"], **spec.get("student", {})}

    slug = spec.get("slug") or re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")[:36]
    bundle_dir = BASE_DIR / "reports" / f"Lab_{lab_num:02d}_{slug}"
    screenshots_dir = bundle_dir / "screenshots"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    spec_resolved = {
        **spec,
        "lab_number": lab_num,
        "title": title,
        "clos": clos,
        "objective": objective,
        "student": student,
    }

    # 1. Execute tasks and render Colab Dark-Mode screenshots
    shared_ns = {"__name__": "__main__"}
    executed_tasks = []

    for idx, task in enumerate(spec["tasks"], 1):
        code = task["code"].strip("\n")
        if task.get("execute", True):
            stdout_text, elapsed_sec, shared_ns = execute_task_code(code, shared_ns)
            output_text = task.get("custom_output") or stdout_text
        else:
            output_text = task.get("custom_output", "")
            elapsed_sec = task.get("elapsed_sec", 0.2)

        extra_img_path = None
        if callable(task.get("plot_hook")):
            extra_img_path = screenshots_dir / f"task_{idx:02d}_plot.png"
            task["plot_hook"](shared_ns, extra_img_path)

        colab_png = screenshots_dir / f"task_{idx:02d}_colab.png"
        render_colab_screenshot(
            code=code,
            output_text=output_text,
            cell_index=idx,
            elapsed_sec=elapsed_sec,
            out_path=colab_png,
            extra_image_path=extra_img_path,
        )

        executed_tasks.append(
            {
                **task,
                "code": code,
                "output": output_text,
                "elapsed_sec": elapsed_sec,
                "colab_png": colab_png,
                "extra_img_path": extra_img_path,
            }
        )

    # 2. Build Clean, Box-Free Word Document (.docx)
    doc = Document()
    configure_document_styles(doc)
    add_header_and_metadata(doc, lab_num, title, student)

    if objective:
        add_body_paragraph(doc, "Objective", objective)

    for idx, t in enumerate(executed_tasks, 1):
        task_title = t["title"].replace("—", "-")
        add_section_heading(doc, f"Task {idx} - {task_title}")

        if t.get("problem_statement"):
            add_body_paragraph(doc, None, t["problem_statement"])

        add_code_paragraphs(doc, t["code"])
        add_output_paragraphs(doc, t["output"])
        add_unboxed_screenshot(doc, t["colab_png"])

        if t.get("table"):
            tbl_spec = t["table"]
            add_data_table(
                doc,
                headers=tbl_spec["headers"],
                rows=tbl_spec["rows"],
                title=tbl_spec.get("title"),
            )

        if t.get("analysis"):
            add_body_paragraph(doc, "Analysis", t["analysis"])

    if spec.get("conclusion"):
        add_section_heading(doc, "Conclusion")
        add_body_paragraph(doc, None, spec["conclusion"])

    docx_path = bundle_dir / f"Lab_{lab_num:02d}_{slug}_Report_{student['cms_id']}.docx"
    ipynb_path = bundle_dir / f"Lab_{lab_num:02d}_{slug}.ipynb"
    py_path = bundle_dir / f"Lab_{lab_num:02d}_{slug}.py"

    doc.save(str(docx_path))
    export_colab_notebook(spec_resolved, executed_tasks, ipynb_path, bundle_dir.name)
    export_python_script(spec_resolved, executed_tasks, py_path)

    colab_url = (
        f"https://colab.research.google.com/github/Hammad271618/CS-370-Artificial-Intelligence-Labs"
        f"/blob/main/reports/{bundle_dir.name}/{ipynb_path.name}"
    )

    return {
        "bundle_dir": bundle_dir,
        "docx": docx_path,
        "ipynb": ipynb_path,
        "py": py_path,
        "screenshots_dir": screenshots_dir,
        "colab_url": colab_url,
    }


def main():
    parser = argparse.ArgumentParser(description="Generate CS-370 AI Lab Report Bundle")
    parser.add_argument("--lab", type=int, required=True, help="Lab number (1-15)")
    args = parser.parse_args()

    mod_name = f"lab_system.specs.lab_{args.lab:02d}"
    try:
        mod = importlib.import_module(mod_name)
    except ModuleNotFoundError as exc:
        raise SystemExit(
            f"Specification module '{mod_name}' not found. Create lab_system/specs/lab_{args.lab:02d}.py first."
        ) from exc

    paths = generate_lab_bundle(mod.LAB_SPEC)
    print(f"=== Lab #{args.lab:02d} Bundle Successfully Generated ===")
    for k, v in paths.items():
        print(f"  {k:<16}: {v}")


if __name__ == "__main__":
    main()
