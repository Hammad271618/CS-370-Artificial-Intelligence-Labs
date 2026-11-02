---
name: ai-lab-generator
description: Automates CS-370 Artificial Intelligence Lab lookup and state-of-the-art lab report generation (.docx, .ipynb, .py, and 2x Google Colab Dark-Mode screenshots) for Military College of Signals (NUST). Activate whenever the user asks "what is lab X", "tell me about lab X", "prepare lab X", or "generate lab X report".
---

# CS-370 AI Lab Lookup & Report Generator Skill

Use this skill whenever the user asks about a lab number from the CS-370 Artificial Intelligence Lab Manual or requests a lab report to be generated.

## Default Student Profile
- **Institution:** Military College of Signals (NUST)
- **Course:** CS-370 — Artificial Intelligence
- **Submitted To:** `Lec Shehla`
- **Submitted By:** `GC HAMMAD LATIF`
- **CMS ID:** `534740`
- **Class:** `BESE 30B`

## Two-Step Interactive Workflow

### Step 1 — Lab Lookup ("What is Lab X?")
When the user asks *"What is Lab X?"* (or mentions a lab number):
1. Run the manual lookup CLI:
   ```powershell
   python -m lab_system.manual_parser --lab <X>
   ```
   *(Or read `lab_system/lab_manual_index.json` directly.)*
2. Present a clean, well-structured summary of **Lab # X** from the manual:
   - **Lab Title & CLOs**
   - **Time & Software Required**
   - **Lab Objective**
   - **Exact Lab Tasks to Implement**
3. Ask the user: *"Would you like me to generate the complete submission bundle (`.docx` report in the NUST Royal Navy & Teal theme, `.ipynb` Colab notebook, `.py` script, and 2x Colab Dark-Mode screenshots) for Lab # X now, or would you like any custom modifications first?"*

### Step 2 — On-Demand Solution & Report Generation ("Generate Lab X")
Once the user confirms (or if they explicitly ask to generate the report right away):
1. Check if `lab_system/specs/lab_<XX>.py` exists (where `<XX>` is zero-padded like `02`, `03`, ..., `14`).
2. If `lab_system/specs/lab_<XX>.py` does not exist yet (or needs updates), create it following the schema in `lab_system/specs/lab_01.py`:
   - Read the full lab details (`theory_and_implementation` and `tasks`) for Lab `X` from `lab_system/lab_manual_index.json`.
   - Write clean, self-contained, deterministic Python code for each task in `LAB_SPEC["tasks"]`.
   - Include a clear `problem_statement`, `analysis` (answering all theoretical questions asked in the manual for that task), optional `table` (`headers`, `rows`, `title`) for comparisons, and optional `plot_hook(shared_ns, extra_img_path)` if the task requires drawing a graph/diagram/plot (e.g., Constraint Graphs in Lab 9, Bayesian Network DAG in Lab 11, TD Convergence in Lab 8).
3. Run the generator CLI:
   ```powershell
   python -m lab_system.report_generator --lab <X>
   ```
4. Commit and push the generated notebook to GitHub so the Colab link works immediately:
   ```powershell
   git add .
   git commit -m "Add Lab <X> report and Colab notebook"
   git push origin main
   ```
5. Output the 1-Click **Open in Colab** badge:
   `[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Hammad271618/CS-370-Artificial-Intelligence-Labs/blob/main/reports/Lab_<XX>_<Slug>/Lab_<XX>_<Slug>.ipynb)`
   and provide clickable links to the local files.
