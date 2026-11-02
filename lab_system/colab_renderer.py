"""
Google Colab Dark-Mode Cell Executor & 2x Retina Screenshot Renderer.
Also provides Python syntax tokenization used by both the Colab screenshot renderer
and the Word (.docx) syntax-highlighted code block builder.
"""

import io
import keyword
import math
import time
import tokenize
from contextlib import redirect_stdout
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Authentic Google Colab / VS Code Dark+ palette
COLAB_COLORS = {
    "canvas_bg": (23, 23, 23),         # #171717 outer notebook background
    "editor_bg": (30, 30, 30),         # #1E1E1E code cell background
    "output_bg": (25, 25, 25),         # #191919 output cell background
    "border": (60, 64, 67),            # #3C4043 cell border
    "divider": (45, 45, 45),           # #2D2D2D divider & 80-col ruler
    "gutter_text": (154, 160, 166),    # #9AA0A6 [1], 0s, icons
    "check_green": (52, 168, 83),      # #34A853 green checkmark
    "play_circle": (209, 213, 219),    # #D1D5DB play button circle
    "play_triangle": (30, 30, 30),     # #1E1E1E play triangle
    "output_text": (232, 234, 237),    # #E8EAED stdout text
    # Syntax token colors (Dark+)
    "kw_control": (197, 134, 192),     # #C586C0 import, from, return, if, else, for, while
    "kw_decl": (86, 156, 214),         # #569CD6 def, class, True, False, None, and, or, not, in
    "builtin": (220, 220, 170),        # #DCDCAA print, len, sum, range, max, min, func calls
    "string": (206, 145, 120),         # #CE9178 string literals & docstrings
    "number": (181, 206, 168),         # #B5CEA8 numeric literals
    "comment": (106, 153, 85),         # #6A9955 comments
    "identifier": (156, 220, 254),     # #9CDCFE variables / parameters
    "operator": (212, 212, 212),       # #D4D4D4 punctuation & operators
}

# Light-theme syntax palette for Word (.docx) code blocks
DOCX_SYNTAX_HEX = {
    "kw_control": "AF00DB",   # Purple
    "kw_decl": "0000FF",      # Royal Blue
    "builtin": "795E26",      # Golden Brown
    "string": "A31515",       # Brick Red
    "number": "098658",       # Emerald Green
    "comment": "008000",      # Forest Green
    "identifier": "0F2C59",   # Deep Navy
    "operator": "334155",     # Slate
}

CONTROL_KEYWORDS = {
    "import", "from", "as", "if", "elif", "else", "for", "while",
    "return", "try", "except", "finally", "with", "raise", "break",
    "continue", "pass", "yield", "assert",
}

DECL_KEYWORDS = {
    "def", "class", "lambda", "True", "False", "None",
    "and", "or", "not", "in", "is", "global", "nonlocal", "del",
}

BUILTINS = {
    "print", "len", "sum", "sorted", "range", "max", "min", "abs",
    "int", "float", "str", "list", "dict", "set", "tuple", "bool",
    "enumerate", "any", "all", "round", "open", "zip", "map", "filter",
    "type", "isinstance", "reversed", "pow",
}


def tokenize_code_lines(code: str) -> list[list[tuple[str, str]]]:
    """
    Tokenize Python source into per-line list of (text_segment, token_category).
    Categories: kw_control, kw_decl, builtin, string, number, comment, identifier, operator.
    """
    raw_lines = code.splitlines()
    if not raw_lines:
        return [[]]

    # Build character-level category map per line (1-indexed for tokenize)
    line_cats: list[list[str]] = [
        ["operator"] * len(line) for line in raw_lines
    ]

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
    except tokenize.TokenError:
        tokens = []

    for idx, tok in enumerate(tokens):
        ttype, tstr, (srow, scol), (erow, ecol), _ = tok
        cat = "operator"
        if ttype == tokenize.COMMENT:
            cat = "comment"
        elif ttype == tokenize.STRING:
            cat = "string"
        elif ttype == tokenize.NUMBER:
            cat = "number"
        elif ttype == tokenize.NAME:
            if tstr in CONTROL_KEYWORDS:
                cat = "kw_control"
            elif tstr in DECL_KEYWORDS or keyword.iskeyword(tstr):
                cat = "kw_decl"
            elif tstr in BUILTINS:
                cat = "builtin"
            else:
                # Check if preceded by 'def'/'class' or followed by '('
                prev_tok = tokens[idx - 1] if idx > 0 else None
                next_tok = tokens[idx + 1] if idx + 1 < len(tokens) else None
                if prev_tok and prev_tok.string in ("def", "class"):
                    cat = "builtin"
                elif next_tok and next_tok.string == "(":
                    cat = "builtin"
                else:
                    cat = "identifier"

        for r in range(srow, erow + 1):
            if 1 <= r <= len(raw_lines):
                line_len = len(raw_lines[r - 1])
                c_start = scol if r == srow else 0
                c_end = ecol if r == erow else line_len
                for c in range(max(0, c_start), min(line_len, c_end)):
                    line_cats[r - 1][c] = cat

    # Merge contiguous characters with the same category on each line
    result: list[list[tuple[str, str]]] = []
    for line_idx, line in enumerate(raw_lines):
        if not line:
            result.append([])
            continue
        cats = line_cats[line_idx]
        spans: list[tuple[str, str]] = []
        cur_cat = cats[0]
        cur_chars = [line[0]]
        for ch, c in zip(line[1:], cats[1:]):
            if c == cur_cat:
                cur_chars.append(ch)
            else:
                spans.append(("".join(cur_chars), cur_cat))
                cur_cat = c
                cur_chars = [ch]
        spans.append(("".join(cur_chars), cur_cat))
        result.append(spans)

    return result


def execute_task_code(code: str, shared_ns: dict | None = None) -> tuple[str, float, dict]:
    """Execute Python code in shared_ns, returning (stdout_text, elapsed_seconds, shared_ns)."""
    if shared_ns is None:
        shared_ns = {"__name__": "__main__"}
    buf = io.StringIO()
    t0 = time.perf_counter()
    with redirect_stdout(buf):
        exec(compile(code, "<colab_cell>", "exec"), shared_ns)
    elapsed = time.perf_counter() - t0
    return buf.getvalue().rstrip("\n"), elapsed, shared_ns


def _load_font(names: list[str], size: int) -> ImageFont.FreeTypeFont:
    fonts_dir = Path(r"C:\Windows\Fonts")
    for name in names:
        fp = fonts_dir / name
        if fp.exists():
            return ImageFont.truetype(str(fp), size=size)
    return ImageFont.load_default()


def render_colab_screenshot(
    code: str,
    output_text: str,
    cell_index: int,
    elapsed_sec: float,
    out_path: Path,
    extra_image_path: Path | None = None,
) -> Path:
    """
    Render a crisp 2x Retina Google Colab Dark-Mode cell screenshot containing:
    - Left gutter with [cell_index], green checkmark, and execution time (e.g. 0s / 1s)
    - Play button icon at top-left of code editor
    - Syntax-highlighted code with 80-col vertical ruler line
    - Output tray with collapse chevron, ellipsis menu icon, console stdout, and optional plot image
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 2x Retina dimensions
    width = 1650
    gutter_w = 88
    right_margin = 28
    top_margin = 22
    bottom_margin = 22
    card_x0 = gutter_w
    card_x1 = width - right_margin

    font_code = _load_font(["consola.ttf"], 24)
    font_ui = _load_font(["segoeui.ttf", "consola.ttf"], 21)
    font_ui_sm = _load_font(["segoeui.ttf", "consola.ttf"], 19)

    # Measure character width & line height
    bbox = font_code.getbbox("M")
    char_w = bbox[2] - bbox[0]
    line_h = 34

    code_lines_tokens = tokenize_code_lines(code.strip("\n"))
    output_lines = output_text.splitlines() if output_text.strip() else []

    code_pad_top = 26
    code_pad_bottom = 26
    code_x_start = card_x0 + 74  # space for play button inside cell

    code_section_h = max(76, code_pad_top + len(code_lines_tokens) * line_h + code_pad_bottom)

    # Check if there is an extra plot/diagram image to embed in the output pane
    embedded_img = None
    embedded_img_h = 0
    if extra_image_path and Path(extra_image_path).exists():
        embedded_img = Image.open(extra_image_path).convert("RGBA")
        max_img_w = (card_x1 - code_x_start) - 40
        if embedded_img.width > max_img_w:
            ratio = max_img_w / embedded_img.width
            embedded_img = embedded_img.resize(
                (int(embedded_img.width * ratio), int(embedded_img.height * ratio)),
                Image.Resampling.LANCZOS,
            )
        embedded_img_h = embedded_img.height + 24

    has_output = bool(output_lines) or embedded_img is not None
    out_pad_top = 22 if has_output else 0
    out_pad_bottom = 24 if has_output else 0
    output_section_h = (
        out_pad_top + len(output_lines) * line_h + embedded_img_h + out_pad_bottom
        if has_output
        else 0
    )

    total_card_h = code_section_h + output_section_h
    height = top_margin + total_card_h + bottom_margin

    img = Image.new("RGB", (width, height), COLAB_COLORS["canvas_bg"])
    draw = ImageDraw.Draw(img)

    card_y0 = top_margin
    card_y1 = card_y0 + total_card_h
    divider_y = card_y0 + code_section_h

    # Draw cell background (rounded rectangle)
    draw.rounded_rectangle(
        [card_x0, card_y0, card_x1, card_y1],
        radius=14,
        fill=COLAB_COLORS["editor_bg"],
        outline=COLAB_COLORS["border"],
        width=2,
    )

    # If output exists, draw output pane background at bottom half of card
    if has_output:
        draw.rounded_rectangle(
            [card_x0 + 2, divider_y, card_x1 - 2, card_y1 - 2],
            radius=12,
            fill=COLAB_COLORS["output_bg"],
        )
        # Cover top corners of output pane so divider is straight
        draw.rectangle(
            [card_x0 + 2, divider_y, card_x1 - 2, min(divider_y + 16, card_y1 - 2)],
            fill=COLAB_COLORS["output_bg"],
        )
        # Horizontal divider line
        draw.line(
            [(card_x0, divider_y), (card_x1, divider_y)],
            fill=COLAB_COLORS["divider"],
            width=2,
        )

    # Draw 80-column ruler line inside code editor
    ruler_x = code_x_start + int(80 * char_w)
    if ruler_x < card_x1 - 20:
        draw.line(
            [(ruler_x, card_y0 + 2), (ruler_x, divider_y - 2)],
            fill=COLAB_COLORS["divider"],
            width=2,
        )

    # Left gutter: [cell_index] and green checkmark + elapsed seconds
    bracket_label = f"[{cell_index}]"
    draw.text((20, card_y0 + 16), bracket_label, fill=COLAB_COLORS["gutter_text"], font=font_ui)

    # Green checkmark icon (drawn geometrically for crispness)
    cx, cy = 22, card_y0 + 56
    draw.line([(cx, cy + 7), (cx + 6, cy + 13), (cx + 16, cy + 1)], fill=COLAB_COLORS["check_green"], width=3)
    sec_int = max(0, int(round(elapsed_sec)))
    draw.text((cx + 23, card_y0 + 49), f"{sec_int}s", fill=COLAB_COLORS["gutter_text"], font=font_ui_sm)

    # Play button circle inside top-left of code cell
    play_cx = card_x0 + 36
    play_cy = card_y0 + 36
    play_r = 16
    draw.ellipse(
        [play_cx - play_r, play_cy - play_r, play_cx + play_r, play_cy + play_r],
        fill=COLAB_COLORS["play_circle"],
    )
    draw.polygon(
        [
            (play_cx - 5, play_cy - 8),
            (play_cx - 5, play_cy + 8),
            (play_cx + 8, play_cy),
        ],
        fill=COLAB_COLORS["play_triangle"],
    )

    # Render syntax-highlighted code lines
    for row_idx, spans in enumerate(code_lines_tokens):
        y = card_y0 + code_pad_top + row_idx * line_h
        x = code_x_start
        for segment, cat in spans:
            color = COLAB_COLORS.get(cat, COLAB_COLORS["operator"])
            draw.text((x, y), segment, fill=color, font=font_code)
            seg_box = font_code.getbbox(segment)
            x += seg_box[2] - seg_box[0]

    # Render output pane icons & stdout text
    if has_output:
        # Left gutter chevron 'v'
        chev_x, chev_y = 32, divider_y + 28
        draw.line(
            [(chev_x - 6, chev_y - 3), (chev_x, chev_y + 3), (chev_x + 6, chev_y - 3)],
            fill=COLAB_COLORS["gutter_text"],
            width=3,
        )
        # Three dots menu icon inside output pane
        dots_cx = card_x0 + 36
        dots_cy = divider_y + 30
        for dx in (-7, 0, 7):
            draw.ellipse(
                [dots_cx + dx - 2, dots_cy - 2, dots_cx + dx + 2, dots_cy + 2],
                fill=COLAB_COLORS["gutter_text"],
            )

        out_y = divider_y + out_pad_top
        for oline in output_lines:
            draw.text(
                (code_x_start, out_y),
                oline,
                fill=COLAB_COLORS["output_text"],
                font=font_code,
            )
            out_y += line_h

        if embedded_img is not None:
            out_y += 10
            img.paste(embedded_img, (code_x_start, out_y), embedded_img)

    img.save(out_path, format="PNG", optimize=True)
    return out_path
